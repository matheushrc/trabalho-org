# Simulações Parametrizadas — gem5 RISC-V (inorder.py)

Cada simulação gera seus arquivos de configuração na pasta `/workspace/simulations/<grupo>/<variante>/` e as estatísticas de desempenho formatadas em JSON no arquivo `stats.json`.

O flag `--outdir` e `--stats-file` são passados **ao gem5** (antes do script), não ao script Python.

> **Baseline de referência** usado em todos os grupos (salvo quando a variável do grupo muda):
> - Branch Predictor : `LocalBP`
> - CPU Type         : `TIMING`
> - Clock            : `3GHz`
> - Cache L1d / L1i  : `32kB`
> - Cache L2         : `256kB`
> - Núcleos          : `1`
> - Memória          : `1GB`
> - Hierarquia Cache : `private_l1_private_l2`

---

## 0. Pré-requisito: compilar o binário (uma única vez)

```bash
docker exec -it gem5 riscv64-linux-gnu-gcc -static \
  /workspace/src/heapSort_original.s \
  -o /workspace/src/heapSort_original.riscv
```

---

## 1. Branch Prediction

Compara `LocalBP` (preditor local simples) com `BiModeBP` (preditor global complexo).  
Usa CPU `O3` pois é o modelo que expõe `branchPred` no gem5.

```bash
# 1.1 LocalBP — preditor local simples
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/branch_prediction/LocalBP \
  --stats-file=json:///workspace/simulations/branch_prediction/LocalBP/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --cpu-type O3 \
  --branch-predictor LocalBP

# 1.2 BiModeBP — preditor global complexo
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/branch_prediction/BiModeBP \
  --stats-file=json:///workspace/simulations/branch_prediction/BiModeBP/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --cpu-type O3 \
  --branch-predictor BiModeBP
```

---

## 2. Tipo de CPU

```bash
# 2.1 TIMING — pipeline in-order
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cpu_type/TIMING \
  --stats-file=json:///workspace/simulations/cpu_type/TIMING/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --cpu-type TIMING

# 2.2 O3 — out-of-order superescalar
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cpu_type/O3 \
  --stats-file=json:///workspace/simulations/cpu_type/O3/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --cpu-type O3
```

---

## 3. Frequência de Clock

```bash
# 3.1 1GHz
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/clock_freq/1GHz \
  --stats-file=json:///workspace/simulations/clock_freq/1GHz/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --clk-freq 1GHz

# 3.2 2GHz
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/clock_freq/2GHz \
  --stats-file=json:///workspace/simulations/clock_freq/2GHz/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --clk-freq 2GHz

# 3.3 3GHz (baseline)
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/clock_freq/3GHz \
  --stats-file=json:///workspace/simulations/clock_freq/3GHz/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --clk-freq 3GHz

# 3.4 4GHz
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/clock_freq/4GHz \
  --stats-file=json:///workspace/simulations/clock_freq/4GHz/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --clk-freq 4GHz
```

---

## 4. Tamanho da Cache L1 (L1d e L1i juntos)

```bash
# 4.1 L1 = 8kB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l1/8kB \
  --stats-file=json:///workspace/simulations/cache_l1/8kB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l1d-size 8kB --l1i-size 8kB

# 4.2 L1 = 16kB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l1/16kB \
  --stats-file=json:///workspace/simulations/cache_l1/16kB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l1d-size 16kB --l1i-size 16kB

# 4.3 L1 = 32kB (baseline)
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l1/32kB \
  --stats-file=json:///workspace/simulations/cache_l1/32kB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l1d-size 32kB --l1i-size 32kB

# 4.4 L1 = 64kB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l1/64kB \
  --stats-file=json:///workspace/simulations/cache_l1/64kB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l1d-size 64kB --l1i-size 64kB
```

---

## 5. Tamanho da Cache L2

```bash
# 5.1 L2 = 128kB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l2/128kB \
  --stats-file=json:///workspace/simulations/cache_l2/128kB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l2-size 128kB

# 5.2 L2 = 256kB (baseline)
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l2/256kB \
  --stats-file=json:///workspace/simulations/cache_l2/256kB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l2-size 256kB

# 5.3 L2 = 512kB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l2/512kB \
  --stats-file=json:///workspace/simulations/cache_l2/512kB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l2-size 512kB

# 5.4 L2 = 1MB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_l2/1MB \
  --stats-file=json:///workspace/simulations/cache_l2/1MB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --l2-size 1MB
```

---

## 6. Número de Cores

```bash
# 6.1 1 core (baseline)
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/num_cores/1core \
  --stats-file=json:///workspace/simulations/num_cores/1core/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --num-cores 1

# 6.2 2 cores
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/num_cores/2cores \
  --stats-file=json:///workspace/simulations/num_cores/2cores/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --num-cores 2

# 6.3 4 cores
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/num_cores/4cores \
  --stats-file=json:///workspace/simulations/num_cores/4cores/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --num-cores 4
```

---

## 7. Tamanho da Memória Principal

```bash
# 7.1 512MB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/memory/512MB \
  --stats-file=json:///workspace/simulations/memory/512MB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --memory-size 512MB

# 7.2 1GB (baseline)
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/memory/1GB \
  --stats-file=json:///workspace/simulations/memory/1GB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --memory-size 1GB

# 7.3 2GB
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/memory/2GB \
  --stats-file=json:///workspace/simulations/memory/2GB/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --memory-size 2GB
```

---

## 8. Hierarquia de Cache

```bash
# 8.1 private_l1_l2
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_hierarchy/private_l1_l2 \
  --stats-file=json:///workspace/simulations/cache_hierarchy/private_l1_l2/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --cache-hierarchy private_l1_l2

# 8.2 private_l1_private_l2 (baseline)
docker exec -it gem5 /gem5/build/RISCV/gem5.opt \
  --outdir=/workspace/simulations/cache_hierarchy/private_l1_private_l2 \
  --stats-file=json:///workspace/simulations/cache_hierarchy/private_l1_private_l2/stats.json \
  /workspace/src/models/inorder.py \
  --binary /workspace/src/heapSort_original.riscv \
  --cache-hierarchy private_l1_private_l2
```

---

## 9. Executar todas as simulações em sequência

Execute dentro do container com:

```bash
docker exec -it gem5 bash /workspace/run_all_simulations.sh
```

---

## Estrutura de saída gerada

Após rodar todas as simulações, a pasta `simulations/` terá a seguinte estrutura:

```
simulations/
├── branch_prediction/
│   ├── LocalBP/         ← stats.json, config.ini, config.json, ...
│   └── BiModeBP/
├── cpu_type/
│   ├── TIMING/
│   └── O3/
...
```

O arquivo principal contendo as métricas de desempenho será o **`stats.json`** de cada pasta de resultado.
