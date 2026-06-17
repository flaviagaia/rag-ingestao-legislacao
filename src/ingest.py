"""Pipeline de ingestão: bruto -> estrutura -> JSON pronto para o RAG.

    raw = fetch_arquivo("data/lei_13709_raw.txt")   # ou fetch_url(...)
    doc = ingest(raw)                                # parse + metadados + vigência
    salvar(doc, "data/lei_estruturada.json")

A saída tem o MESMO formato (nodes com id/tipo/parent/rotulo/texto/vigente) que os
outros repos da série consomem, então este pipeline é a porta de entrada deles.
"""

from __future__ import annotations

import json
from pathlib import Path

from parser import parse


def ingest(raw: str) -> dict:
    doc = parse(raw)
    # higiene: remove nós sem texto e deduplica por id
    vistos, limpos = set(), []
    for n in doc["nodes"]:
        if n["texto"] and n["id"] not in vistos:
            vistos.add(n["id"])
            limpos.append(n)
    doc["nodes"] = limpos
    doc["stats"] = resumo(doc)
    return doc


def resumo(doc: dict) -> dict:
    tipos: dict[str, int] = {}
    for n in doc["nodes"]:
        tipos[n["tipo"]] = tipos.get(n["tipo"], 0) + 1
    revogados = sum(1 for n in doc["nodes"] if not n["vigente"])
    return {"total": len(doc["nodes"]), "por_tipo": tipos, "revogados": revogados}


def salvar(doc: dict, caminho: str | Path) -> None:
    Path(caminho).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
