# -*- coding: utf-8 -*-

# Copyright (c) 2015 Jason Power
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Script de simulacao parametrizado para RISC-V no gem5.

Variaveis configuráveis via linha de comando:
  --branch-predictor : Preditor de desvio (LocalBP | BiModeBP)
  --cpu-type         : Tipo de CPU (TIMING | O3)
  --clk-freq         : Frequencia do clock (ex: 1GHz, 2GHz, 3GHz, 4GHz)
  --l1d-size         : Tamanho da cache L1 de dados (ex: 16kB, 32kB, 64kB)
  --l1i-size         : Tamanho da cache L1 de instrucoes (ex: 16kB, 32kB, 64kB)
  --l2-size          : Tamanho da cache L2 (ex: 128kB, 256kB, 512kB, 1MB)
  --num-cores        : Numero de cores (ex: 1, 2, 4)
  --memory-size      : Tamanho da memoria principal (ex: 512MB, 1GB, 2GB)
  --cache-hierarchy  : Hierarquia de cache (private_l1_l2 | private_l1_private_l2)
  --binary           : Caminho para o binario RISC-V (obrigatorio)

Exemplos de uso:
  # Branch Prediction: LocalBP (simples) vs BiModeBP (global complexo)
  gem5.opt inorder.py --binary ./heapSort.riscv --branch-predictor LocalBP
  gem5.opt inorder.py --binary ./heapSort.riscv --branch-predictor BiModeBP

  # Variacao de clock
  gem5.opt inorder.py --binary ./heapSort.riscv --clk-freq 1GHz
  gem5.opt inorder.py --binary ./heapSort.riscv --clk-freq 4GHz

  # Variacao de cache
  gem5.opt inorder.py --binary ./heapSort.riscv --l1d-size 16kB --l2-size 128kB
  gem5.opt inorder.py --binary ./heapSort.riscv --l1d-size 64kB --l2-size 1MB
