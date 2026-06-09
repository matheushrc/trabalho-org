"""
Dependëncias:
pip install matplotlib numpy
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── 1. Carregar dados ──────────────────────────────────────────────────────────
DATA_FILE = "search_raw_results.json"

with open(DATA_FILE) as f:
    results = json.load(f)

# ── 2. Filtrar apenas CPU TIMING ───────────────────────────────────────────────
timing_data = [r for r in results if r["config"]["cpu_type"] == "TIMING"]

local_bp  = [r for r in timing_data if r["config"]["branch_predictor"] == "LocalBP"]
bimode_bp = [r for r in timing_data if r["config"]["branch_predictor"] == "BiModeBP"]

# ── 3. Extrair e organizar por frequência de clock ─────────────────────────────
def group_by_clock(entries):
    groups = {}
    for e in entries:
        clk = e["config"]["clk_freq"]
        groups.setdefault(clk, []).append(e["ticks"])
    return groups

local_by_clk  = group_by_clock(local_bp)
bimode_by_clk = group_by_clock(bimode_bp)

# Frequências presentes nos dados TIMING
all_clocks = sorted(
    set(list(local_by_clk.keys()) + list(bimode_by_clk.keys())),
    key=lambda x: int(x.replace("GHz", ""))
)

# ── 4. Calcular métricas por frequência ────────────────────────────────────────
# Total de instruções estimado a partir do melhor resultado de referência
# (baseline TIMING 3GHz = 48.402.756.459 ticks, 86.674.630 instruções → dataset 100k)
# Para o dataset de 6 elementos (usado nas simulações DSE), usamos como proxy:
# cycles = ticks / period, period = 1/freq → cycles = ticks * freq_Hz / 1e9
# IPC ∝ instructions / cycles; como instrução é constante, IPC ∝ 1 / (ticks * freq)

def ticks_to_ns(ticks, clk_freq_str):
    freq_ghz = int(clk_freq_str.replace("GHz", ""))
    period_ns = 1.0 / freq_ghz          # ns por ciclo
    return ticks * period_ns / 1000     # em µs (legível)

def ticks_to_cycles(ticks, clk_freq_str):
    freq_ghz = int(clk_freq_str.replace("GHz", ""))
    freq_hz  = freq_ghz * 1e9
    return ticks / (1e9 / freq_hz)      # ciclos = ticks / period_ticks

# Número fixo de instruções comprometidas do benchmark heap sort 6-elem
# (valor obtido das stats: ~30.971 branches committed × escala típica do benchmark)
# Usamos valor relativo — IPC normalizado pela configuração mais rápida.
# ticks → cycles → IPC = N_instr / cycles
N_INSTR_PROXY = 86_674_630  # instruções comprometidas (dataset 100k como escala)
# Para comparação relativa, o N_INSTR cancela; usamos apenas cycles para IPC relativo.

def compute_stats(groups):
    stats = {}
    for clk, tick_list in groups.items():
        cycles_list = [ticks_to_cycles(t, clk) for t in tick_list]
        stats[clk] = {
            "ticks_mean":  np.mean(tick_list),
            "ticks_min":   np.min(tick_list),
            "ticks_max":   np.max(tick_list),
            "cycles_mean": np.mean(cycles_list),
            "ipc_mean":    N_INSTR_PROXY / np.mean(cycles_list),  # IPC estimado
        }
    return stats

local_stats  = compute_stats(local_by_clk)
bimode_stats = compute_stats(bimode_by_clk)

# ── 5. Preparar dados para os gráficos ────────────────────────────────────────
clocks_present = [c for c in all_clocks
                  if c in local_stats and c in bimode_stats]

x = np.arange(len(clocks_present))
width = 0.35

local_ticks  = [local_stats[c]["ticks_mean"]  / 1e9 for c in clocks_present]
bimode_ticks = [bimode_stats[c]["ticks_mean"] / 1e9 for c in clocks_present]

local_ipc    = [local_stats[c]["ipc_mean"]   for c in clocks_present]
bimode_ipc   = [bimode_stats[c]["ipc_mean"]  for c in clocks_present]

# Porcentagem de melhoria do BiModeBP sobre LocalBP (ticks — menor é melhor)
improvement_ticks = [
    (local_ticks[i] - bimode_ticks[i]) / local_ticks[i] * 100
    for i in range(len(clocks_present))
]

# ── 6. Estilo visual ───────────────────────────────────────────────────────────
COLOR_LOCAL  = "#4C72B0"   # azul
COLOR_BIMODE = "#DD8452"   # laranja
BACKGROUND   = "#F8F9FA"
GRID_COLOR   = "#DEE2E6"

plt.rcParams.update({
    "font.family":     "DejaVu Sans",
    "font.size":       11,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "figure.facecolor":   BACKGROUND,
    "axes.facecolor":     BACKGROUND,
})

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle(
    "Branch Prediction: LocalBP vs. BiModeBP\nCPU Em-Ordem (TIMING) — gem5 RISC-V · Heap Sort",
    fontsize=14, fontweight="bold", y=1.02
)

# ── 6a. Gráfico 1: Tempo total de simulação (ticks × 10⁹) ─────────────────────
ax1 = axes[0]
bars1 = ax1.bar(x - width/2, local_ticks,  width, label="LocalBP",  color=COLOR_LOCAL,  zorder=3)
bars2 = ax1.bar(x + width/2, bimode_ticks, width, label="BiModeBP", color=COLOR_BIMODE, zorder=3)

ax1.set_title("Tempo Total de Simulação", fontsize=12, fontweight="bold", pad=10)
ax1.set_ylabel("Ticks Simulados (×10⁹)", fontsize=10)
ax1.set_xlabel("Frequência de Clock", fontsize=10)
ax1.set_xticks(x)
ax1.set_xticklabels(clocks_present)
ax1.yaxis.grid(True, color=GRID_COLOR, linewidth=0.8, zorder=0)
ax1.set_axisbelow(True)
ax1.legend(framealpha=0.6)

# Anotações de melhoria (%)
for i, (b1, b2, imp) in enumerate(zip(bars1, bars2, improvement_ticks)):
    color_ann = "#2D6A4F" if imp > 0 else "#AE2012"
    symbol    = "▼" if imp > 0 else "▲"
    ax1.annotate(
        f"{symbol}{abs(imp):.1f}%",
        xy=(x[i], max(b1.get_height(), b2.get_height()) + 0.3),
        ha="center", va="bottom", fontsize=9,
        color=color_ann, fontweight="bold"
    )

# Valores no topo das barras
for bar in list(bars1) + list(bars2):
    h = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, h + 0.1,
             f"{h:.1f}", ha="center", va="bottom", fontsize=8, color="#555")

# ── 6b. Gráfico 2: IPC estimado ────────────────────────────────────────────────
ax2 = axes[1]
bars3 = ax2.bar(x - width/2, local_ipc,  width, label="LocalBP",  color=COLOR_LOCAL,  zorder=3)
bars4 = ax2.bar(x + width/2, bimode_ipc, width, label="BiModeBP", color=COLOR_BIMODE, zorder=3)

ax2.set_title("IPC Estimado\n(Instruções por Ciclo)", fontsize=12, fontweight="bold", pad=10)
ax2.set_ylabel("IPC", fontsize=10)
ax2.set_xlabel("Frequência de Clock", fontsize=10)
ax2.set_xticks(x)
ax2.set_xticklabels(clocks_present)
ax2.yaxis.grid(True, color=GRID_COLOR, linewidth=0.8, zorder=0)
ax2.set_axisbelow(True)
ax2.legend(framealpha=0.6)

improvement_ipc = [
    (bimode_ipc[i] - local_ipc[i]) / local_ipc[i] * 100
    for i in range(len(clocks_present))
]
for i, (b3, b4, imp) in enumerate(zip(bars3, bars4, improvement_ipc)):
    color_ann = "#2D6A4F" if imp > 0 else "#AE2012"
    symbol    = "▲" if imp > 0 else "▼"
    ax2.annotate(
        f"{symbol}{abs(imp):.1f}%",
        xy=(x[i], max(b3.get_height(), b4.get_height()) + 0.005),
        ha="center", va="bottom", fontsize=9,
        color=color_ann, fontweight="bold"
    )

for bar in list(bars3) + list(bars4):
    h = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, h + 0.002,
             f"{h:.3f}", ha="center", va="bottom", fontsize=8, color="#555")

# ── 7. Rodapé com nota metodológica ───────────────────────────────────────────
fig.text(
    0.5, -0.04,
    "IPC estimado com base em N=86.674.630 instruções (dataset 100k) | "
    "Valores médios agrupados por frequência de clock | "
    "▼/▲ = variação do BiModeBP em relação ao LocalBP",
    ha="center", fontsize=8.5, color="#666", style="italic"
)

plt.tight_layout()
output_path = "branch_predictor_comparison.png"
plt.savefig(output_path, dpi=150, bbox_inches="tight")
print(f"✅  Gráfico salvo em: {output_path}")
plt.show()
