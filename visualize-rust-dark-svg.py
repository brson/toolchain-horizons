#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Generate the Rust toolchain compatibility chart in dark-mode SVG,
for embedding in the blog post.
"""

import matplotlib
matplotlib.rcParams['svg.fonttype'] = 'none'
import matplotlib.pyplot as plt
from datetime import datetime
import json
import sys

# Rust version release dates.
rust_versions = {
    '1.0.0': ('2015-05-15', 0),
    '1.1.0': ('2015-06-26', 1),
    '1.2.0': ('2015-08-07', 2),
    '1.3.0': ('2015-09-18', 3),
    '1.4.0': ('2015-10-30', 4),
    '1.5.0': ('2015-12-11', 5),
    '1.6.0': ('2016-01-22', 6),
    '1.7.0': ('2016-03-04', 7),
    '1.8.0': ('2016-04-15', 8),
    '1.9.0': ('2016-05-27', 9),
    '1.10.0': ('2016-07-08', 10),
    '1.11.0': ('2016-08-19', 11),
    '1.12.1': ('2016-09-30', 12),
    '1.13.0': ('2016-11-11', 13),
    '1.14.0': ('2016-12-23', 14),
    '1.15.1': ('2017-02-03', 15),
    '1.16.0': ('2017-03-16', 16),
    '1.17.0': ('2017-04-28', 17),
    '1.18.0': ('2017-06-09', 18),
    '1.19.0': ('2017-07-21', 19),
    '1.20.0': ('2017-09-01', 20),
    '1.21.0': ('2017-10-13', 21),
    '1.22.1': ('2017-11-24', 22),
    '1.23.0': ('2018-01-05', 23),
    '1.24.1': ('2018-02-16', 24),
    '1.25.0': ('2018-03-30', 25),
    '1.26.2': ('2018-05-11', 26),
    '1.27.2': ('2018-06-22', 27),
    '1.28.0': ('2018-08-03', 28),
    '1.29.2': ('2018-09-14', 29),
    '1.30.1': ('2018-10-26', 30),
    '1.31.1': ('2018-12-20', 31),
    '1.32.0': ('2019-01-18', 32),
    '1.33.0': ('2019-03-01', 33),
    '1.34.2': ('2019-04-12', 34),
    '1.35.0': ('2019-05-24', 35),
    '1.36.0': ('2019-07-05', 36),
    '1.37.0': ('2019-08-16', 37),
    '1.38.0': ('2019-09-27', 38),
    '1.39.0': ('2019-11-08', 39),
    '1.40.0': ('2019-12-20', 40),
    '1.41.1': ('2020-01-31', 41),
    '1.42.0': ('2020-03-13', 42),
    '1.43.1': ('2020-04-24', 43),
    '1.44.1': ('2020-06-05', 44),
    '1.45.2': ('2020-07-17', 45),
    '1.46.0': ('2020-08-28', 46),
    '1.47.0': ('2020-10-09', 47),
    '1.48.0': ('2020-11-20', 48),
    '1.49.0': ('2021-01-01', 49),
    '1.50.0': ('2021-02-12', 50),
    '1.51.0': ('2021-03-26', 51),
    '1.52.1': ('2021-05-07', 52),
    '1.53.0': ('2021-06-18', 53),
    '1.54.0': ('2021-07-30', 54),
    '1.55.0': ('2021-09-10', 55),
    '1.56.1': ('2021-11-01', 56),
    '1.57.0': ('2021-12-03', 57),
    '1.58.1': ('2022-01-14', 58),
    '1.59.0': ('2022-02-25', 59),
    '1.60.0': ('2022-04-08', 60),
    '1.61.0': ('2022-05-20', 61),
    '1.62.1': ('2022-07-01', 62),
    '1.63.0': ('2022-08-12', 63),
    '1.64.0': ('2022-09-23', 64),
    '1.65.0': ('2022-11-04', 65),
    '1.66.1': ('2022-12-16', 66),
    '1.67.1': ('2023-01-27', 67),
    '1.68.2': ('2023-03-10', 68),
    '1.69.0': ('2023-04-21', 69),
    '1.70.0': ('2023-06-02', 70),
    '1.71.1': ('2023-07-14', 71),
    '1.72.1': ('2023-08-25', 72),
    '1.73.0': ('2023-10-06', 73),
    '1.74.1': ('2023-11-17', 74),
    '1.75.0': ('2023-12-29', 75),
    '1.76.0': ('2024-02-09', 76),
    '1.77.2': ('2024-03-22', 77),
    '1.78.0': ('2024-05-03', 78),
    '1.79.0': ('2024-06-14', 79),
    '1.80.1': ('2024-07-26', 80),
    '1.81.0': ('2024-09-06', 81),
    '1.82.0': ('2024-10-17', 82),
    '1.83.0': ('2024-11-29', 83),
    '1.84.1': ('2025-01-10', 84),
    '1.85.1': ('2025-02-21', 85),
    '1.86.0': ('2025-04-04', 86),
    '1.87.0': ('2025-05-16', 87),
    '1.88.0': ('2025-06-27', 88),
    '1.89.0': ('2025-08-08', 89),
    '1.90.0': ('2025-09-18', 90),
    '1.91.1': ('2025-11-10', 91),
    '1.92.0': ('2025-12-11', 92),
    '1.93.1': ('2026-02-12', 93),
    '1.94.1': ('2026-03-26', 94),
}

# Colors tuned for black background.
COLOR_MAP = {
    "minimal":  "#81C784",  # green
    "low":      "#FFEE58",  # yellow
    "moderate": "#FFB74D",  # orange
    "severe":   "#EF5350",  # red
}

BG = "#000000"
FG = "#FFFFFF"
GRID = "#555555"

baseline_version = '1.0.0'
baseline_date = datetime.strptime(rust_versions[baseline_version][0], '%Y-%m-%d')
latest_date = datetime(2026, 7, 1)
chart_start_date = datetime(2016, 1, 1)

with open('rust/results.json', 'r') as f:
    results = json.load(f)

crates_data = []
for crate in results:
    if crate['crate_name'] == 'CONTROL':
        continue
    oldest = crate['oldest_compatible']
    if oldest is None:
        continue
    version_index = rust_versions[oldest][1]
    if version_index < 31:
        impact = 'minimal'
    elif version_index < 46:
        impact = 'low'
    elif version_index < 68:
        impact = 'moderate'
    else:
        impact = 'severe'
    crates_data.append((
        crate['crate_name'],
        oldest,
        rust_versions[oldest][0],
        rust_versions[oldest][1] - rust_versions[baseline_version][1],
        impact,
    ))

crates_data.sort(key=lambda x: x[3])

# Figure
fig, ax = plt.subplots(figsize=(14, 32))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)


BAR_HEIGHT = 0.8
LABEL_OFFSET_X = -50
VERSION_OFFSET_X = 30

y_pos = 0
for crate_name, rust_version, date_str, versions_lost, impact in crates_data:
    crate_date = datetime.strptime(date_str, "%Y-%m-%d")
    bar_start = (crate_date - chart_start_date).days
    bar_width = (latest_date - crate_date).days

    color = COLOR_MAP[impact]

    ax.barh(y_pos, bar_width, left=bar_start, height=BAR_HEIGHT,
            color=color, alpha=0.85, edgecolor=BG, linewidth=0.5)

    ax.text(LABEL_OFFSET_X, y_pos, crate_name,
            ha='right', va='center', fontsize=13, fontweight='bold', color=FG)

    ax.text(bar_start + VERSION_OFFSET_X, y_pos, f'{rust_version}',
            ha='left', va='center', fontsize=10, color='black')

    y_pos += 1

total_days = (latest_date - chart_start_date).days
ax.set_xlim(0, total_days)
ax.set_ylim(len(crates_data) - 0.5, -0.5)
ax.set_yticks([])

year_markers = []
for year in range(2016, 2027):
    year_date = datetime(year, 1, 1)
    if chart_start_date <= year_date <= latest_date:
        days_from_start = (year_date - chart_start_date).days
        ax.axvline(days_from_start, color=GRID, linestyle='--',
                   alpha=0.6, linewidth=1)
        year_markers.append((days_from_start, str(year)))

ax.set_xticks([pos for pos, _ in year_markers])
ax.set_xticklabels([label for _, label in year_markers], fontsize=22, color=FG)

ax_top = ax.twiny()
ax_top.set_xlim(ax.get_xlim())
ax_top.set_xticks([pos for pos, _ in year_markers])
ax_top.set_xticklabels([label for _, label in year_markers], fontsize=22, color=FG)
ax_top.set_facecolor(BG)

for s in ax.spines.values():
    s.set_color(FG)
for s in ax_top.spines.values():
    s.set_color(FG)

ax.tick_params(colors=FG, which='both')
ax_top.tick_params(colors=FG, which='both')

ax.grid(axis='x', color=GRID, alpha=0.4)

ax.set_title('Rust Toolchain Horizons — April 2026',
             fontsize=28, fontweight='bold', color=FG, pad=70)

plt.tight_layout()

out = sys.argv[1] if len(sys.argv) > 1 else 'compatibility-timeline-rust-dark.svg'
plt.savefig(out, facecolor=BG, bbox_inches='tight')

# Inline fragment-only <use> elements (tick markers) so the blog's
# file-checker doesn't treat them as broken in-document links.
import re
with open(out) as f:
    svg = f.read()

defs = dict(re.findall(r'<path id="([^"]+)"\s+d="([^"]+)"', svg))

def repl_use(m):
    attrs = m.group(1)
    id_match = re.search(r'xlink:href="#([^"]+)"', attrs)
    if not id_match or id_match.group(1) not in defs:
        return m.group(0)
    href_id = id_match.group(1)
    x = re.search(r'\bx="([^"]+)"', attrs)
    y = re.search(r'\by="([^"]+)"', attrs)
    style = re.search(r'style="([^"]*)"', attrs)
    tx = x.group(1) if x else '0'
    ty = y.group(1) if y else '0'
    style_attr = f' style="{style.group(1)}"' if style else ''
    return f'<path d="{defs[href_id]}" transform="translate({tx} {ty})"{style_attr}/>'

svg = re.sub(r'<use([^/>]*)/>', repl_use, svg)

with open(out, 'w') as f:
    f.write(svg)

print(f"Saved {out}")
