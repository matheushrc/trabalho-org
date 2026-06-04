# Execucao da simulacao com Docker

## 1) Subir o container

```bash
docker compose up -d --build
```

## 2) Compilar o programa RISC-V no container

```bash
docker exec -it gem5 bash
```

Dentro do container:

```bash
riscv64-linux-gnu-gcc -static /workspace/src/heapSort_gem5.s -o /workspace/src/heapSort.riscv
```

## 3) Construir o gem5 para RISC-V (primeira vez)

```bash
cd /gem5
scons build/RISCV/gem5.opt -j2
```

## 4) Executar a simulacao no gem5

Escolha um modelo em /workspace/src/models. Exemplo com inorder:

```bash
/gem5/build/RISCV/gem5.opt /workspace/src/models/inorder.py --binary /workspace/src/heapSort.riscv
```

Outros exemplos:

```bash
/gem5/build/RISCV/gem5.opt /workspace/src/models/outorder.py --binary /workspace/src/heapSort.riscv
/gem5/build/RISCV/gem5.opt /workspace/src/models/simple-riscv.py --binary /workspace/src/heapSort.riscv
/gem5/build/RISCV/gem5.opt /workspace/src/models/custom_core.py --binary /workspace/src/heapSort.riscv
```
