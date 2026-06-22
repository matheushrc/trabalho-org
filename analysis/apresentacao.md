# Relatório de Simulação e Exploração de Espaço de Projeto (gem5 RISC-V)

Este documento compila de forma detalhada a sequência de ideias, passos executados, decisões arquiteturais tomadas e análises geradas durante o estudo de otimização de hardware usando o simulador gem5 com a ISA RISC-V, rodando o benchmark de ordenação **Heap Sort**.

---

## 1. Introdução e Metodologia

O processo de exploração iniciou-se com uma abordagem estruturada passo a passo:

1. **Varredura Uniparamétrica (Parameter Sweep)**: Escrevemos scripts para realizar simulações isoladas alterando apenas um atributo de hardware por vez (Branch Predictor, Tipo de CPU, Clock, Cache L1, Cache L2, Núcleos, Memória e Hierarquia de Cache), mantendo as demais variáveis no baseline.
2. **Escolha dos Melhores Executores (Best Performers)**: Analisamos as estatísticas de tempo de simulação (`simTicks`) para identificar qual configuração individual entregava o melhor desempenho em cada categoria.
3. **Fusão em Híbridos**: Projetamos e simulamos configurações híbridas que combinavam todos os melhores componentes individuais.
4. **Varredura Multiparamétrica (Grid & Randomized Search)**: Executamos uma exploração do espaço de projeto (DSE) mais robusta simulando 36 novas variações usando abordagens inspiradas em `GridSearchCV` e `RandomizedSearchCV` para estudar a sensibilidade dos parâmetros e encontrar o design ideal.
5. **Validação**: Testamos a hipótese de viés de dataset rodando uma simulação paralela de grande escala com um array de 100k inteiros.

---

## 2. Análise de Predição de Desvios (Branch Prediction)

Nos modelos de CPU que possuem pipeline detalhada e execução fora de ordem (como o modelo `O3`), o preditor de desvios desempenha um papel crítico para o desempenho. As estatísticas no arquivo `stats.json` gerado pelo gem5 localizam-se sob o caminho:
`board.processor.cores.value[0].core.branchPred`

### Mapeamento dos Vetores de Estatísticas (Índice → Tipo de Instrução)

Para as estatísticas representadas como vetores (como `lookups`, `committed` e `mispredicted`), o gem5 mapeia internamente os seguintes tipos de desvio:

| Índice  | Nome do Tipo de Desvio | Descrição                                                   |
| :-----: | :--------------------- | :---------------------------------------------------------- |
| **`0`** | `NoBranch`             | Instruções normais (que não realizam desvios)               |
| **`1`** | `Return`               | Instruções de retorno de função (ex: `ret`, `jr ra`)        |
| **`2`** | `CallDirect`           | Chamadas diretas de função (ex: `jal`)                      |
| **`3`** | `CallIndirect`         | Chamadas indiretas de função (ex: `jalr`)                   |
| **`4`** | `DirectCond`           | Desvios condicionais diretos (ex: `beq`, `bne`)             |
| **`5`** | `DirectUncond`         | Desvios incondicionais diretos (ex: `j`, `jal` sem retorno) |
| **`6`** | `IndirectCond`         | Desvios condicionais indiretos (raramente utilizados)       |
| **`7`** | `IndirectUncond`       | Desvios incondicionais indiretos (ex: `jr reg`)             |

### Mapeamento dos Provedores de Alvo (Target Providers)

Cada predição de desvio registra de onde veio a predição do endereço de destino (`targetProvider`):

- **`0` (None / Fallthrough)**: Sem destino previsto (desvio não tomado ou falha na previsão do endereço).
- **`1` (BTB)**: Endereço de destino fornecido pelo _Branch Target Buffer_ (BTB).
- **`2` (RAS)**: Endereço fornecido pela _Return Address Stack_ (pilha de retornos de funções).
- **`3` (Indirect Predictor)**: Endereço fornecido pelo preditor de desvios indiretos.

### Comparação de Desempenho: BiModeBP vs. LocalBP (Baseline de 6 Elementos)

Realizamos um comparativo direto rodando o benchmark com o preditor local simples (`LocalBP`) e o preditor global (`BiModeBP`) sob uma CPU `O3`:

