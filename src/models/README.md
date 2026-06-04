# Diretório de modelos de processadores

Inclui atualmente processadores:
- ordenados com pipeline fixo
- não-ordenado
- não-ordenado com core customizado

## Arquivos

### `simple-riscv.py`
Modelo de processador simples para RISC-V. Este é o processador base com configuração padrão.

### `inorder.py`
Implementação de um processador **ordenado** (in-order) com pipeline fixo. As instruções são processadas sequencialmente sem execução especulativa.

### `outorder.py`
Implementação de um processador **não-ordenado** (out-of-order). Permite execução especulativa e reordenação de instruções para melhor desempenho.

### `custom_core.py`
Processador não-ordenado com **core customizado**. Estende o processador out-of-order com configurações e otimizações específicas.
