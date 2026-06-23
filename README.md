# Trabalho_org_gem5

Projeto educacional para estudar organizações de processadores (arquitetura e pipeline) utilizando o simulador **gem5** com suporte a arquitetura RISC-V.

## Objetivo

Este repositório contém exemplos de programas em C compilados para RISC-V e modelos de processadores (simples, ordenado e não-ordenado) para simulação em gem5, permitindo analisar como diferentes arquiteturas executam e otimizam o código.

## Pré-requisitos

Certifique-se de ter instalado:
- **GCC para RISC-V**: Compilador que gera código de máquina para arquitetura RISC-V
- **gem5**: Simulador de arquitetura de processadores
- **riscv64-linux-gnu-objdump**: Ferramenta para desassemblagem de binários RISC-V

### Instalação do GCC para RISC-V

```bash
sudo apt install gcc-riscv64-linux-gnu
```

## Passo a Passo

### 1. Compilar código C para RISC-V

Compile um programa em C gerando um binário estático RISC-V:

```bash
riscv64-linux-gnu-gcc -static sum.c -o sum.riscv
```

**Parâmetros:**
- `-static`: Faz linking estático (importante para simulação em gem5)
- `sum.c`: Arquivo fonte em C
- `-o sum.riscv`: Nome do binário de saída

### 2. Visualizar o Assembly do binário

Para entender como o código foi compilado, você pode desassemblar o binário e ver as instruções RISC-V:

```bash
riscv64-linux-gnu-objdump -d sum.riscv
```

**Parâmetros:**
- `-d`: Desassembla o binário mostrando as instruções em linguagem de assembly

Você também pode redirecionar a saída para um arquivo para análise:

```bash
riscv64-linux-gnu-objdump -d sum.riscv > sum_assembly.txt
```

### 3. Simular a execução em gem5

Execute a simulação do programa usando um dos modelos de processador:

```bash
./gem5/build/RISCV/gem5.opt models/<model_name>.py --binary programs/<program_name>.riscv
```

**Substituir:**
- `<model_name>`: Nome do modelo (ex: `simple-riscv`, `inorder`, `outorder`, `custom_core`)
- `<program_name>`: Nome do programa (ex: `sum`)

**Exemplo:**
```bash
./gem5/build/RISCV/gem5.opt models/inorder.py --binary programs/sum.riscv
```

## Gerar os PDFs do relatório e dos slides

O serviço `tex` do `docker-compose.yml` usa a imagem `texlive/texlive` para compilar `trabalho_latex/main.tex` e `trabalho_latex/apresentacao.tex`, deixando apenas os `.pdf` (os arquivos auxiliares do LaTeX são removidos ao final):

```bash
docker compose run --rm tex
```

Os PDFs são gerados em `trabalho_latex/main.pdf` e `trabalho_latex/apresentacao.pdf`.

## Estrutura do Repositório

- **src/**: Fontes RISC-V e binários compilados — `heapSort_original.s`/`.riscv` (entrega parcial, n=6) e `heapSort_100k.s`/`.riscv` (n=100.000) — além dos modelos de processador em `src/models/`
- **src/analysis/**: Scripts de análise/verificação dos dados das simulações (ver [src/analysis/README.md](src/analysis/README.md))
- **simulations/**: Saídas das simulações gem5 (`stats.json` por configuração)
- **analysis/**: Relatórios e resultados consolidados das análises
- **trabalho_latex/**: Relatório científico (`main.tex`) e slides (`apresentacao.tex`) + figuras
- **docs/**: Documentação do projeto (ver abaixo)

### Documentação (`docs/`)

- [execution.md](docs/execution.md) — como subir o container e rodar uma simulação
- [simulation.md](docs/simulation.md) — comandos das simulações parametrizadas por eixo
- [requisitos.md](docs/requisitos.md) — requisitos do seminário/relatório
- [specs_trabalho_2.md](docs/specs_trabalho_2.md) — enunciado do trabalho
- [tutorial_venus.md](docs/tutorial_venus.md) — porte de assembly do Venus para o gem5

Para detalhes sobre os modelos, veja [src/models/README.md](src/models/README.md)