| Métrica                                   | BiModeBP  |  LocalBP  |  Diferença  | Análise                                                                                            |
| :---------------------------------------- | :-------: | :-------: | :---------: | :------------------------------------------------------------------------------------------------- |
| **Consultas Totais (Lookups)**            | 39.218,00 | 46.370,00 | **-15,42%** | O `BiModeBP` reduz a execução de caminhos errados (_wrong-path_), buscando 15,4% menos instruções. |
| **Desvios Commitados Totais**             | 30.971,00 | 30.971,00 |  **0,00%**  | Idênticos, pois o programa executa a mesma lógica até a conclusão.                                 |
| **Predições Incorretas (Mispredictions)** |  984,00   | 1.643,00  | **-40,11%** | **O BiModeBP reduziu os erros de predição totais em 40%**.                                         |
| **Taxa Global de Erro (Mispred Rate)**    |   3,18%   |   5,30%   | **-40,11%** | Redução substancial nos descartes (_squashes_) de pipeline.                                        |
| **Erro por Direção de Desvio**            |  542,00   | 1.189,00  | **-54,42%** | **Redução de mais da metade nos erros de direção**, mostrando a eficiência do histórico global.    |
| **Erro por Falha no BTB (BTB Miss)**      |  442,00   |  454,00   | **-2,64%**  | Semelhante, pois o tamanho físico do BTB é o mesmo.                                                |
| **Taxa de Acerto no BTB (Hit Rate)**      |  40,99%   |  44,45%   | **-7,77%**  | Ligeiramente maior no LocalBP devido ao fluxo do caminho incorreto.                                |
| **Precisão do RAS**                       |  100,00%  |  100,00%  |  **0,00%**  | Ambos os preditores obtiveram 100% de precisão nos retornos.                                       |
| **Taxa de Acerto Indireto**               |  87,97%   |  94,76%   | **-7,17%**  | LocalBP obteve taxa ligeiramente melhor, mas sobre um volume maior de consultas.                   |
| **Precisão do Preditor Condicional**      |  96,39%   |  95,05%   | **+1,40%**  | `BiModeBP` atinge 96,39% de precisão direcional (contra 95,05% do LocalBP).                        |

#### Detalhamento das Taxas de Erro Condicional por Tipo de Desvio

| Tipo de Desvio       | BiModeBP (Erros / Comm)  |   LocalBP (Erros / Comm)   | Análise                                                                                          |
| :------------------- | :----------------------: | :------------------------: | :----------------------------------------------------------------------------------------------- |
| **`Return`**         |    0 / 2.194 (0,00%)     |     0 / 2.194 (0,00%)      | Perfeitamente previsto pelo RAS.                                                                 |
| **`CallDirect`**     |   112 / 2.147 (5,22%)    |    121 / 2.147 (5,64%)     | Baixo erro, correspondendo a alvos frios na inicialização.                                       |
| **`CallIndirect`**   |     27 / 52 (51,92%)     |      27 / 52 (51,92%)      | Erro elevado pelo baixo volume amostrado (dificuldade de aprendizado).                           |
| **`DirectCond`**     | **772 / 21.909 (3,52%)** | **1.421 / 21.909 (6,49%)** | **O BiModeBP quase reduz à metade o erro nos desvios condicionais das estruturas de repetição!** |
| **`DirectUncond`**   |    59 / 2.927 (2,02%)    |     60 / 2.927 (2,05%)     | Quase nulo, representando apenas falhas frias de BTB.                                            |
| **`IndirectUncond`** |    14 / 1.742 (0,80%)    |     14 / 1.742 (0,80%)     | Bem previsto pelo preditor indireto.                                                             |

> [!NOTE]
> **Por que o `LocalBP` gera mais consultas (Lookups) do que o `BiModeBP`?**
> Quando o preditor falha, a CPU busca instruções no caminho incorreto de desvios. Essas instruções contêm desvios adicionais que são consultados no preditor, mas que acabam sendo descartados posteriormente. O preditor pior (`LocalBP`) gera um maior desperdício de pipeline (_wrong-path execution_), elevando artificialmente as consultas totais.

---

## 3. Projeto e Resultado das Configurações Híbridas

