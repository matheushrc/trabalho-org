# Histórico de sessões de chat (Gemini / Antigravity CLI)

Este documento reconstrói, em detalhe, o trabalho realizado neste repositório
através do **Antigravity CLI** (ferramenta da família Gemini), com base nos
transcripts legíveis em
`~/.gemini/antigravity-cli/brain/<session_id>/.system_generated/logs/transcript.jsonl`.

O projeto está registrado no Gemini com o id
`85abb256-982e-4f64-a446-32b465f952b5` (`~/.gemini/config/projects/85abb256-982e-4f64-a446-32b465f952b5.json`),
apontando para `/home/matheus/Documents/Faculdade/trabalho-org`.

Das 8 sessões encontradas que mencionam o caminho deste repositório, apenas
3 contêm trabalho real sobre RISC-V/gem5 (as demais eram sessões triviais ou
sobre configuração de tooling não relacionada ao trabalho de arquitetura de
computadores, e foram descartadas deste documento).

## Visão geral cronológica

| Sessão (id) | Período (UTC) | Eventos | Conteúdo |
| --- | --- | --- | --- |
| `1ec9e465-34d2-4efe-9d25-0b4d4a248ef5` | 2026-06-04 22:45–22:48 | 27 | Corrige `execution.md` e `docker-compose.yml` (cache do gem5) |
| `81d0eedc-5e37-41c2-99b5-aa866102635d` | 2026-06-04 23:18–01:20 (+1d) | 125 | Planeja `simulation.md`, define eixos de simulação e formato `stats.json` |
| `a22c9a0e-42c3-4bac-bea4-899007a8fa88` | 2026-06-05 01:32 até 2026-06-09 23:05 | 566 | Sessão principal: análises, busca de hiperparâmetros, hybrids, heapsort 100k, `apresentacao.md` |

## Sessão 1 — `1ec9e465` (corrigindo execução via Docker)

**Pedido do usuário:** acessar os arquivos dentro do container `gem5` e
corrigir os comandos em `execution.md` para usar caminhos relativos ao
container, rodando tudo via `docker exec` (sem precisar abrir o shell do
Docker Desktop).

**O que o agente fez:**

1. Listou o diretório do projeto e leu `execution.md`.
2. Rodou comandos dentro do container (`docker exec`) para confirmar os
   caminhos reais dos arquivos fonte (`/workspace/src/heapSort_gem5.s`,
   `/workspace/src/heapSort.riscv`, `/workspace/src/models/*.py`) e verificar
   se o `gem5.opt` já estava compilado.
3. Editou `execution.md` para usar `docker exec` com os caminhos corretos do
   container, em vez de instruções de shell manual.
4. O usuário perguntou por que o gem5 estava "em um cache separado" — o
   agente explicou que o `docker-compose.yml` montava um volume nomeado
   `gem5-build-cache:/gem5/build`, que sobrescrevia o binário `gem5.opt`
   compilado dentro da imagem por um volume vazio, forçando recompilação.
5. A pedido do usuário, removeu esse volume nomeado do `docker-compose.yml`
   (bloco `volumes: gem5-build-cache:` e a entrada de montagem), simplificando
   o fluxo: o build do gem5 agora acontece uma vez dentro da imagem Docker e
   persiste enquanto a imagem não for reconstruída.

