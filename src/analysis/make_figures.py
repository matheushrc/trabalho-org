#!/usr/bin/env python3
"""Gera as figuras do relatório a partir dos dados BRUTOS do gem5.

Todos os valores são lidos de simulations/**/stats.json (via gem5_stats) —
nada é digitado à mão. As figuras saem em trabalho_latex/figuras/*.png.

Conforme o tópico 2 do enunciado (Branch Prediction em pipeline EM-ORDEM), a
comparação LocalBP vs. BiModeBP usa a CPU TIMING (in-order) tanto em n=6
quanto em n=100.000, de onde saem as métricas pedidas: total de desvios
avaliados e erros de predição. Em ambas as escalas o simTicks é idêntico
entre os dois preditores — o modelo em-ordem não modela penalidade de
misprediction no tempo, então o ganho do BiModeBP aparece apenas na
contagem/taxa de erros, não no tempo de simulação.

Execução:
    python3 src/analysis/make_figures.py
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "lib"))
from gem5_stats import Metrics  # noqa: E402

FIG_DIR = os.path.join(ROOT, "trabalho_latex", "figuras")
os.makedirs(FIG_DIR, exist_ok=True)

C_LOCAL = "#4C72B0"   # LocalBP  (azul)
C_BIMODE = "#DD5E47"  # BiModeBP (laranja/vermelho)
plt.rcParams.update({"font.size": 12, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.axisbelow": True})

# Comparação em pipeline EM-ORDEM (TIMING) — métricas do enunciado, n=6 e n=100k
LO = Metrics(os.path.join(ROOT, "simulations", "branch_prediction_inorder", "LocalBP", "stats.json"))
BI = Metrics(os.path.join(ROOT, "simulations", "branch_prediction_inorder", "BiModeBP", "stats.json"))
LO_100K = Metrics(os.path.join(ROOT, "simulations", "branch_prediction_inorder_100k", "LocalBP", "stats.json"))
BI_100K = Metrics(os.path.join(ROOT, "simulations", "branch_prediction_inorder_100k", "BiModeBP", "stats.json"))


def _save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✔ {os.path.relpath(path, ROOT)}")


def _grouped(ax, labels, local_vals, bimode_vals, fmt="{:,.0f}"):
    x = np.arange(len(labels))
    w = 0.38
    b1 = ax.bar(x - w / 2, local_vals, w, label="LocalBP", color=C_LOCAL)
    b2 = ax.bar(x + w / 2, bimode_vals, w, label="BiModeBP", color=C_BIMODE)
    for bars in (b1, b2):
        for r in bars:
            ax.annotate(fmt.format(r.get_height()),
                        (r.get_x() + r.get_width() / 2, r.get_height()),
                        ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()


def fig_inorder():
    """Figura principal (EM-ORDEM, TIMING, n=6): erros de predição e taxas.

    Painel A — contagens: total de desvios avaliados, predições incorretas e
    erros nos desvios condicionais diretos (DirectCond, as comparações de
    heapify). Painel B — taxas de erro (%).
    """
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.6))
    fig.suptitle("LocalBP vs. BiModeBP — pipeline em-ordem (TIMING, n=6)",
                 fontweight="bold", y=1.02)

    # Painel A: contagens (erros). Desvios avaliados é igual p/ ambos (em-ordem).
    _grouped(a1, ["Predições\nincorretas", "Erros em\nDirectCond"],
             [LO.cond_incorrect, LO.directcond_mispredicted],
             [BI.cond_incorrect, BI.directcond_mispredicted])
    a1.set_ylabel("Quantidade de erros")
    a1.set_ylim(0, LO.cond_incorrect * 1.45)
    a1.legend(loc="upper right")
    var_tot = (BI.cond_incorrect - LO.cond_incorrect) / LO.cond_incorrect * 100
    var_dc = (BI.directcond_mispredicted - LO.directcond_mispredicted) / LO.directcond_mispredicted * 100
    a1.set_title(f"Erros de predição\nBiModeBP: {var_tot:+.1f}% / DirectCond {var_dc:+.1f}%")

    # Painel B: taxas de erro (%)
    lo_g = LO.cond_incorrect / LO.bp_lookups * 100
    bi_g = BI.cond_incorrect / BI.bp_lookups * 100
    lo_dc = LO.directcond_mispredicted / LO.directcond_committed * 100
    bi_dc = BI.directcond_mispredicted / BI.directcond_committed * 100
    _grouped(a2, ["Taxa de erro\nglobal", "Taxa de erro\nDirectCond"],
             [lo_g, lo_dc], [bi_g, bi_dc], fmt="{:.2f}%")
    a2.set_ylabel("Taxa de erro (%)")
    a2.set_ylim(0, max(lo_g, lo_dc, bi_g, bi_dc) * 1.25)
    a2.set_title(f"Total de desvios avaliados: {LO.bp_lookups:,.0f}\n(igual p/ ambos — sem especulação)")

    fig.tight_layout()
    _save(fig, "comparacao_inorder.png")


def fig_volume():
    """Volume: desvios avaliados e desvios DirectCond (EM-ORDEM, TIMING, n=6).

    Recriação da antiga volume_e_desvios.png (que usava dados O3), agora com
    os números em-ordem corretos.
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _grouped(ax, ["Desvios avaliados\n(lookups)", "Desvios DirectCond"],
             [LO.bp_lookups, LO.directcond_committed],
             [BI.bp_lookups, BI.directcond_committed])
    ax.set_ylabel("Quantidade")
    ax.set_title("Volume de desvios avaliados (pipeline em-ordem, TIMING, n=6)\nidêntico para os dois preditores")
    _save(fig, "volume_e_desvios.png")