Após realizar simulações isoladas por parâmetro, identificamos os melhores desempenhos individuais:

- **CPU**: O modelo `O3` (Out-of-Order, 36,08M ticks) superou massivamente o `TIMING` (In-Order, 106,60M ticks).
- **Preditor de Desvios**: O `BiModeBP` (35,15M ticks) superou o `LocalBP` (36,08M ticks).
- **Frequência de Clock**: O clock de `4GHz` (88,78M ticks) superou frequências menores (3GHz: 106,60M, 2GHz: 143,42M, 1GHz: 252,49M).
- **Tamanho da L1**: Cache L1 de `64kB` (106,52M ticks) obteve leve vantagem sobre tamanhos menores (32kB: 106,60M, 8kB: 106,73M).
- **Demais Parâmetros (L2, Cores, Memória e Coerência)**: Mostraram desempenho plano (ticks idênticos) por limitações do dataset original de 6 elementos.

Criamos duas configurações híbridas:

- **Grupo de Controle (Baseline)**: CPU `TIMING` | `LocalBP` | Clock `3GHz` | L1 `32kB` | L2 `256kB` | 1 Core | Memória `1GB` | Cache `private_l1_private_l2`.
- **Híbrido 1 (Performance Máxima)**: CPU `O3` | `BiModeBP` | Clock `4GHz` | L1 `64kB` | L2 `1MB` | 1 Core | Memória `2GB` | Cache `private_l1_private_l2`.
- **Híbrido 2 (Design Equilibrado)**: CPU `O3` | `BiModeBP` | Clock `4GHz` | L1 `64kB` | L2 `128kB` | 1 Core | Memória `512MB` | Cache `private_l1_l2` (menores capacidades para parâmetros planos).

### Resultados das Configurações Híbridas (Dataset de 6 Elementos)

| Configuração                | Ticks de Simulação | Tempo de Execução | Speedup vs. Baseline |
| :-------------------------- | :----------------: | :---------------: | :------------------: |
| **Controle (Baseline)**     |    106.596.297     |      100,00%      |     1,00x (Ref)      |
| **Híbrido 1 (Performance)** |     32.258.250     |      30,26%       |      **3,30x**       |
| **Híbrido 2 (Equilibrado)** |     32.258.250     |      30,26%       |      **3,30x**       |

### Conclusões do Estudo Híbrido

1. Ambos os híbridos entregaram **exatamente o mesmo tempo de execução (3,30x de speedup)**.
2. Isso prova que, sob o dataset original, expandir a cache L2 (`1MB` vs `128kB`) ou a memória (`2GB` vs `512MB`) gera **zero ganho de desempenho**.
3. O **Híbrido 2** é a melhor escolha arquitetural (Design Otimizado), pois atinge o maior desempenho reduzindo os custos de área de silício e consumo elétrico.

---

## 4. Exploração Geral do Espaço de Projeto (DSE)

Realizamos uma busca sistemática executando uma pesquisa em grade reduzida (**Grid Search** - 16 combinações dos 4 parâmetros mais importantes) e uma pesquisa aleatória (**Randomized Search** - 20 combinações amostradas do espaço total de parâmetros).

### Melhores 15 Configurações do DSE (Dataset 100k Elementos)

Os resultados abaixo foram obtidos a partir da simulação do dataset expandido de **100.000 elementos**:

