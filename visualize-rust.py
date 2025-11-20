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

# Check if we should show the plot window
show_plot = '--show' in sys.argv

# Font scale factor: 2x for windowed display, 1x for PNG export
fs = 2.0 if show_plot else 1.0

# Load results
with open('rust/results.json', 'r') as f:
    results = json.load(f)

# Rust version release dates (mapping version to date and index).
rust_versions = {
    '1.0.0': ('2015-05-15', 0),
    '1.16.0': ('2017-03-16', 16),
    '1.31.1': ('2018-12-20', 31),
    '1.32.0': ('2019-01-17', 32),
    '1.36.0': ('2019-07-04', 36),
    '1.38.0': ('2019-09-26', 38),
    '1.51.0': ('2021-03-25', 51),
    '1.57.0': ('2021-12-02', 57),
    '1.60.0': ('2022-04-07', 60),
    '1.61.0': ('2022-05-19', 61),
    '1.62.1': ('2022-07-19', 62),
    '1.63.0': ('2022-08-11', 63),
    '1.65.0': ('2022-11-03', 65),
    '1.68.2': ('2023-03-28', 68),
    '1.71.1': ('2023-08-03', 71),
    '1.80.1': ('2024-08-08', 80),
    '1.82.0': ('2024-10-17', 82),
    '1.83.0': ('2024-11-28', 83),
    '1.90.0': ('2024-12-01', 90),
}

# Baseline.
baseline_version = '1.16.0'
baseline_date = datetime.strptime(rust_versions[baseline_version][0], '%Y-%m-%d')
latest_date = datetime.strptime(rust_versions['1.90.0'][0], '%Y-%m-%d')

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
    if versions_lost <= 5:
        impact = 'minimal'
    elif versions_lost <= 25:
        impact = 'low'
    elif versions_lost <= 40:
        impact = 'moderate'
    elif versions_lost <= 50:
        impact = 'high'
    elif versions_lost <= 60:
        impact = 'severe'
    else:
        impact = 'extreme'

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
color_map = {
    "baseline": "#2E7D32",  # Green
    "minimal": "#66BB6A",   # Light green
    "low": "#FDD835",       # Yellow
    "moderate": "#FFB74D",  # Orange
    "high": "#FF7043",      # Deep orange
    "severe": "#E53935",    # Red
    "extreme": "#880E4F",   # Deep purple
}

# Create figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle('Rust Crate Toolchain Compatibility Timeline\nEdition 2018', fontsize=int(16*fs), fontweight='bold')

# Plot 1: Timeline bars
y_pos = 0
for crate_name, rust_version, date_str, versions_lost, impact in crates_data:
    crate_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Calculate bar position and width
    bar_start = (crate_date - baseline_date).days
    bar_width = (latest_date - crate_date).days

    color = color_map[impact]

    # Draw bar from crate's min version to latest
    ax1.barh(y_pos, bar_width, left=bar_start, height=0.8,
             color=color, alpha=0.7, edgecolor='black', linewidth=0.5)

    # Add crate name
    ax1.text(-50, y_pos, crate_name, ha='right', va='center', fontsize=int(9*fs), fontweight='bold')

    # Add version and date on the bar
    text_x = bar_start + 30
    ax1.text(text_x, y_pos, f'{rust_version}',
             ha='left', va='center', fontsize=int(7*fs), color='black')

    y_pos += 1

# Timeline from baseline to now
total_days = (latest_date - baseline_date).days
ax1.set_xlim(0, total_days)
ax1.set_ylim(-0.5, len(crates_data) - 0.5)
ax1.set_xlabel('Time', fontsize=int(12*fs))
ax1.set_yticks([])

# Add year markers
year_markers = []
for year in range(2017, 2025):
    year_date = datetime(year, 1, 1)
    if year_date >= baseline_date and year_date <= latest_date:
        days_from_start = (year_date - baseline_date).days
        ax1.axvline(days_from_start, color='gray', linestyle='--', alpha=0.3, linewidth=1)
        year_markers.append((days_from_start, str(year)))

# Set x-axis labels to years
ax1.set_xticks([pos for pos, _ in year_markers])
ax1.set_xticklabels([label for _, label in year_markers])

# Add grid
ax1.grid(axis='x', alpha=0.2)
ax1.set_title('Compatibility Window by Crate\n(Each bar shows the range of supported Rust versions)',
              fontsize=int(11*fs), pad=10)

# Add baseline indicator
baseline_line = ax1.axvline(0, color='green', linestyle='-', linewidth=2, alpha=0.8)

# Plot 2: Impact distribution
impact_counts = {}
for _, _, _, _, impact in crates_data:
    if impact != "baseline":
        impact_counts[impact] = impact_counts.get(impact, 0) + 1

impact_order = ["minimal", "low", "moderate", "high", "severe", "extreme"]
counts = [impact_counts.get(imp, 0) for imp in impact_order]
colors = [color_map[imp] for imp in impact_order]

bars = ax2.bar(impact_order, counts, color=colors, alpha=0.7, edgecolor='black')
ax2.set_ylabel('Number of Crates', fontsize=int(11*fs))
ax2.set_xlabel('Impact Level', fontsize=int(11*fs))
ax2.set_title('Distribution of Compatibility Impact', fontsize=int(11*fs))
ax2.grid(axis='y', alpha=0.2)

# Add count labels on bars
for bar, count in zip(bars, counts):
    if count > 0:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontsize=int(10*fs), fontweight='bold')

# Create legend for impact levels
legend_elements = [
    mpatches.Patch(color=color_map["minimal"], label='Minimal (<=5 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["low"], label='Low (6-25 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["moderate"], label='Moderate (26-40 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["high"], label='High (41-50 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["severe"], label='Severe (51-60 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["extreme"], label='Extreme (>60 versions lost)', alpha=0.7),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=int(8*fs), title='Impact Severity')

plt.tight_layout()
plt.savefig('compatibility-timeline-rust.png', dpi=300, bbox_inches='tight')
print("Visualization saved to compatibility-timeline-rust.png")

# Create a second visualization: Lost versions chart
fig2, ax = plt.subplots(figsize=(12, 8))

# Use the already sorted crates_data (CONTROL was already filtered out).
crate_names = [d[0] for d in crates_data]
versions_lost = [d[3] for d in crates_data]
impacts = [d[4] for d in crates_data]
colors_sorted = [color_map[imp] for imp in impacts]

# Create horizontal bar chart
bars = ax.barh(range(len(crate_names)), versions_lost, color=colors_sorted,
               alpha=0.7, edgecolor='black')

ax.set_yticks(range(len(crate_names)))
ax.set_yticklabels(crate_names, fontsize=int(9*fs))
ax.set_xlabel('Number of Rust Versions Lost', fontsize=int(12*fs))
ax.set_title(f'Toolchain Compatibility Loss by Crate\n(Compared to no-dependency baseline of {baseline_total} versions)',
             fontsize=int(13*fs), fontweight='bold')
ax.grid(axis='x', alpha=0.2)

# Add percentage labels
for i, (bar, lost) in enumerate(zip(bars, versions_lost)):
    percentage = (lost / baseline_total) * 100
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{int(lost)} ({percentage:.0f}%)',
            ha='left', va='center', fontsize=int(8*fs))

# Add baseline reference line
ax.axvline(0, color='green', linestyle='-', linewidth=2, alpha=0.5, label='Baseline (no deps)')

plt.tight_layout()
plt.savefig('versions-lost-rust.png', dpi=300, bbox_inches='tight')
print("Visualization saved to versions-lost-rust.png")

# Only show plot window if --show argument is passed
if show_plot:
    plt.show()
