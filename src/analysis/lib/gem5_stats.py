"""Biblioteca reutilizável para ler stats.json do gem5.

Centraliza toda a lógica de extração de métricas dispersa nos scripts
antigos (analyze*.py, parse_bp_stats.py, check_*_bp.py, compare_all_sims.py).
Todas as métricas citadas no relatório (main.tex) são derivadas daqui.

Uso:
    from gem5_stats import load_stats, Metrics
    m = Metrics("simulations/branch_prediction/LocalBP/stats.json")
    print(m.sim_ticks, m.ipc, m.cond_incorrect, m.l1d_demand_misses)
"""
import json
import os

# Ordem dos tipos de desvio nos vetores Vector2d do branchPred do gem5.
BRANCH_TYPES = [
    "NoBranch", "Return", "CallDirect", "CallIndirect",
    "DirectCond", "DirectUncond", "IndirectCond", "IndirectUncond",
]


def load_stats(path):
    """Carrega stats.json (lista ou objeto) e devolve o dump do tick final."""
    with open(path) as f:
        data = json.load(f)
    return data[0] if isinstance(data, list) else data


def _scalar(node):
    """Extrai o campo 'value' escalar de um nó de estatística do gem5."""
    if isinstance(node, dict) and "value" in node:
        return node["value"]
    return node


def _branchpred(stats):
    """Localiza o nó branchPred do primeiro core (estrutura aninhada do gem5)."""
    try:
        cores = stats["board"]["processor"]["cores"]
        if isinstance(cores, dict):  # nó Vector: lista fica sob 'value'
            cores = cores["value"]
        return cores[0]["core"]["branchPred"]
    except (KeyError, IndexError, TypeError):
        return None


def _vec2d_by_type(node, btype):
    """Soma o valor de um Vector2d do branchPred para um tipo de desvio.

    Os Vector2d têm forma {value: {thread: {value: {type_idx: {value}}}}}.
    Somamos sobre todas as threads para o índice do tipo pedido.
    """
    idx = str(BRANCH_TYPES.index(btype))
    total = 0.0
    threads = node.get("value", {})
    for _, tnode in threads.items():
        per_type = tnode.get("value", {})
        cell = per_type.get(idx)
        if cell is not None:
            total += cell.get("value", 0.0)
    return total


class Metrics:
    """Métricas de interesse de uma simulação, prontas para verificação."""

    def __init__(self, path):
        self.path = path
        self.stats = load_stats(path)
        self.bp = _branchpred(self.stats)

    # --- métricas globais ---------------------------------------------
    @property
    def sim_insts(self):
        return _scalar(self.stats.get("simInsts"))

    @property
    def sim_ticks(self):
        return _scalar(self.stats.get("simTicks"))

    @property
    def num_cycles(self):
        """core_numCycles no topo (dumps trimados antigos) ou aninhado em
        board.processor.cores[].core.numCycles (dump nativo completo)."""
        flat = self.stats.get("core_numCycles")
        if flat is not None:
            return _scalar(flat)
        try:
            cores = self.stats["board"]["processor"]["cores"]
            if isinstance(cores, dict):
                cores = cores["value"]
            return _scalar(cores[0]["core"]["numCycles"])
        except (KeyError, IndexError, TypeError):
            return None

    @property
    def ipc(self):
        c = self.num_cycles
        return self.sim_insts / c if c else None

    # --- predição de desvios (apenas CPU O3) --------------------------
    @property
    def bp_lookups(self):
        """Total de consultas ao BTB (rótulo 'lookups' na Tabela 2)."""
        return _scalar(self.bp.get("BTBLookups")) if self.bp else None

    @property
    def cond_predicted(self):
        return _scalar(self.bp.get("condPredicted")) if self.bp else None

    @property
    def cond_incorrect(self):
        return _scalar(self.bp.get("condIncorrect")) if self.bp else None

    @property
    def cond_error_rate(self):
        cp = self.cond_predicted
        return self.cond_incorrect / cp if cp else None

    @property
    def global_error_rate(self):
        """condIncorrect / BTBLookups (taxa de erro global da Tabela 2)."""
        lk = self.bp_lookups
        return self.cond_incorrect / lk if lk else None

    @property
    def total_committed(self):
        """Soma de desvios commitados de todos os tipos."""
        if not self.bp:
            return None
        return sum(_vec2d_by_type(self.bp["committed"], t) for t in BRANCH_TYPES)

    @property
    def total_mispredicted(self):
        """Soma de desvios commitados mal previstos, todos os tipos."""
        if not self.bp:
            return None
        return sum(_vec2d_by_type(self.bp["mispredicted"], t) for t in BRANCH_TYPES)

    @property
    def mispred_over_committed(self):
        """total_mispredicted / total_committed.

        É o valor de fato tabulado como 'taxa de erro global' no main.tex
        (o texto descreve condIncorrect/lookups, que resulta em outro número).
        """
        c = self.total_committed
        return self.total_mispredicted / c if c else None

    @property
    def directcond_committed(self):
        return _vec2d_by_type(self.bp["committed"], "DirectCond") if self.bp else None

    @property
    def directcond_mispredicted(self):
        return _vec2d_by_type(self.bp["mispredicted"], "DirectCond") if self.bp else None

    @property
    def directcond_error_rate(self):
        d = self.directcond_committed
        return self.directcond_mispredicted / d if d else None

    @property
    def cond_precision(self):
        """Precisão condicional = 1 - condIncorrect/condPredicted."""
        r = self.cond_error_rate
        return 1 - r if r is not None else None

    # --- cache L1D -----------------------------------------------------
    def _l1d_by_cmd(self):
        return self.stats.get("l1d_cache_0_by_cmd", {})

    @property
    def l1d_demand_misses(self):
        """Misses de demanda (ReadReq + WriteReq), excluindo atômicas."""
        by = self._l1d_by_cmd()
        return sum(by.get(c, {}).get("misses", 0.0) for c in ("ReadReq", "WriteReq"))

    @property
    def l1d_demand_accesses(self):
        by = self._l1d_by_cmd()
        tot = 0.0
        for c in ("ReadReq", "WriteReq"):
            cmd = by.get(c, {})
            tot += cmd.get("hits", 0.0) + cmd.get("misses", 0.0)
        return tot

    @property
    def l1d_demand_miss_rate(self):
        a = self.l1d_demand_accesses
        return self.l1d_demand_misses / a if a else None


def discover(root="simulations"):
    """Devolve {caminho_relativo_da_pasta: Metrics} para todo stats.json achado."""
    out = {}
    for dirpath, _, files in os.walk(root):
        if "stats.json" in files:
            p = os.path.join(dirpath, "stats.json")
            try:
                out[dirpath] = Metrics(p)
            except Exception as e:  # pragma: no cover
                print(f"[warn] falha ao ler {p}: {e}")
    return out
