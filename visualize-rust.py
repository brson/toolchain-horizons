#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Visualize Rust crate toolchain compatibility on a timeline.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import numpy as np
import json
import sys
import chart_style as cs

# Check if we should show the plot window
show_plot = '--show' in sys.argv

# Font scale factor: 2x for windowed display, 1x for PNG export
fs = 2.0 if show_plot else 1.0

# Load results
with open('rust/results.json', 'r') as f:
    results = json.load(f)

# Rust version release dates (mapping version to date and index).
# Dates are approximate based on 6-week release cycle, with known anchor points.
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
    '1.90.0': ('2024-12-01', 90),
}

# Baseline: Edition 2018 stabilized in Rust 1.31.
baseline_version = '1.31.1'
baseline_date = datetime.strptime(rust_versions[baseline_version][0], '%Y-%m-%d')
latest_date = datetime(2026, 1, 1)

# Process data.
crates_data = []
for crate in results:
    if crate['crate_name'] == 'CONTROL':
        continue

    oldest = crate['oldest_compatible']
    if oldest is None:
        # Crate doesn't work with any tested version.
        continue

    crate_date = datetime.strptime(rust_versions[oldest][0], '%Y-%m-%d')
    versions_lost = rust_versions[oldest][1] - rust_versions[baseline_version][1]

    # Categorize impact.
    if versions_lost <= 15:
        impact = 'minimal'
    elif versions_lost <= 30:
        impact = 'low'
    elif versions_lost <= 40:
        impact = 'moderate'
    elif versions_lost <= 50:
        impact = 'high'
    else:
        impact = 'severe'

    crates_data.append((
        crate['crate_name'],
        oldest,
        rust_versions[oldest][0],
        versions_lost,
        impact
    ))

# Sort by versions lost.
crates_data.sort(key=lambda x: x[3])

# Calculate total versions in baseline range.
baseline_total = rust_versions['1.90.0'][1] - rust_versions[baseline_version][1]

# Color scheme based on impact
color_map = cs.COLOR_MAP

# Create figure
fig, ax1 = plt.subplots(figsize=cs.FIGURE_SIZE)
fig.suptitle('Rust Toolchain Horizons - Edition 2018', fontsize=int(cs.FONT_TITLE*fs), fontweight='bold')

# Timeline bars
y_pos = 0
for crate_name, rust_version, date_str, versions_lost, impact in crates_data:
    crate_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Calculate bar position and width
    bar_start = (crate_date - baseline_date).days
    bar_width = (latest_date - crate_date).days

    color = color_map[impact]

    # Draw bar from crate's min version to latest
    ax1.barh(y_pos, bar_width, left=bar_start, height=cs.BAR_HEIGHT,
             color=color, alpha=cs.BAR_ALPHA, edgecolor=cs.BAR_EDGE_COLOR, linewidth=cs.BAR_EDGE_WIDTH)

    # Add crate name
    ax1.text(cs.LABEL_OFFSET_X, y_pos, crate_name, ha='right', va='center', fontsize=int(cs.FONT_PKG_NAME*fs), fontweight='bold')

    # Add version and date on the bar
    text_x = bar_start + cs.VERSION_OFFSET_X
    ax1.text(text_x, y_pos, f'{rust_version}',
             ha='left', va='center', fontsize=int(cs.FONT_VERSION_LABEL*fs), color='black')

    y_pos += 1

# Timeline from baseline to now
total_days = (latest_date - baseline_date).days
ax1.set_xlim(0, total_days)
ax1.set_ylim(-0.5, len(crates_data) - 0.5)
ax1.set_xlabel('')
ax1.set_yticks([])

# Add year markers
year_markers = []
for year in range(2019, 2026):
    year_date = datetime(year, 1, 1)
    if year_date >= baseline_date and year_date <= latest_date:
        days_from_start = (year_date - baseline_date).days
        ax1.axvline(days_from_start, color='gray', linestyle='--', alpha=cs.GRID_ALPHA, linewidth=cs.MARKER_LINEWIDTH)
        year_markers.append((days_from_start, str(year)))

# Set x-axis labels to years
ax1.set_xticks([pos for pos, _ in year_markers])
ax1.set_xticklabels([label for _, label in year_markers], fontsize=int(cs.FONT_XTICK*fs))

# Add grid
ax1.grid(axis='x', alpha=cs.GRID_ALPHA)

# Add baseline indicator
baseline_line = ax1.axvline(0, color='green', linestyle='-', linewidth=cs.BASELINE_LINEWIDTH, alpha=cs.BASELINE_ALPHA)

# Create legend for impact levels
legend_elements = [
    mpatches.Patch(color=color_map["minimal"], label='Minimal (<=15 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["low"], label='Low (16-30 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["moderate"], label='Moderate (31-40 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["high"], label='High (41-50 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["severe"], label='Severe (>50 versions lost)', alpha=cs.BAR_ALPHA),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=int(cs.FONT_LEGEND*fs),
           title='Impact Severity', title_fontsize=int(cs.FONT_LEGEND_TITLE*fs))

plt.tight_layout()
plt.savefig('compatibility-timeline-rust.png', dpi=cs.DPI, bbox_inches='tight')
print("Visualization saved to compatibility-timeline-rust.png")

# Create a second visualization: Lost versions chart
fig2, ax = plt.subplots(figsize=cs.FIGURE_SIZE_SECONDARY)

# Use the already sorted crates_data (CONTROL was already filtered out).
crate_names = [d[0] for d in crates_data]
versions_lost = [d[3] for d in crates_data]
impacts = [d[4] for d in crates_data]
colors_sorted = [color_map[imp] for imp in impacts]

# Create horizontal bar chart
bars = ax.barh(range(len(crate_names)), versions_lost, color=colors_sorted,
               alpha=cs.BAR_ALPHA, edgecolor=cs.BAR_EDGE_COLOR, linewidth=cs.BAR_EDGE_WIDTH)

ax.set_yticks(range(len(crate_names)))
ax.set_yticklabels(crate_names, fontsize=int(cs.FONT_PKG_NAME*fs))
ax.set_xlabel('Number of Rust Versions Lost', fontsize=int(cs.FONT_AXIS_LABEL*fs))
ax.set_title(f'Toolchain Compatibility Loss by Crate\n(Compared to no-dependency baseline of {baseline_total} versions)',
             fontsize=int(13*fs), fontweight='bold')
ax.grid(axis='x', alpha=cs.GRID_ALPHA)

# Add percentage labels
for i, (bar, lost) in enumerate(zip(bars, versions_lost)):
    percentage = (lost / baseline_total) * 100
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{int(lost)} ({percentage:.0f}%)',
            ha='left', va='center', fontsize=int(cs.FONT_LEGEND*fs))

# Add baseline reference line
ax.axvline(0, color='green', linestyle='-', linewidth=cs.BASELINE_LINEWIDTH, alpha=0.5, label='Baseline (no deps)')

plt.tight_layout()
plt.savefig('versions-lost-rust.png', dpi=cs.DPI, bbox_inches='tight')
print("Visualization saved to versions-lost-rust.png")

# Only show plot window if --show argument is passed
if show_plot:
    plt.show()
