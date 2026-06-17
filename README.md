# Ingestão de Legislação: do scraping à estrutura

[🇧🇷 Português](#-português) · [🇺🇸 English](#-english)

Python 3.10+ · só stdlib (parser e fetch) · 100% offline no fixture · MIT License

Dados públicos: LGPD (Lei nº 13.709/2018), texto do Planalto/gov.br.

> **Em uma frase:** o scraping só pega bytes; o valor está em transformar o texto
> jurídico bruto na **árvore estruturada** (artigo → caput → parágrafo → inciso →
> alínea), com metadados e marcação de vigência. Esta é a porta de entrada que
> alimenta os outros repos da série, sem curadoria manual de documentos.

---

## 🇧🇷 Português

### O problema (e a vantagem metodológica)
A maior dificuldade de um RAG corporativo costuma ser produzir e curar a base de
conhecimento. Com legislação é o contrário: a base já existe, é oficial e pública, e
pode ser coletada por scraping. O gargalo vira a **estruturação**: o texto cru não
serve, porque a unidade de sentido (o dispositivo) e a hierarquia se perdem, e
porque é preciso saber o que está **revogado** para não citar norma fora de vigência.

### O pipeline
```
fetch (bytes)  ──►  parser (estrutura)  ──►  ingest (higiene + metadados)  ──►  JSON
fonte oficial      artigo/§/inciso/alínea     dedup, stats, vigência            pronto p/ RAG
(arquivo ou URL)   + flag de revogação
```
- **fetch.py**: lê de arquivo (padrão, offline) ou de uma URL oficial (`fetch_url`),
  com extrator de HTML. Trocar a fonte não muda o parser.
- **parser.py**: reconhece `Art. Nº`, `§ Nº`/`Parágrafo único`, incisos (romano +
  travessão) e alíneas (letra + parêntese); monta nós `{id, tipo, parent, rotulo,
  texto, vigente}`; detecta `(Revogado...)` e registra a fonte da revogação.
- **ingest.py**: remove nós vazios, deduplica e gera estatísticas. Idempotente.

### Resultado real (fixture da LGPD)
```
Lei nº 13.709 (14 DE AGOSTO DE 2018) — LGPD
Total de dispositivos: 17  | artigo: 5, inciso: 8, parágrafo: 2, alínea: 2
Revogados sinalizados: 1  (Art. 7º, § 1º — revogado pela Lei nº 13.853, de 2019)
```
O bruto vira `artigo > parágrafo/inciso > alínea`, com a hierarquia correta (as
alíneas do Art. 11 penduradas no inciso II) e a vigência marcada. A saída tem o
**mesmo formato** que `graphrag-hierarquia-normativa`, `rag-segmentacao` e
`rag-recuperacao-hibrida` consomem.

### Como explicar em 30 segundos
Baixar a lei é fácil; o difícil é ela chegar como um texto corrido em que ninguém
sabe onde começa um artigo, o que é inciso, e o que já foi revogado. Este pipeline é
o que pega esse texto e devolve uma árvore organizada e datada, pronta para o RAG.

### Execução
```
python src/demo.py        # ingere o fixture e mostra a árvore + stats
pytest tests/ -v          # 7 testes (hierarquia, vigência, metadados, idempotência)
```
Para coletar ao vivo: `fetch_url("https://www.planalto.gov.br/.../l13709.htm")`
em vez do arquivo. Respeite os termos de uso e o robots.txt do portal.

### Estrutura
```
data/lei_13709_raw.txt   # texto jurídico bruto (fixture público)
src/fetch.py             # coleta: arquivo local (padrão) ou URL oficial
src/parser.py            # bruto -> hierarquia (artigo/§/inciso/alínea) + vigência
src/ingest.py            # higiene, metadados, stats, JSON de saída
src/demo.py              # o pipeline ponta a ponta
```

### Limitações honestas
O parser cobre as estruturas mais comuns (artigo, parágrafo, inciso, alínea) com
formatação regular. Atos reais têm itens, incisos em parágrafos, remissões e
revogações implícitas ("revogam-se as disposições em contrário") que exigem regras
adicionais. A vigência aqui é por marcação textual; um controle completo modela as
relações de alteração/revogação como grafo. O objetivo é mostrar o **núcleo
reprodutível**: do bruto à estrutura datada, sem curadoria manual.

### Referências (crédito)
- LGPD (Lei nº 13.709/2018): ato oficial de domínio público (Planalto/gov.br), art. 8º da Lei de Direitos Autorais.
- Lewis et al. (2020), Retrieval-Augmented Generation, NeurIPS — o consumidor da base.
- Edge et al. (2024), Graph RAG — relações de revogação como grafo (extensão natural).

Reimplementação didática; o conteúdo legal é público e creditado à fonte oficial.

---

## 🇺🇸 English

**In one line:** scraping only fetches bytes; the value is turning raw legal text into
the **structured tree** (article → caput → paragraph → item → sub-item) with metadata
and validity flags. It is the entry point that feeds the other repos, with no manual
document curation.

### The pipeline
`fetch` (file or official URL, with an HTML extractor) → `parser` (recognizes
articles, paragraphs, items, sub-items; builds `{id, tipo, parent, rotulo, texto,
vigente}` nodes; flags `(Revogado...)`) → `ingest` (dedup, stats, metadata). Output
has the same shape the other repos consume.

### Real result (LGPD fixture)
17 provisions (5 articles, 8 items, 2 paragraphs, 2 sub-items); 1 flagged as revoked
(Art. 7, §1, revoked by Law 13.853/2019). Correct hierarchy (Art. 11 sub-items under
item II).

### Running
```
python src/demo.py
pytest tests/ -v          # 7 tests
```

### References
LGPD (public official act); Lewis et al. (2020), RAG; Edge et al. (2024), Graph RAG.

---

Part of my LinkedIn series on RAG efficiency → [Flávia Gaia](https://www.linkedin.com/in/flavia-gaia/)