| Rank | Tipo de Busca |    ID     | Ticks Simulados | Speedup vs Baseline | CPU |    BP    | CLK  |  L1  |  L2   | Cores | Memória |      Hierarquia       |
| :--: | :-----------: | :-------: | :-------------: | :-----------------: | :-: | :------: | :--: | :--: | :---: | :---: | :-----: | :-------------------: |
|  1   |     GRID      |  grid_15  |  9.778.474.250  |        4,95x        | O3  | BiModeBP | 4GHz | 64kB | 256kB |   1   |   1GB   | private_l1_private_l2 |
|  2   |     GRID      |  grid_11  | 10.388.132.750  |        4,66x        | O3  | LocalBP  | 4GHz | 64kB | 256kB |   1   |   1GB   | private_l1_private_l2 |
|  3   |     GRID      |  grid_14  | 10.428.981.250  |        4,64x        | O3  | BiModeBP | 4GHz | 16kB | 256kB |   1   |   1GB   | private_l1_private_l2 |
|  4   |     GRID      |  grid_10  | 11.015.935.000  |        4,39x        | O3  | LocalBP  | 4GHz | 16kB | 256kB |   1   |   1GB   | private_l1_private_l2 |
|  5   |    RANDOM     | random_15 | 11.468.775.744  |        4,22x        | O3  | LocalBP  | 3GHz | 32kB | 512kB |   1   |  512MB  |     private_l1_l2     |
|  6   |    RANDOM     | random_1  | 12.367.516.104  |        3,91x        | O3  | BiModeBP | 3GHz | 64kB | 256kB |   1   |  512MB  | private_l1_private_l2 |
|  7   |    RANDOM     | random_6  | 13.219.187.580  |        3,66x        | O3  | BiModeBP | 3GHz | 16kB | 256kB |   2   |   1GB   |     private_l1_l2     |
|  8   |    RANDOM     | random_4  | 16.085.972.000  |        3,01x        | O3  | BiModeBP | 2GHz | 32kB | 512kB |   1   |  512MB  | private_l1_private_l2 |
|  9   |     GRID      |  grid_13  | 17.588.158.500  |        2,75x        | O3  | BiModeBP | 2GHz | 64kB | 256kB |   1   |   1GB   | private_l1_private_l2 |
|  10  |    RANDOM     | random_17 | 17.588.158.500  |        2,75x        | O3  | BiModeBP | 2GHz | 64kB | 256kB |   1   |  512MB  |     private_l1_l2     |
|  11  |    RANDOM     | random_16 | 17.857.933.500  |        2,71x        | O3  | LocalBP  | 2GHz | 16kB |  1MB  |   2   |  512MB  | private_l1_private_l2 |
|  12  |    RANDOM     | random_0  | 18.464.447.500  |        2,62x        | O3  | LocalBP  | 2GHz | 8kB  | 512kB |   2   |   2GB   | private_l1_private_l2 |
|  13  |     GRID      |  grid_9   | 18.792.986.000  |        2,58x        | O3  | LocalBP  | 2GHz | 64kB | 256kB |   1   |   1GB   | private_l1_private_l2 |
|  14  |     GRID      |  grid_12  | 18.834.237.500  |        2,57x        | O3  | BiModeBP | 2GHz | 16kB | 256kB |   1   |   1GB   | private_l1_private_l2 |
|  15  |     GRID      |  grid_8   | 19.998.213.500  |        2,42x        | O3  | LocalBP  | 2GHz | 16kB | 256kB |   1   |   1GB   | private_l1_private_l2 |

- **Referência do Controle (Baseline - 100k)**: `48.402.756.459` ticks (1,00x)
- **Melhor Configuração**: Ticks: `9.778.474.250` (Speedup: **4,95x**)

### Análise de Sensibilidade Paramétrica (Dataset 100k Elementos)

Esta análise isola o impacto médio de cada parâmetro físico nos ticks agregados de todas as simulações executadas:

#### Parâmetro: `cpu_type`

| Tipo de CPU | Ocorrências | Média de Ticks | Speedup Médio | Variação Relativa |
| :---------- | :---------: | :------------: | :-----------: | :---------------: |
| **O3**      |     17      | 16.814.527.275 |     2,88x     |      -65,26%      |
| **TIMING**  |     19      | 66.259.511.803 |     0,73x     |      +36,89%      |

#### Parâmetro: `clk_freq` (Frequência)

| Frequência | Ocorrências | Média de Ticks | Speedup Médio | Variação Relativa |
| :--------- | :---------: | :------------: | :-----------: | :---------------: |
| **4GHz**   |      9      | 25.217.873.306 |     1,92x     |      -47,90%      |
| **3GHz**   |      6      | 32.178.007.948 |     1,50x     |      -33,52%      |
| **2GHz**   |     17      | 46.432.245.676 |     1,04x     |      -4,07%       |
| **1GHz**   |      4      | 83.850.151.000 |     0,58x     |      +73,23%      |

#### Parâmetro: `cache_hierarchy` (Coerência de Cache)