"""

import os
import sys

GEM5_ROOT = os.environ.get("GEM5_ROOT", "/gem5")
GEM5_PYTHON = os.path.join(GEM5_ROOT, "src", "python")
if GEM5_PYTHON not in sys.path:
    sys.path.insert(0, GEM5_PYTHON)

import m5
from m5.objects import *

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_core import SimpleCore
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from gem5.isas import ISA

import argparse

# ---------------------------------------------------------------------------
# Argumentos de linha de comando
# ---------------------------------------------------------------------------

VALID_BRANCH_PREDICTORS = ["LocalBP", "BiModeBP"]
VALID_CPU_TYPES = ["TIMING", "O3"]
VALID_CACHE_HIERARCHIES = ["private_l1_l2", "private_l1_private_l2"]

parser = argparse.ArgumentParser(
    description="Simulacao parametrizada RISC-V no gem5 (modo in-order / pipeline)"
)

# Binario obrigatorio
parser.add_argument(
    "--binary",
    type=str,
    required=True,
    help="Caminho para o binario RISC-V a ser simulado",
)

# Branch Prediction
parser.add_argument(
    "--branch-predictor",
    type=str,
    default="LocalBP",
    choices=VALID_BRANCH_PREDICTORS,
    help=(
        "Tecnica de branch prediction:\n"
        "  LocalBP   - preditor local simples (historico por PC)\n"
        "  BiModeBP  - preditor global complexo (tabela de 2 bits)\n"
        "Padrao: LocalBP"
    ),
)

# Tipo de CPU
parser.add_argument(
    "--cpu-type",
    type=str,
    default="TIMING",
    choices=VALID_CPU_TYPES,
    help=(
        "Modelo de CPU:\n"
        "  TIMING - pipeline in-order (padrao para este script)\n"
        "  O3     - out-of-order superscalar\n"
        "Padrao: TIMING"
    ),
)

# Frequencia do clock
parser.add_argument(
    "--clk-freq",
    type=str,
    default="3GHz",
    help="Frequencia do clock da placa (ex: 1GHz, 2GHz, 3GHz, 4GHz). Padrao: 3GHz",
)

# Tamanhos de cache
parser.add_argument(
    "--l1d-size",
    type=str,
    default="32kB",
    help="Tamanho da cache L1 de dados (ex: 8kB, 16kB, 32kB, 64kB). Padrao: 32kB",
)
parser.add_argument(
    "--l1i-size",
    type=str,
    default="32kB",
    help="Tamanho da cache L1 de instrucoes (ex: 8kB, 16kB, 32kB, 64kB). Padrao: 32kB",
)
parser.add_argument(
    "--l2-size",
    type=str,
    default="256kB",
    help="Tamanho da cache L2 unificada (ex: 128kB, 256kB, 512kB, 1MB). Padrao: 256kB",
)

# Numero de cores
parser.add_argument(
    "--num-cores",
    type=int,
    default=1,
    help="Numero de cores do processador (ex: 1, 2, 4). Padrao: 1",
)

# Tamanho da memoria
parser.add_argument(
    "--memory-size",
    type=str,
    default="1GB",
    help="Tamanho da memoria principal DDR3 (ex: 512MB, 1GB, 2GB). Padrao: 1GB",
)

# Hierarquia de cache
parser.add_argument(
    "--cache-hierarchy",
    type=str,
    default="private_l1_private_l2",
    choices=VALID_CACHE_HIERARCHIES,
    help=(
        "Tipo de hierarquia de cache:\n"
        "  private_l1_l2         - alias para private_l1_private_l2\n"
        "  private_l1_private_l2 - L1 e L2 privadas por nucleo\n"
        "Padrao: private_l1_private_l2"
    ),
)

args = parser.parse_args()
binary_path = os.path.abspath(args.binary)

# ---------------------------------------------------------------------------
# Mapeamento de parametros
# ---------------------------------------------------------------------------

CPU_TYPE_MAP = {
    "TIMING": CPUTypes.TIMING,
    "O3": CPUTypes.O3,
}

cpu_type = CPU_TYPE_MAP[args.cpu_type]

# ---------------------------------------------------------------------------
# Exibicao da configuracao escolhida
# ---------------------------------------------------------------------------

print("=" * 60)
print("  Configuracao da Simulacao gem5 (RISC-V In-Order/Pipeline)")
print("=" * 60)
print(f"  Binario            : {binary_path}")
print(f"  Branch Predictor   : {args.branch_predictor}")
print(f"  Tipo de CPU        : {args.cpu_type}")
print(f"  Frequencia do Clock: {args.clk_freq}")
print(f"  Cache L1d          : {args.l1d_size}")
print(f"  Cache L1i          : {args.l1i_size}")
print(f"  Cache L2           : {args.l2_size}")
print(f"  Numero de Cores    : {args.num_cores}")
print(f"  Tamanho da Memoria : {args.memory_size}")
print(f"  Hierarquia Cache   : {args.cache_hierarchy}")
print("=" * 60)

# ---------------------------------------------------------------------------
# 1. Processador
# ---------------------------------------------------------------------------

processor = SimpleProcessor(
    cpu_type=cpu_type,
    num_cores=args.num_cores,
    isa=ISA.RISCV,
)

# ---------------------------------------------------------------------------
# 2. Branch Predictor
#    Aplica o preditor escolhido em cada core (suportado pelo O3CPU e MinorCPU)
# ---------------------------------------------------------------------------

def apply_branch_predictor(processor, predictor_name):
    """
    Configura o preditor de desvio em cada core do processador.

    gem5 suporta varios preditores via parametro branchPred do CPU:
      - LocalBP   : preditor local simples (historico por PC, tabela de 2 bits)
      - BiModeBP  : preditor global (tabela indexada por PC, 2 bits por entrada)

    Nota: a configuracao direta via `core.branchPred` so e possivel para
    modelos de CPU que expoe esse atributo (O3CPU, MinorCPU). Para CPUs
    TIMING simples o preditor nao e configuravel desta forma, mas o
    argumento e registrado para fins de documentacao e comparacao.
    """
    predictor_map = {
        "LocalBP": lambda: BranchPredictor(conditionalBranchPred=LocalBP()),
        "BiModeBP": lambda: BranchPredictor(conditionalBranchPred=BiModeBP()),
    }

    predictor_creator = predictor_map.get(predictor_name)
    if predictor_creator is None:
        print(f"[AVISO] Preditor '{predictor_name}' desconhecido. Usando padrao do gem5.")
        return

    for core in processor.cores:
        cpu = core.core
        # Verifica se o modelo de CPU suporta branchPred
        if hasattr(cpu, "branchPred"):
            cpu.branchPred = predictor_creator()
            print(f"  [OK] branchPred = {predictor_name} aplicado ao core {cpu}")
        else:
            print(
                f"  [INFO] CPU '{type(cpu).__name__}' nao expoe 'branchPred' diretamente.\n"
                f"         O preditor '{predictor_name}' foi selecionado e sera registrado,\n"
                f"         mas a CPU usa o preditor interno padrao."
            )

# ---------------------------------------------------------------------------
# 3. Hierarquia de Cache
# ---------------------------------------------------------------------------

# Ambas as opcoes usam PrivateL1PrivateL2CacheHierarchy.
# O argumento --cache-hierarchy existe para deixar claro ao usuario
# qual configuracao foi escolhida e permitir extensao futura.
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size=args.l1d_size,
    l1i_size=args.l1i_size,
    l2_size=args.l2_size,
)

# ---------------------------------------------------------------------------
# 4. Memoria principal
# ---------------------------------------------------------------------------

memory = SingleChannelDDR3_1600(args.memory_size)

# ---------------------------------------------------------------------------
# 5. Montagem da placa (board)
# ---------------------------------------------------------------------------

board = SimpleBoard(
    clk_freq=args.clk_freq,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

# ---------------------------------------------------------------------------
# 6. Aplicar branch predictor (apos montar a placa, cores ja instanciados)
# ---------------------------------------------------------------------------

apply_branch_predictor(processor, args.branch_predictor)

# ---------------------------------------------------------------------------
# 7. Workload (binario)
# ---------------------------------------------------------------------------

binary = BinaryResource(local_path=binary_path)
board.set_se_binary_workload(binary)

# ---------------------------------------------------------------------------
# 8. Execucao da simulacao
# ---------------------------------------------------------------------------

simulator = Simulator(board=board)

print(f"\nIniciando simulacao RISC-V (CPU={args.cpu_type}, BP={args.branch_predictor}, CLK={args.clk_freq})...")
simulator.run()

print(f"\nSimulacao finalizada no tick {simulator.get_current_tick()}")
print("=" * 60)
