"""Demo: ingere o fixture da LGPD e mostra a árvore estruturada (~1s).

    python src/demo.py
"""

from __future__ import annotations

from pathlib import Path

from fetch import fetch_arquivo
from ingest import ingest

ROOT = Path(__file__).parent.parent
INDENT = {"artigo": "", "paragrafo": "    ", "inciso": "    ", "alinea": "        "}


def main() -> None:
    raw = fetch_arquivo(ROOT / "data" / "lei_13709_raw.txt")
    doc = ingest(raw)

    print("=" * 70)
    print(f"Ingestão: Lei nº {doc['lei']['numero']} ({doc['lei']['data']})")
    print(f"Ementa: {doc['lei']['ementa']}")
    print("=" * 70)
    for n in doc["nodes"]:
        flag = "" if n["vigente"] else "  [REVOGADO]"
        txt = n["texto"][:60] + ("..." if len(n["texto"]) > 60 else "")
        print(f"{INDENT.get(n['tipo'], '')}{n['rotulo']}: {txt}{flag}")

    s = doc["stats"]
    print("\n" + "-" * 70)
    print(f"Total de dispositivos: {s['total']} | por tipo: {s['por_tipo']}")
    print(f"Revogados (sinalizados para controle de vigência): {s['revogados']}")
    print("\nO bruto virou estrutura: artigo > parágrafo/inciso > alínea, com vigência.")
    print("Essa saída alimenta os outros repos (graphrag, segmentação, recuperação...).")


if __name__ == "__main__":
    main()