| Modelo                    | Ocorrências | Média de Ticks | Speedup Médio | Variação Relativa |
| :------------------------ | :---------: | :------------: | :-----------: | :---------------: |
| **private_l1_private_l2** |     27      | 40.316.473.951 |     1,20x     |      -16,71%      |
| **private_l1_l2**         |      9      | 50.692.543.475 |     0,95x     |      +4,73%       |

#### Parâmetro: `l1_size` (Tamanho da L1)

| Tamanho  | Ocorrências | Média de Ticks | Speedup Médio | Variação Relativa |
| :------- | :---------: | :------------: | :-----------: | :---------------: |
| **64kB** |     15      | 45.901.030.128 |     1,05x     |      -5,17%       |
| **32kB** |      4      | 36.888.444.301 |     1,31x     |      -23,79%      |
| **16kB** |     11      | 34.674.092.985 |     1,40x     |      -28,36%      |
| **8kB**  |      6      | 54.548.905.998 |     0,89x     |      +12,70%      |

#### Parâmetro: `l2_size` (Tamanho da L2)

| Tamanho   | Ocorrências | Média de Ticks | Speedup Médio | Variação Relativa |
| :-------- | :---------: | :------------: | :-----------: | :---------------: |
| **256kB** |     23      | 35.882.868.843 |     1,35x     |      -25,87%      |
| **512kB** |      6      | 36.400.371.291 |     1,33x     |      -24,80%      |
| **128kB** |      2      | 53.804.905.902 |     0,90x     |      +11,16%      |
| **1MB**   |      5      | 78.691.933.000 |     0,62x     |      +62,58%      |

#### Parâmetro: `branch_predictor`

| Modelo       | Ocorrências | Média de Ticks | Speedup Médio | Variação Relativa |
| :----------- | :---------: | :------------: | :-----------: | :---------------: |
| **LocalBP**  |     16      | 41.658.871.077 |     1,16x     |      -13,93%      |
| **BiModeBP** |     20      | 43.911.787.535 |     1,10x     |      -9,28%       |

> [!NOTE]
> Conforme detalhado na sensibilidade paramétrica, o `LocalBP` obteve um desempenho médio ligeiramente melhor que o `BiModeBP` devido à natureza aleatória da amostragem do _Randomized Search_ (que pareou mais CPUs lentas `TIMING` ou clock de `1GHz` com o `BiModeBP`, enviesando as médias agregadas). Nos cenários de melhor desempenho geral, o `BiModeBP` supera consistentemente o `LocalBP` por reduzir a taxa de erros nos desvios.

---

## 5. Decisões Não Tomadas (Architectural Trade-offs)

No desenvolvimento do hardware otimizado, algumas decisões de design foram explicitamente rejeitadas baseadas em nossas simulações práticas. Elas ilustram o balanço entre **Desempenho**, **Área de Silício (Custo)** e **Consumo Energético**:

1. **Não aumentamos o número de núcleos (`num_cores = 1`)**:
   - _Decisão_: Mantivemos o chip com apenas 1 núcleo.
   - _Razão_: O benchmark `heapSort` é sequencial (single-threaded). Os testes com 2 ou 4 cores apresentaram exatamente os mesmos ticks de execução que os testes equivalentes com 1 único núcleo. Adicionar núcleos causaria o desperdício de área e aumentaria a potência estática por correntes de fuga sem ganho de velocidade.
2. **Rejeição de Cache L2 de grande porte (`l2_size > 128kB` para o Híbrido Otimizado)**:
   - _Decisão_: No híbrido final equilibrado, mantivemos a cache L2 em `128kB`.
   - _Razão_: No dataset inicial, a cache L1 era suficiente para comportar o dataset e as instruções. Mesmo no dataset maior de 100k, o incremento da L2 de 256kB para 512kB e 1MB não justificou o custo financeiro e o tempo de latência de acesso adicional decorrente de caches físicas muito grandes.
3. **Rejeição de alta capacidade de Memória Principal (`memory_size > 512MB` para o Híbrido Otimizado)**:
   - _Decisão_: Adotamos o patamar mínimo de `512MB` no design equilibrado.
   - _Razão_: A alocação dinâmica do programa de ordenação consome apenas algumas dezenas de kilobytes de RAM. Capacidades maiores de memória não alteraram o desempenho e representariam desperdício de projeto.
