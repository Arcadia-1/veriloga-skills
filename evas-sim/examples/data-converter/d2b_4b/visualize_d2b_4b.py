"""Visualize d2b_4b: simulate all 16 trim codes, read CSV results, plot bit-grids.

For each trim_code in 0..15:
  - Generates a temporary testbench with that trim_code
  - Runs evas_simulate
  - Reads the last row of tran.csv (steady-state values)

Then plots 6 heatmaps (binary, one-hot, thermometer × active-high / active-low)
where rows = trim_code and columns = bit index.
"""
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

from evas.netlist.runner import evas_simulate

HERE   = Path(__file__).parent
OUT    = HERE.parent.parent / 'output' / 'd2b_4b'
OUT.mkdir(parents=True, exist_ok=True)

# ── Testbench template (trim_code injected at runtime) ───────────────────────
TB_TEMPLATE = """\
simulator lang=spectre
global 0

ahdl_include "d2b_4b.va"

XDUT (bin_o_3 bin_o_2 bin_o_1 bin_o_0 \\
      bin_n_o_3 bin_n_o_2 bin_n_o_1 bin_n_o_0 \\
      onehot_o_15 onehot_o_14 onehot_o_13 onehot_o_12 onehot_o_11 onehot_o_10 \\
      onehot_o_9 onehot_o_8 onehot_o_7 onehot_o_6 onehot_o_5 onehot_o_4 \\
      onehot_o_3 onehot_o_2 onehot_o_1 onehot_o_0 \\
      onehot_n_o_15 onehot_n_o_14 onehot_n_o_13 onehot_n_o_12 onehot_n_o_11 onehot_n_o_10 \\
      onehot_n_o_9 onehot_n_o_8 onehot_n_o_7 onehot_n_o_6 onehot_n_o_5 onehot_n_o_4 \\
      onehot_n_o_3 onehot_n_o_2 onehot_n_o_1 onehot_n_o_0 \\
      therm_o_14 therm_o_13 therm_o_12 therm_o_11 therm_o_10 \\
      therm_o_9 therm_o_8 therm_o_7 therm_o_6 therm_o_5 \\
      therm_o_4 therm_o_3 therm_o_2 therm_o_1 therm_o_0 \\
      therm_n_o_14 therm_n_o_13 therm_n_o_12 therm_n_o_11 therm_n_o_10 \\
      therm_n_o_9 therm_n_o_8 therm_n_o_7 therm_n_o_6 therm_n_o_5 \\
      therm_n_o_4 therm_n_o_3 therm_n_o_2 therm_n_o_1 therm_n_o_0) \\
      d2b_4b trim_code={trim_code} vdd=0.9

tran tran stop=10n maxstep=0.1n
save bin_o_3:d bin_o_2:d bin_o_1:d bin_o_0:d \\
     bin_n_o_3:d bin_n_o_2:d bin_n_o_1:d bin_n_o_0:d \\
     onehot_o_15:d onehot_o_14:d onehot_o_13:d onehot_o_12:d onehot_o_11:d onehot_o_10:d \\
     onehot_o_9:d onehot_o_8:d onehot_o_7:d onehot_o_6:d onehot_o_5:d onehot_o_4:d \\
     onehot_o_3:d onehot_o_2:d onehot_o_1:d onehot_o_0:d \\
     onehot_n_o_15:d onehot_n_o_14:d onehot_n_o_13:d onehot_n_o_12:d onehot_n_o_11:d onehot_n_o_10:d \\
     onehot_n_o_9:d onehot_n_o_8:d onehot_n_o_7:d onehot_n_o_6:d onehot_n_o_5:d onehot_n_o_4:d \\
     onehot_n_o_3:d onehot_n_o_2:d onehot_n_o_1:d onehot_n_o_0:d \\
     therm_o_14:d therm_o_13:d therm_o_12:d therm_o_11:d therm_o_10:d \\
     therm_o_9:d therm_o_8:d therm_o_7:d therm_o_6:d therm_o_5:d \\
     therm_o_4:d therm_o_3:d therm_o_2:d therm_o_1:d therm_o_0:d \\
     therm_n_o_14:d therm_n_o_13:d therm_n_o_12:d therm_n_o_11:d therm_n_o_10:d \\
     therm_n_o_9:d therm_n_o_8:d therm_n_o_7:d therm_n_o_6:d therm_n_o_5:d \\
     therm_n_o_4:d therm_n_o_3:d therm_n_o_2:d therm_n_o_1:d therm_n_o_0:d
"""

# ── Run 16 simulations and collect last-row values ───────────────────────────
CODES = list(range(16))
rows = {}   # trim_code -> dict of {col: bit_value}

