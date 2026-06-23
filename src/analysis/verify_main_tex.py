#!/usr/bin/env python3
"""Verifica os números do relatório (trabalho_latex/main.tex) contra os
dados brutos das simulações gem5.

Cada alegação do texto/tabelas é comparada com o valor recalculado a partir
de stats.json (ou de search_raw_results.json, para a tabela de escala). Imprime
um relatório PASS/FAIL com valor esperado (no .tex) vs. valor obtido.

Execução:
    python3 src/analysis/verify_main_tex.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "lib"))

from gem5_stats import Metrics  # noqa: E402

SIM = os.path.join(ROOT, "simulations")
SEARCH_JSON = os.path.join(ROOT, "analysis", "search_raw_results.json")

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

_results = []


def check(label, expected, actual, tol=0.01, unit=""):
    """Compara esperado vs. obtido com tolerância relativa (tol).

    'expected' e 'actual' devem estar na mesma escala. Para taxas/percentuais,
    passe os dois em pontos percentuais (use rate*100 no chamador).
    """
    if actual is None:
        status, ok = f"{YELLOW}SKIP{RESET}", None
        shown = "sem dado"
    else:
        if expected == 0:
            ok = abs(actual) < 1e-6
        else:
            ok = abs(actual - expected) / abs(expected) <= tol
        status = f"{GREEN}PASS{RESET}" if ok else f"{RED}FAIL{RESET}"
        shown = f"esperado {expected:,.3f}{unit}  obtido {actual:,.3f}{unit}"
    _results.append(ok)
    print(f"  [{status}] {label}: {shown}")


def section(title):
    print(f"\n{'='*70}\n{title}\n{'='*70}")


def pct_var(local, bimode):
    return (bimode - local) / local * 100.0


# ----------------------------------------------------------------------
# Tabela 1 — baseline (CPU TIMING, 3 GHz, n=6)
# ----------------------------------------------------------------------
def verify_baseline():
    section("Tabela 1 — Baseline (CPU em-ordem TIMING, 3 GHz, n=6)")
    m = Metrics(os.path.join(SIM, "cpu_type", "TIMING", "stats.json"))
    check("simTicks", 106_596_297, m.sim_ticks)
    check("IPC", 0.395, m.ipc, tol=0.01)
    check("simInsts", 126_371, m.sim_insts)
    check("Misses L1D (demanda)", 548, m.l1d_demand_misses)
    check("Taxa de miss L1D", 1.95, m.l1d_demand_miss_rate * 100, unit="%")


# ----------------------------------------------------------------------
# Tabela 2 — LocalBP vs BiModeBP (CPU O3, n=6)
# ----------------------------------------------------------------------
def verify_branch():
    section("Tabela 2 — LocalBP vs BiModeBP (CPU O3, n=6)")
    lo = Metrics(os.path.join(SIM, "branch_prediction", "LocalBP", "stats.json"))
    bi = Metrics(os.path.join(SIM, "branch_prediction", "BiModeBP", "stats.json"))

    print("  Nota: a 'taxa de erro global' tabulada (5,30%/3,18%) corresponde a")
    print("  mispredicted/committed; o texto a descreve como condIncorrect/lookups")
    print("  (3,54%/2,51%) — inconsistência editorial sinalizada abaixo.\n")

    print(" LocalBP:")
    check("lookups (BTBLookups)", 46_370, lo.bp_lookups)
    check("predições incorretas", 1_643, lo.cond_incorrect)
    check("taxa de erro global (tabela = mispred/committed)", 5.30, lo.mispred_over_committed * 100, tol=0.03, unit="%")
    check("erros DirectCond", 1_421, lo.directcond_mispredicted)
    check("desvios DirectCond", 21_909, lo.directcond_committed)
    check("precisão condicional", 95.05, lo.cond_precision * 100, unit="%")
    check("simTicks", 36_084_546, lo.sim_ticks)
    check("IPC", 1.166, lo.ipc, tol=0.01)

    print("\n BiModeBP:")
    check("lookups (BTBLookups)", 39_218, bi.bp_lookups)
    check("predições incorretas", 984, bi.cond_incorrect)
    check("taxa de erro global (tabela = mispred/committed)", 3.18, bi.mispred_over_committed * 100, tol=0.03, unit="%")
    check("erros DirectCond", 772, bi.directcond_mispredicted)
    check("desvios DirectCond", 21_909, bi.directcond_committed)
    check("precisão condicional", 96.39, bi.cond_precision * 100, unit="%")
    check("simTicks", 35_149_815, bi.sim_ticks)
    check("IPC", 1.197, bi.ipc, tol=0.01)

    print("\n Variações (BiMode vs Local):")
    check("Var. lookups", -15.4, pct_var(lo.bp_lookups, bi.bp_lookups), tol=0.05, unit="%")
    check("Var. incorretas", -40.1, pct_var(lo.cond_incorrect, bi.cond_incorrect), tol=0.05, unit="%")
    check("Var. simTicks", -2.6, pct_var(lo.sim_ticks, bi.sim_ticks), tol=0.10, unit="%")
    check("Var. IPC", +2.7, pct_var(lo.ipc, bi.ipc), tol=0.10, unit="%")
    # Texto da Discussão: erro DirectCond 6,49% -> 3,52%
    check("erro DirectCond LocalBP (texto 6,49%)", 6.49, lo.directcond_error_rate * 100, tol=0.03, unit="%")
    check("erro DirectCond BiModeBP (texto 3,52%)", 3.52, bi.directcond_error_rate * 100, tol=0.03, unit="%")


# ----------------------------------------------------------------------
# Tabela 3 — efeito de escala (n=100.000, busca em grade)
# ----------------------------------------------------------------------
def verify_scale():
    section("Tabela 3 — Efeito de escala (n=100.000, grid search)")
    if not os.path.exists(SEARCH_JSON):
        print(f"  {YELLOW}SKIP{RESET} {SEARCH_JSON} não encontrado")
        return
    rows = json.load(open(SEARCH_JSON))

    def find(cpu, bp, clk, l1):
        # A Tabela 3 usa pares controlados da busca em GRADE (grid_*);
        # amostras aleatórias (random_*) variam outros parâmetros e não pareiam.
        for r in rows:
            if r.get("search_type") != "grid":
                continue
            c = r["config"]
            if (c["cpu_type"] == cpu and c["branch_predictor"] == bp
                    and c["clk_freq"] == clk and c["l1_size"] == l1):
                return r["ticks"]
        return None

    # (cpu, clk, l1, local_esperado, bimode_esperado, var_esperada)
    pairs = [
        ("TIMING", "2GHz", "16kB", 72_559_366_000, 72_559_366_000, 0.0),
        ("TIMING", "4GHz", "64kB", 36_381_554_750, 36_381_554_750, 0.0),
        ("O3", "2GHz", "16kB", 19_998_213_500, 18_834_237_500, -5.8),
        ("O3", "2GHz", "64kB", 18_792_986_000, 17_588_158_500, -6.4),
        ("O3", "4GHz", "16kB", 11_015_935_000, 10_428_981_250, -5.3),
        ("O3", "4GHz", "64kB", 10_388_132_750, 9_778_474_250, -5.9),
    ]
    for cpu, clk, l1, e_lo, e_bi, e_var in pairs:
        lo = find(cpu, "LocalBP", clk, l1)
        bi = find(cpu, "BiModeBP", clk, l1)
        tag = f"{cpu} {clk}/{l1}"
        check(f"{tag} LocalBP ticks", e_lo, lo, tol=0.001)
        check(f"{tag} BiModeBP ticks", e_bi, bi, tol=0.001)
        if lo and bi:
            check(f"{tag} Var.", e_var, pct_var(lo, bi), tol=0.10 if e_var else 0, unit="%")


def main():
    print(f"Raiz do projeto: {ROOT}")
    verify_baseline()
    verify_branch()
    verify_scale()

    section("Resumo")
    passed = sum(1 for r in _results if r is True)
    failed = sum(1 for r in _results if r is False)
    skipped = sum(1 for r in _results if r is None)
    print(f"  PASS: {passed}   FAIL: {failed}   SKIP: {skipped}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
