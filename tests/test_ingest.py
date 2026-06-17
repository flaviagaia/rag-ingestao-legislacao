"""O parser de ingestão vira invariante: bruto -> hierarquia correta e vigente."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from fetch import fetch_arquivo, html_para_texto  # noqa: E402
from ingest import ingest  # noqa: E402
from parser import art_label  # noqa: E402

DOC = ingest(fetch_arquivo(ROOT / "data" / "lei_13709_raw.txt"))
NODES = {n["id"]: n for n in DOC["nodes"]}


def test_metadata_extraida():
    assert DOC["lei"]["numero"] == "13.709"
    assert "2018" in DOC["lei"]["data"]
    assert "Prote" in DOC["lei"]["ementa"]


def test_hierarquia_integra():
    """Todo nó não-artigo aponta para um pai existente; alínea -> inciso -> artigo."""
    for n in DOC["nodes"]:
        if n["tipo"] != "artigo":
            assert n["parent"] in NODES
    assert NODES["art11_II_a"]["parent"] == "art11_II"
    assert NODES["art11_II"]["parent"] == "art11"


def test_tipos_reconhecidos():
    tipos = DOC["stats"]["por_tipo"]
    assert tipos["artigo"] >= 4 and tipos["inciso"] >= 6
    assert tipos["paragrafo"] >= 2 and tipos["alinea"] == 2


def test_vigencia_revogacao():
    """O parágrafo marcado '(Revogado...)' fica vigente=False com a fonte."""
    par = NODES["art7_par1"]
    assert par["vigente"] is False
    assert "13.853" in par.get("revogado_por", "")
    # dispositivos sem marca permanecem vigentes
    assert NODES["art7_I"]["vigente"] is True


def test_convencao_do_rotulo():
    assert art_label("7") == "Art. 7º"
    assert art_label("11") == "Art. 11"
    assert NODES["art11"]["rotulo"] == "Art. 11"


def test_idempotente():
    a = ingest(fetch_arquivo(ROOT / "data" / "lei_13709_raw.txt"))
    b = ingest(fetch_arquivo(ROOT / "data" / "lei_13709_raw.txt"))
    assert a["nodes"] == b["nodes"]


def test_html_para_texto():
    """O extrator de HTML tira tags e mantém o texto (para coleta via URL)."""
    html = "<html><body><p>Art. 1º Texto.</p><script>x=1</script></body></html>"
    txt = html_para_texto(html)
    assert "Art. 1º Texto." in txt and "x=1" not in txt
