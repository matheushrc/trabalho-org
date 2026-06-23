# Scripts de análise de dados (`src/analysis/`)

Ferramentas reutilizáveis para extrair métricas das simulações gem5
(`simulations/**/stats.json`) e **verificar os números do relatório**
`trabalho_latex/main.tex`. Todos os caminhos são resolvidos em relação à raiz
do projeto (dois níveis acima deste diretório), então os scripts podem ser
executados de qualquer lugar.

## Estrutura

```
src/analysis/
├── lib/
│   └── gem5_stats.py        # biblioteca: leitura de stats.json + métricas
├── verify_main_tex.py       # verifica TODAS as tabelas/números do main.tex
├── make_figures.py          # gera as figuras (PNG) de trabalho_latex/figuras
├── bp_report.py             # relatório detalhado do branch predictor + comparação
├── compare_ticks.py         # varredura de simTicks por eixo (melhor config)
├── search_simulations.py    # executa grid/random search (precisa do Docker/gem5)
├── run_hybrids.py           # executa configurações híbridas (precisa do Docker/gem5)
└── compile_search_report.py # consolida resultados da busca em relatório
```

## Uso rápido

```bash
# Verificar se os números do relatório batem com os dados brutos
python3 src/analysis/verify_main_tex.py        # imprime PASS/FAIL por métrica

# Relatório completo do preditor (BiModeBP e LocalBP) + tabela comparativa
python3 src/analysis/bp_report.py
python3 src/analysis/bp_report.py <stats.json>                 # um arquivo
python3 src/analysis/bp_report.py <stats_a.json> <stats_b.json> # comparar dois

# Melhor configuração por eixo (branch, cpu, clock, cache, ...)
python3 src/analysis/compare_ticks.py

# (Re)gerar as figuras da apresentação/relatório a partir dos dados brutos
python3 src/analysis/make_figures.py   # -> trabalho_latex/figuras/*.png
```

## A biblioteca `lib/gem5_stats.py`

Centraliza a navegação na estrutura aninhada do `stats.json` do gem5. O
`branchPred` fica em `board.processor.cores.value[0].core.branchPred`.

```python
from gem5_stats import Metrics
m = Metrics("simulations/branch_prediction/LocalBP/stats.json")
m.sim_ticks            # tempo total de simulação
m.ipc                  # simInsts / core_numCycles
m.bp_lookups           # BTBLookups (linha 'lookups' da Tabela 2)
m.cond_incorrect       # condIncorrect
m.mispred_over_committed  # taxa 'global' tabulada (mispredicted/committed)
m.directcond_mispredicted / m.directcond_committed
m.l1d_demand_misses    # ReadReq+WriteReq misses (= 548 no baseline)
```

## O que `verify_main_tex.py` confere

| Tabela do main.tex | Fonte dos dados |
|---|---|
| Tab. 1 — baseline (TIMING 3 GHz, n=6) | `simulations/cpu_type/TIMING/stats.json` |
| Tab. 2 — LocalBP vs BiModeBP (O3, n=6) | `simulations/branch_prediction/{LocalBP,BiModeBP}/stats.json` |
| Tab. 3 — efeito de escala (n=100.000) | `analysis/search_raw_results.json` (pares `grid_*`) |

### Observação encontrada na verificação

A coluna **"Taxa de erro global"** da Tabela 2 (5,30% / 3,18%) corresponde a
`mispredicted / committed`. O texto da Seção 3.4, porém, descreve a fórmula como
`condIncorrect / lookups`, que daria 3,54% / 2,51%. Os demais números do
relatório são reproduzidos exatamente a partir dos dados brutos.
