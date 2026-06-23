# Execucao da simulacao com Docker

## 1) Subir o container

```bash
docker compose up -d --build
```

## 2) Compilar os programas RISC-V no container

Há duas versões do HeapSort: `heapSort_original.s` (n=6, entrega parcial) e
`heapSort_100k.s` (n=100.000, usado na busca em escala). Compile ambas:

```bash
docker exec -it gem5 riscv64-linux-gnu-gcc -static /workspace/src/heapSort_original.s -o /workspace/src/heapSort_original.riscv
docker exec -it gem5 riscv64-linux-gnu-gcc -static /workspace/src/heapSort_100k.s -o /workspace/src/heapSort_100k.riscv
```

## 4) Executar a simulacao no gem5

Escolha um modelo em /workspace/src/models. Exemplo com inorder (binário n=6):

```bash
docker exec -it gem5 /gem5/build/RISCV/gem5.opt /workspace/src/models/inorder.py --binary /workspace/src/heapSort_original.riscv
```

Outros exemplos:

```bash
docker exec -it gem5 /gem5/build/RISCV/gem5.opt /workspace/src/models/outorder.py --binary /workspace/src/heapSort_original.riscv
docker exec -it gem5 /gem5/build/RISCV/gem5.opt /workspace/src/models/simple-riscv.py --binary /workspace/src/heapSort_original.riscv
docker exec -it gem5 /gem5/build/RISCV/gem5.opt /workspace/src/models/custom_core.py --binary /workspace/src/heapSort_original.riscv
```
