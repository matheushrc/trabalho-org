#!/usr/bin/env bash
# run_all_simulations.sh
# Executa todas as simulacoes parametrizadas do inorder.py,
# cada uma com sua propria pasta de output em /workspace/simulations/
# e com estatisticas no formato estruturado JSON.

set -euo pipefail

GEM5=/gem5/build/RISCV/gem5.opt
SCRIPT=/workspace/src/models/inorder.py
BIN=/workspace/src/heapSort_original.riscv
OUT=/workspace/simulations

# Helper: cria o diretorio e roda a simulacao com estatisticas JSON
run_sim() {
    local outdir="$1"
    shift
    echo ""
    echo "========================================================"
    echo "  INICIANDO: $outdir"
    echo "========================================================"
    mkdir -p "$outdir"
    "$GEM5" --outdir="$outdir" --stats-file="json://$outdir/stats.json" "$SCRIPT" --binary "$BIN" "$@"
    echo "  CONCLUIDO: $outdir"
}

# ---------------------------------------------------------------
# 1. Branch Prediction (usa O3 para expor branchPred)
# ---------------------------------------------------------------
run_sim "$OUT/branch_prediction/LocalBP"  --cpu-type O3 --branch-predictor LocalBP
run_sim "$OUT/branch_prediction/BiModeBP" --cpu-type O3 --branch-predictor BiModeBP

# ---------------------------------------------------------------
# 2. Tipo de CPU
# ---------------------------------------------------------------
run_sim "$OUT/cpu_type/TIMING" --cpu-type TIMING
run_sim "$OUT/cpu_type/O3"     --cpu-type O3

# ---------------------------------------------------------------
# 3. Frequencia de Clock
# ---------------------------------------------------------------
run_sim "$OUT/clock_freq/1GHz" --clk-freq 1GHz
run_sim "$OUT/clock_freq/2GHz" --clk-freq 2GHz
run_sim "$OUT/clock_freq/3GHz" --clk-freq 3GHz
run_sim "$OUT/clock_freq/4GHz" --clk-freq 4GHz

# ---------------------------------------------------------------
# 4. Tamanho da Cache L1 (L1d e L1i juntos)
# ---------------------------------------------------------------
run_sim "$OUT/cache_l1/8kB"  --l1d-size  8kB --l1i-size  8kB
run_sim "$OUT/cache_l1/16kB" --l1d-size 16kB --l1i-size 16kB
run_sim "$OUT/cache_l1/32kB" --l1d-size 32kB --l1i-size 32kB
run_sim "$OUT/cache_l1/64kB" --l1d-size 64kB --l1i-size 64kB

# ---------------------------------------------------------------
# 5. Tamanho da Cache L2
# ---------------------------------------------------------------
run_sim "$OUT/cache_l2/128kB" --l2-size 128kB
run_sim "$OUT/cache_l2/256kB" --l2-size 256kB
run_sim "$OUT/cache_l2/512kB" --l2-size 512kB
run_sim "$OUT/cache_l2/1MB"   --l2-size 1MB

# ---------------------------------------------------------------
# 6. Numero de Cores
# ---------------------------------------------------------------
run_sim "$OUT/num_cores/1core"  --num-cores 1
run_sim "$OUT/num_cores/2cores" --num-cores 2
run_sim "$OUT/num_cores/4cores" --num-cores 4

# ---------------------------------------------------------------
# 7. Tamanho da Memoria Principal
# ---------------------------------------------------------------
run_sim "$OUT/memory/512MB" --memory-size 512MB
run_sim "$OUT/memory/1GB"   --memory-size 1GB
run_sim "$OUT/memory/2GB"   --memory-size 2GB

# ---------------------------------------------------------------
# 8. Hierarquia de Cache
# ---------------------------------------------------------------
run_sim "$OUT/cache_hierarchy/private_l1_l2"         --cache-hierarchy private_l1_l2
run_sim "$OUT/cache_hierarchy/private_l1_private_l2" --cache-hierarchy private_l1_private_l2

echo ""
echo "========================================================"
echo "  TODAS AS SIMULACOES CONCLUIDAS!"
echo "  Resultados em: $OUT"
echo "========================================================"