for code in CODES:
    sim_out = OUT / f'code_{code}'
    sim_out.mkdir(parents=True, exist_ok=True)

    # Write SCS next to VA file so bare ahdl_include resolves correctly; delete after
    tb_content = TB_TEMPLATE.format(trim_code=code)
    tb_path = HERE / f'_tb_d2b_4b_code{code}.scs'
    tb_path.write_text(tb_content, encoding='utf-8')

    print(f"[code={code:2d}] simulating ...", end=' ', flush=True)
    try:
        ok = evas_simulate(str(tb_path), output_dir=str(sim_out),
                           log_path=str(sim_out / 'sim.log'))
    finally:
        tb_path.unlink(missing_ok=True)
    if not ok:
        print("FAILED")
        continue

    df   = np.genfromtxt(sim_out / 'tran.csv', delimiter=',', names=True, dtype=None, encoding='utf-8')
    last = df[-1]
    rows[code] = last
    print(f"done  ({len(df)} rows)")

# ── Build matrices from simulation data ──────────────────────────────────────
VDD    = 0.9
THRESH = VDD * 0.5

def bit(row, col):
    try:
        v = row[col]
    except (ValueError, KeyError):
        v = 0.0
    return 1 if float(v) > THRESH else 0

bin_mat      = np.array([[bit(rows[n], f'bin_o_{i}')      for i in range(4)]  for n in CODES])
bin_n_mat    = np.array([[bit(rows[n], f'bin_n_o_{i}')    for i in range(4)]  for n in CODES])
onehot_mat   = np.array([[bit(rows[n], f'onehot_o_{i}')   for i in range(16)] for n in CODES])
onehot_n_mat = np.array([[bit(rows[n], f'onehot_n_o_{i}') for i in range(16)] for n in CODES])
therm_mat    = np.array([[bit(rows[n], f'therm_o_{i}')    for i in range(15)] for n in CODES])
therm_n_mat  = np.array([[bit(rows[n], f'therm_n_o_{i}')  for i in range(15)] for n in CODES])

# ── Color maps ───────────────────────────────────────────────────────────────
CMAP_AH = ListedColormap(['#f0f4ff', '#2563eb'])   # active-high: white / blue
CMAP_AL = ListedColormap(['#fff7ed', '#ea580c'])   # active-low:  white / orange

# ── Plot ─────────────────────────────────────────────────────────────────────

def draw_grid(ax, data, title, cmap, bit_labels, ylabel=True):
    n_rows, n_cols = data.shape
    ax.imshow(data, aspect='auto', cmap=cmap, vmin=0, vmax=1,
              interpolation='nearest')
    ax.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n_rows, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1.0)
    ax.tick_params(which='minor', length=0)
    for r in range(n_rows):
        for c in range(n_cols):
            v = data[r, c]
            ax.text(c, r, str(v), ha='center', va='center',
                    fontsize=6.5, color='white' if v else '#555555',
                    fontweight='bold')
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(bit_labels, fontsize=7)
    ax.set_yticks(range(n_rows))
    if ylabel:
        ax.set_yticklabels([f'{n:2d}  (0x{n:X})' for n in CODES], fontsize=7)
    else:
        ax.set_yticklabels([])
    ax.set_title(title, fontsize=9, pad=4)
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()


fig, axes = plt.subplots(2, 3, figsize=(20, 10),
                         gridspec_kw={'hspace': 0.45, 'wspace': 0.08})
fig.suptitle('d2b_4b — all 16 trim codes, from simulation results', fontsize=13)
fig.text(0.01, 0.5, 'trim_code  (decimal / hex)',
         va='center', rotation='vertical', fontsize=9)

# Row 0: active-high
draw_grid(axes[0, 0], bin_mat,    'bin_o[3:0]  — binary, active-high',        CMAP_AH, [f'b{k}' for k in range(4)])
draw_grid(axes[0, 1], onehot_mat, 'onehot_o[15:0]  — one-hot, active-high',   CMAP_AH, [f'{k}' for k in range(16)],  ylabel=False)
draw_grid(axes[0, 2], therm_mat,  'therm_o[14:0]  — thermometer, active-high', CMAP_AH, [f'{k}' for k in range(15)], ylabel=False)

# Row 1: active-low
draw_grid(axes[1, 0], bin_n_mat,    'bin_n_o[3:0]  — binary, active-low',        CMAP_AL, [f'b{k}' for k in range(4)])
draw_grid(axes[1, 1], onehot_n_mat, 'onehot_n_o[15:0]  — one-cold, active-low',  CMAP_AL, [f'{k}' for k in range(16)],  ylabel=False)
draw_grid(axes[1, 2], therm_n_mat,  'therm_n_o[14:0]  — thermometer, active-low', CMAP_AL, [f'{k}' for k in range(15)], ylabel=False)

leg = [
    mpatches.Patch(color='#2563eb', label='1 (active-high)'),
    mpatches.Patch(color='#ea580c', label='1 (active-low)'),
    mpatches.Patch(color='#f0f4ff', label='0'),
]
fig.legend(handles=leg, loc='lower center', ncol=3, fontsize=9,
           bbox_to_anchor=(0.5, 0.005))

out_png = OUT / 'visualize_d2b_4b.png'
fig.savefig(str(out_png), dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"\nSaved: {out_png}")