def fig_incorretas():
    """Predições incorretas totais e erros em DirectCond (EM-ORDEM, TIMING, n=6).

    Recriação da antiga predicoes_incorretas.png com dados em-ordem corretos.
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _grouped(ax, ["Total de predições\nincorretas", "Erros em DirectCond"],
             [LO.cond_incorrect, LO.directcond_mispredicted],
             [BI.cond_incorrect, BI.directcond_mispredicted])
    ax.set_ylabel("Quantidade de erros")
    ax.set_ylim(0, LO.cond_incorrect * 1.3)
    ax.set_title("Impacto nas predições incorretas (pipeline em-ordem, TIMING, n=6)")
    _save(fig, "predicoes_incorretas.png")


def fig_taxas():
    """Taxa de erro global e em DirectCond, % (EM-ORDEM, TIMING, n=6).

    Recriação da antiga taxa_erro_precisao.png com dados em-ordem corretos.
    """
    lo_g = LO.cond_incorrect / LO.bp_lookups * 100
    bi_g = BI.cond_incorrect / BI.bp_lookups * 100
    lo_dc = LO.directcond_mispredicted / LO.directcond_committed * 100
    bi_dc = BI.directcond_mispredicted / BI.directcond_committed * 100
    fig, ax = plt.subplots(figsize=(7, 4.5))
    _grouped(ax, ["Taxa de erro\nglobal (%)", "Taxa de erro\nDirectCond (%)"],
             [lo_g, lo_dc], [bi_g, bi_dc], fmt="{:.2f}")
    ax.set_ylabel("Percentual (%)")
    ax.set_ylim(0, max(lo_g, lo_dc, bi_g, bi_dc) * 1.3)
    ax.set_title("Taxas de erro de predição (pipeline em-ordem, TIMING, n=6)")
    _save(fig, "taxa_erro_precisao.png")


def fig_tempo_ipc():
    """simTicks e IPC reais (EM-ORDEM, TIMING, n=6). Recriação da antiga
    tempo_ipc_o3.png, agora mostrando que ambos são IDÊNTICOS em-ordem —
    o modelo TIMING não modela o efeito do preditor no tempo/IPC.
    """
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 5.2))
    fig.suptitle("LocalBP vs. BiModeBP — pipeline em-ordem (TIMING, n=6)\n"
                 "simTicks e IPC não variam com o preditor neste modelo",
                 fontweight="bold", y=1.06)

    ticks = [LO.sim_ticks / 1e6, BI.sim_ticks / 1e6]
    b = a1.bar(["LocalBP", "BiModeBP"], ticks, color=[C_LOCAL, C_BIMODE])
    for r, v in zip(b, ticks):
        a1.annotate(f"{v:.2f}M", (r.get_x() + r.get_width() / 2, v), ha="center", va="bottom")
    a1.set_title("Tempo total de simulação\nvariação: 0% (idêntico)")
    a1.set_ylabel("simTicks (milhões)")
    a1.set_ylim(0, max(ticks) * 1.2)

    ipc = [LO.ipc, BI.ipc]
    b = a2.bar(["LocalBP", "BiModeBP"], ipc, color=[C_LOCAL, C_BIMODE])
    for r, v in zip(b, ipc):
        a2.annotate(f"{v:.3f}", (r.get_x() + r.get_width() / 2, v), ha="center", va="bottom")
    a2.set_title("IPC (simInsts / numCycles)\nvariação: 0% (idêntico)")
    a2.set_ylabel("IPC")
    a2.set_ylim(0, max(ipc) * 1.2)
    fig.tight_layout()
    _save(fig, "tempo_ipc_inorder.png")


def fig_escala():
    """Efeito de escala (EM-ORDEM, TIMING): n=6 vs. n=100.000.

    Mostra que o padrão se mantém em escala maior — mesmas contagens de
    desvios avaliados entre preditores, mas o BiModeBP reduz erros em
    proporção parecida (ou maior) que em n=6. O simTicks permanece idêntico
    entre preditores em ambas as escalas (modelo em-ordem).
    """
    labels = ["n=6", "n=100.000"]
    lo_rate = [LO.cond_incorrect / LO.bp_lookups * 100,
               LO_100K.cond_incorrect / LO_100K.bp_lookups * 100]
    bi_rate = [BI.cond_incorrect / BI.bp_lookups * 100,
               BI_100K.cond_incorrect / BI_100K.bp_lookups * 100]

    fig, ax = plt.subplots(figsize=(7, 4.8))
    _grouped(ax, labels, lo_rate, bi_rate, fmt="{:.2f}%")
    ax.set_ylabel("Taxa de erro global (%)")
    ax.set_ylim(0, max(lo_rate + bi_rate) * 1.45)
    ax.set_title("Efeito de escala (pipeline em-ordem, TIMING)\nBiModeBP reduz a taxa de erro em ambas as escalas")
    ax.legend(loc="upper center")

    x = np.arange(len(labels))
    for i in range(len(labels)):
        var = (bi_rate[i] - lo_rate[i]) / lo_rate[i] * 100
        ax.annotate(f"({var:+.1f}%)", (x[i], max(lo_rate[i], bi_rate[i])),
                    xytext=(0, 22), textcoords="offset points",
                    ha="center", va="bottom", fontweight="bold", color=C_BIMODE, fontsize=10)
    _save(fig, "efeito_escala.png")


def main():
    print(f"Gerando figuras em {os.path.relpath(FIG_DIR, ROOT)}/")
    fig_inorder()
    fig_volume()
    fig_incorretas()
    fig_taxas()
    fig_tempo_ipc()
    fig_escala()
    print("Concluído.")


if __name__ == "__main__":
    main()
