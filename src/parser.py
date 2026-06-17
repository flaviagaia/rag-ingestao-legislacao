"""Parser que transforma o texto jurídico bruto na hierarquia estruturada.

Aqui mora o valor da ingestão. O scraping só pega bytes; o difícil é virar isso:

    artigo
      ├─ caput
      ├─ § parágrafo
      └─ inciso
           └─ alínea

Cada nó vira {id, tipo, parent, rotulo, texto, vigente}. A marcação de vigência
(detecção de "(Revogado...)") é o que evita, lá na frente, citar norma revogada.

O parser é linha a linha e reconhece "Art. Nº", "§ Nº", "Parágrafo único",
incisos (algarismo romano + travessão) e alíneas (letra + parêntese).
"""

from __future__ import annotations

import re

RE_ARTIGO = re.compile(r"^Art\.\s*(\d+)[ºo.]?\s*(.*)$")
RE_PARAGRAFO = re.compile(r"^(§\s*\d+|Parágrafo único)[ºo.]?\s*(.*)$")
RE_INCISO = re.compile(r"^([IVXLCDM]+)\s*[-–]\s*(.*)$")
RE_ALINEA = re.compile(r"^([a-z])\)\s*(.*)$")
RE_REVOGADO = re.compile(r"\(\s*Revogad[oa]([^)]*)\)", re.IGNORECASE)
RE_LEI = re.compile(r"LEI\s+N[ºo]?\s*([\d.]+),\s*DE\s*(.+?)\.", re.IGNORECASE)


def _vigencia(texto: str) -> tuple[bool, str | None]:
    m = RE_REVOGADO.search(texto)
    if m:
        return False, ("revogado" + m.group(1)).strip()
    return True, None


def art_label(num: str) -> str:
    """Convenção brasileira: Art. 1º a 9º (ordinal); Art. 10 em diante (cardinal)."""
    return f"Art. {num}º" if int(num) <= 9 else f"Art. {num}"


def _node(nid, tipo, parent, rotulo, texto):
    vig, por = _vigencia(texto)
    n = {"id": nid, "tipo": tipo, "parent": parent, "rotulo": rotulo,
         "texto": texto.strip(), "vigente": vig}
    if por:
        n["revogado_por"] = por
    return n


def parse_metadata(linhas: list[str]) -> dict:
    meta = {"numero": None, "data": None, "ementa": None}
    for ln in linhas:
        m = RE_LEI.search(ln)
        if m:
            meta["numero"] = m.group(1)
            meta["data"] = m.group(2).strip()
            break
    # ementa: primeira linha não vazia que não é o cabeçalho nem um dispositivo
    for ln in linhas:
        s = ln.strip()
        if s and not RE_LEI.search(s) and not RE_ARTIGO.match(s):
            meta["ementa"] = s
            break
    return meta


def parse(raw: str) -> dict:
    linhas = [ln.strip() for ln in raw.splitlines()]
    nodes: list[dict] = []
    art = None          # número do artigo atual
    art_id = None
    par_n = 0           # contador de parágrafos no artigo
    last_inciso_id = None

    for ln in linhas:
        if not ln:
            continue
        m = RE_ARTIGO.match(ln)
        if m:
            art = m.group(1)
            art_id = f"art{art}"
            par_n = 0
            last_inciso_id = None
            caput = m.group(2).strip()
            nodes.append(_node(art_id, "artigo", None, art_label(art), caput))
            continue
        if art_id is None:
            continue
        m = RE_PARAGRAFO.match(ln)
        if m:
            par_n += 1
            rotulo_p = m.group(1).strip().replace("  ", " ")
            pid = f"{art_id}_par{par_n}"
            nodes.append(_node(pid, "paragrafo", art_id, f"{art_label(art)}, {rotulo_p}", m.group(2)))
            last_inciso_id = None
            continue
        m = RE_INCISO.match(ln)
        if m:
            iid = f"{art_id}_{m.group(1)}"
            nodes.append(_node(iid, "inciso", art_id, f"{art_label(art)}, {m.group(1)}", m.group(2)))
            last_inciso_id = iid
            continue
        m = RE_ALINEA.match(ln)
        if m and last_inciso_id:
            aid = f"{last_inciso_id}_{m.group(1)}"
            pai = nodes[[n["id"] for n in nodes].index(last_inciso_id)]
            nodes.append(_node(aid, "alinea", last_inciso_id,
                               f"{pai['rotulo']}, {m.group(1)})", m.group(2)))
            continue
        # continuação de texto do último nó (parágrafo/caput multilinha)
        if nodes:
            nodes[-1]["texto"] = (nodes[-1]["texto"] + " " + ln).strip()

    return {"fonte": "texto jurídico bruto (scraping)", "lei": parse_metadata(linhas), "nodes": nodes}