Essa mudança corresponde ao commit `9fe33f4` do repositório ("remove unused
gem5-build-cache volume" / "simplify RISC-V compilation instructions in
execution.md").

## Sessão 2 — `81d0eedc` (planejamento das simulações)

**Pedido do usuário:** alterar `inorder.py` (modelo de CPU usado no gem5)
para permitir simulações variando:

- método de branch prediction (comparando `LocalBP` vs `BiModeBP`)
- tipo de CPU
- frequência de clock
- tamanho de cache
- número de núcleos
- memória
- hierarquia de cache

E em seguida documentar **todas** as combinações possíveis em
`simulation.md`, garantindo que cada execução gere sua própria pasta de saída
(em vez de todas reaproveitarem `m5out`).

**O que o agente fez:**

1. Modificou `src/models/inorder.py` para aceitar os parâmetros acima via
   linha de comando (CPU type, branch predictor, clock, tamanhos de cache
   L1/L2, hierarquia, número de núcleos, memória).
2. Escreveu `simulation.md` enumerando os comandos de simulação para cada eixo
   de variação, cada um direcionando sua saída para uma pasta dedicada
   (em vez de `m5out` compartilhado).
3. Quando o usuário pediu novamente ("try again"), o agente refez a
   configuração de saída por simulação.
4. O usuário perguntou se havia uma forma "built-in" de exportar
   `stats.txt` para um formato mais útil (ex.: JSON). O agente confirmou que
   sim e implementou a conversão, fazendo cada simulação também escrever um
   `stats.json` ao lado do `stats.txt` padrão do gem5.
5. A pedido do usuário, moveu a saída das simulações para dentro de uma pasta
   `simulations/` (em vez de espalhar pelo repositório), estabelecendo a
   estrutura que hoje existe (`simulations/<eixo>/<variante>/{config.json,
   config.ini, stats.json, citations.bib, config.dot...}`).

Essa sessão é a origem direta da estrutura de pastas em `simulations/` e do
arquivo `simulation.md` ainda presente no repositório.

## Sessão 3 — `a22c9a0e` (sessão principal: análise e expansão das simulações)

Esta é a sessão mais longa e mais relevante para o trabalho acadêmico em si
(566 eventos, 2026-06-05 a 2026-06-09). Sequência de pedidos e ações:

1. **Entendimento dos dados** — o usuário pediu para analisar
   `stats.json` de `BiModeBP` (vs `LocalBP`) usando Python, para entender o
   significado de cada chave antes de comparar com as demais simulações da
   pasta `simulations/`. O agente escreveu scripts de inspeção (origem dos
   scripts hoje em `scripts/`, ex. `dump_bp_stats.py`,
   `parse_bp_stats.py`, `find_branch_stats.py`).
2. **Organização** — a pedido do usuário, os scripts de teste foram movidos
   para a pasta `scripts/` e passaram a ser executados a partir dali.
3. **Documentação de achados** — a pedido do usuário ("write your finding to
   the folder analysis"), o agente começou a escrever os arquivos hoje
   presentes em `analysis/` (`branch_predictor_analysis.md`, etc.).
4. **Comparação e hybrids** — o usuário pediu para comparar todas as
   simulações aninhadas entre si, escolher os melhores valores de cada eixo,
   e rodar simulações "hybrid" combinando os melhores parâmetros, salvando em
   `simulations/hybrids/`. O agente implementou isso e gerou
   `simulations/hybrids/balanced/` e `simulations/hybrids/performance/`.
   - O usuário perguntou qual era o *baseline*; o agente foi instruído a
     adicionar uma configuração de controle/baseline à análise dos hybrids.
5. **Busca mais ampla de hiperparâmetros (`run_all_simulations.sh`)** — o
   usuário pediu algo "como GridSearchCV e RandomizedSearchCV" para o
   script `run_all_simulations.sh`. O agente criou
   `scripts/search_simulations.py`, que implementa:
   - uma **busca em grade** (16 combinações fixas de CPU × branch predictor
     × clock × tamanho de L1), salvas em `simulations/search/grid_0`…`grid_15`;
   - uma **busca aleatória** (20 combinações amostradas de um espaço de mais
     de 4.600 combinações possíveis, variando também L2, número de núcleos,
     memória e hierarquia de cache), salvas em
     `simulations/search/random_0`…`random_19`.
   - O agente rodou essas simulações em segundo plano dentro do container
     gem5 e reportou os tempos de execução e ticks simulados conforme cada
     lote terminava.
6. **Justificativa sobre número de núcleos** — o usuário perguntou por que o
   número de núcleos não havia sido aumentado nos hybrids. O agente explicou
   que `heapSort.riscv` é um programa sequencial em RISC-V assembly
   (`heapSort_gem5.s`), sem paralelismo (sem threads/OpenMP/multi-hart), então
   adicionar núcleos não teria efeito — e comprovou isso mostrando que
   configurações de busca aleatória com 1 e 2 núcleos (`random_6` e
   `random_19`) produziram exatamente o mesmo número de ticks simulados
   (`36.352.611`), com os demais parâmetros equivalentes. Pediu-se que essa
   decisão e justificativa fossem registradas em `analysis/` como "decisões
   não tomadas".
7. **Tamanho da entrada** — o usuário questionou se o tamanho do array de
   entrada (pequeno, estático) poderia influenciar a análise, e perguntou
   como passar arrays maiores para um binário RISC-V já compilado
   estaticamente (`src/heapSort.riscv`). Uma primeira tentativa explorou
   gerar isso a partir de C, mas o usuário pediu rollback e manteve o código
   RISC-V original (`rollback these changes, well keep our current riscv
   code`).
8. **Geração de array de 100k elementos em assembly puro** — o usuário pediu
   explicitamente para editar `src/heapSort_gem5.s` diretamente (sem passar
   por C) para gerar um array de **100.000 valores aleatórios**. O agente:
   - definiu `n_elems: .word 100000` na seção `.data`;
   - implementou um **gerador de números pseudoaleatórios (LCG — Linear
     Congruential Generator)** inteiramente em assembly RISC-V
     (rotina `rand_assembly`), com tratamento de imediatos maiores que 12
     bits (`12345`, `0x7FFF`);
   - substituiu o laço estático `copiar_vetor` por um laço `populate_loop`
     que chama `rand_assembly` 100.000 vezes para preencher o buffer;
   - alterou `imprimirArray` para **pular a impressão** quando o array tem
     mais de 20 elementos (evitando horas de I/O simulado dentro do gem5);
   - adicionou salvamento/restauração correta dos registradores
     callee-saved (`s1`, `s2`, `s3`) em `main`;
   - recompilou via
     `docker exec gem5 riscv64-linux-gnu-gcc -static /workspace/src/heapSort_gem5.s -o /workspace/src/heapSort.riscv`;
   - rodou uma simulação de teste única antes de rodar o lote completo, a
     pedido do usuário, para medir o tempo necessário (resultado salvo em
     `simulations/search/test_100k/`).
9. **Compilação da apresentação** — o usuário começou a escrever
   `apresentacao.md` com os passos, decisões e a sequência de ideias
   trocadas com o agente, e pediu para compilar nele as decisões de todos os
   `.md` de `analysis/`. Mais tarde (2026-06-09) pediu que todas as análises
   fossem unificadas em `apresentacao.md` **em português**, corrigindo erros
   de formatação Markdown (`markdownlint`) e padronizando marcadores de lista
   para usar `-`.
10. Próximo aos dias finais da sessão (2026-06-09), o usuário perguntou se
    era possível saber os parâmetros usados em cada simulação — indicando a
    necessidade de rastreabilidade entre `config.ini`/`config.json` e os
    resultados em `stats.json` de cada pasta de `simulations/`.

### Resultado tangível desta sessão no repositório

- `scripts/` (análise e busca de hiperparâmetros: `analyze.py`…`analyze4.py`,
  `check_all_bp.py`, `check_local_bp.py`, `compare_all_sims.py`,
  `compile_search_report.py`, `dump_bp_stats.py`, `find_branch_stats.py`,
  `parse_bp_stats.py`, `run_hybrids.py`, `search_simulations.py`)
- `analysis/` (`branch_predictor_analysis.md`, `hybrid_analysis.md`,
  `search_analysis.md`, `search_raw_results.json`, `comparison_output.txt`)
- `simulations/hybrids/{balanced,performance}/`
- `simulations/search/{grid_0..15, random_0..19, test_100k, test_dynamic}/`
- `src/heapSort_gem5.s` reescrito para gerar 100k números pseudoaleatórios em
  assembly puro; `src/heapSort.riscv` recompilado a partir dele
- `apresentacao.md` consolidando as decisões tomadas durante o trabalho

## Metodologia / limitações

- Cada sessão grava um log estruturado em JSON Lines em
  `~/.gemini/antigravity-cli/brain/<session_id>/.system_generated/logs/transcript.jsonl`,
  com campos `step_index`, `source`, `type`, `status`, `created_at` e
  `content` em texto plano — essa foi a fonte primária usada para este
  relatório (mensagens de usuário, respostas do modelo e resultados de
  comandos/ferramentas).
- Identificação das sessões relevantes: todos os arquivos
  `~/.gemini/antigravity-cli/conversations/*.db` foram varridos por
  ocorrências da string `trabalho-org`; dos 8 que casaram, apenas as 3
  descritas acima continham trabalho real sobre RISC-V/gem5 — as demais
  (sessões triviais e uma sessão sobre tooling do Antigravity CLI não
  relacionada ao trabalho) foram descartadas deste documento.
- Onde o conteúdo extraído não permitia reconstrução confiável (ex. trechos
  binários truncados), isso foi omitido em vez de especulado.
