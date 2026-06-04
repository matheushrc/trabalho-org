from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import PrivateL1PrivateL2CacheHierarchy
from gem5.components.memory.single_channel import SingleChannelDDR3_1600
from gem5.resources.resource import Resource
from gem5.simulate.simulator import Simulator
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_core import SimpleCore
from gem5.components.processors.simple_processor import SimpleProcessor

import argparse

# Aqui esta "magica": criamos uma funcao para configurar o core
def meu_core_customizado():
    # Instanciamos o core O3 padrao
    core = SimpleCore(cpu_type=CPUTypes.O3, isa=ISA.RISCV, core_id=0)
    
    # Agora acessamos o objeto C++ interno para mudar o hardware
    # Nota: No gem5, o O3CPU tem parametros especificos:
    core.core.numROBEntries = 256      # Aumenta o buffer de reordenacao
    core.core.fetchWidth = 8           # Busca 8 instrucoes por ciclo
    core.core.decodeWidth = 8
    core.core.issueWidth = 8
    core.core.dispatchWidth = 8
    core.core.commitWidth = 8
    
    return core

# No seu script, em vez de SimpleProcessor direto, vocfaz:
processor = SimpleProcessor(
    cpu_type=CPUTypes.O3, 
    isa=ISA.RISCV, 
    num_cores=1
)

# Sobrescrevemos o core padrao pelo nosso tunado
processor.cores = [meu_core_customizado()]

parser = argparse.ArgumentParser()
parser.add_argument(
    "--binary",
    type=str,
    required=True,
    help="Caminho para binario RISC-V"
)
args = parser.parse_args()
binary_path = os.path.abspath(args.binary)


# 2. Configurao de Memria e Cache (Obrigatrio para O3)
cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(l1d_size="32kB", l1i_size="32kB", l2_size="256kB")
memory = SingleChannelDDR3_1600("1GB")

# 3. Montagem da placa
board = SimpleBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)


binary = BinaryResource(local_path=binary_path)
board.set_se_binary_workload(binary)

binary = BinaryResource(local_path=binary_path)
board.set_se_binary_workload(binary)

# 6. Rodar a simulacao
simulator = Simulator(board=board)
print("Iniciando simulacao O3 RISC-V...")
simulator.run()

print(f"Simulacaoo finalizada no tick {simulator.get_current_tick()}")