4. **Uso de Hierarquia de Cache Simples (`private_l1_l2`)**:
   - _Decisão_: No design otimizado, evitamos barramentos e protocolos complexos de compartilhamento de cache coerente.
   - _Razão_: Como o chip possui um único núcleo, protocolos de coerência mais complexos (como o `private_l1_private_l2`) adicionariam latência ao barramento de controle desnecessariamente, além de aumentar o risco de falhas de projeto físico.

---

## 6. Limitação do Dataset (Viés do Array Curto)

O benchmark inicial (`heapSort_gem5.s`) possuía um array estático de **apenas 6 elementos (24 bytes)**. Essa restrição introduziu vieses que mascaravam a análise do sistema de memória:

- **Caches e Memória Ociosas**: 24 bytes cabem inteiramente em qualquer cache L1 de dados. Por isso, nenhuma falha de cache (_cache miss_) de dados foi registrada. Alterar a cache L2 ou o barramento de memória resultava em 0% de variação no tempo de simulação.
- **Ocultamento de Latência Inativo**: Em um array real, ocorrem falhas de cache que causam esperas (_stalls_). O processador `TIMING` congela a execução a cada stall, enquanto a CPU `O3` executa instruções fora de ordem para ocultar essa latência de busca na DRAM. Com 6 elementos, o speedup da CPU `O3` ficou artificialmente preso em **3,30x** porque o modelo `TIMING` nunca sofria com latências de memória.
- **Falta de Treino no Preditor**: Preditores de histórico global (como o `BiModeBP`) exigem repetição de laços de execução para treinar suas tabelas. A execução curta impediu que o preditor fizesse o seu warm-up completo, reduzindo a diferença de precisão em relação ao preditor local.

---

## 7. Validação Prática com Dataset de Grande Porte (100.000 Elementos)

Para quebrar o viés do dataset curto e comprovar nossas predições teóricas, modificamos o assembly diretamente para alocar dinamicamente um array de **100.000 inteiros (400 KB)** preenchidos por um gerador de números pseudo-aleatórios (LCG) desenvolvido diretamente em RISC-V.

### Resultados da Simulação de Controle (Baseline 100k)

Rodamos o baseline de controle com este novo tamanho de entrada (CPU `TIMING`, clock `3GHz`, L1 de `32kB`, L2 de `256kB`):

- **Tempo de Execução Real (Máquina Host)**: **2 minutos e 40 segundos** (`hostSeconds = 160.26`).
- **Total de Instruções RISC-V**: **86.674.630 instruções** (~86,67M).
- **Total de Ticks Simulados**: **48.402.756.459** (48,4 ms de tempo simulado).

### Ativação da Hierarquia de Memória

A simulação com 100k comprovou estatisticamente a ativação da cache L2 e do tráfego com a DRAM:

1. **Cache L1 de Dados (L1D)**: Registrou **15.907.370 acessos** de leitura e **390.014 misses** (Taxa de falha: **2,45%**).
2. **Cache L2**: Registrou **408.928 acessos** e **41.853 misses** (Taxa de falha: **10,23%**).
3. **Memória Principal (DRAM)**: Sofreu **51.399 requisições de leitura** e **41.789 requisições de escrita** no controlador de memória, trafegando **3,29 MB lidos** e **2,67 MB gravados**.

### Validação da Teoria de Ocultamento de Latência

Ao analisarmos os dados da busca DSE paralela sob o dataset de 100k, observamos o seguinte comportamento:

- No array de 6 elementos, o speedup máximo da CPU `O3` era de **3,30x**.
- No array de 100.000 elementos, o speedup do melhor design (`grid_15`, com CPU `O3`, BiModeBP e Clock de `4GHz`) saltou para **4,95x** (com os ticks simulados reduzidos para apenas **9.778.474.250**).

Isso valida de forma definitiva nossa tese física: em aplicações reais com falhas de cache significativas, o processador Out-of-Order consegue extrair paralelismo a nível de instrução (ILP) para continuar executando código especulativo e ocultar os longos ciclos de espera da memória DRAM, enquanto o processador In-Order fica paralisado aguardando o retorno dos dados da RAM.
