#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
# ]
# ///
"""
Visualize Rust crate compatibility impact distribution.
"""

import matplotlib.pyplot as plt
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

# Rust version indices for calculating versions lost.
rust_versions = {
    '1.16.0': 16,
    '1.31.1': 31, '1.32.0': 32, '1.33.0': 33, '1.34.2': 34, '1.35.0': 35,
    '1.36.0': 36, '1.37.0': 37, '1.38.0': 38, '1.39.0': 39, '1.40.0': 40,
    '1.41.1': 41, '1.42.0': 42, '1.43.1': 43, '1.44.1': 44, '1.45.2': 45,
    '1.46.0': 46, '1.47.0': 47, '1.48.0': 48, '1.49.0': 49, '1.50.0': 50,
    '1.51.0': 51, '1.52.1': 52, '1.53.0': 53, '1.54.0': 54, '1.55.0': 55,
    '1.56.1': 56, '1.57.0': 57, '1.58.1': 58, '1.59.0': 59, '1.60.0': 60,
    '1.61.0': 61, '1.62.1': 62, '1.63.0': 63, '1.64.0': 64, '1.65.0': 65,
    '1.66.1': 66, '1.67.1': 67, '1.68.2': 68, '1.69.0': 69, '1.70.0': 70,
    '1.71.1': 71, '1.72.1': 72, '1.73.0': 73, '1.74.1': 74, '1.75.0': 75,
    '1.76.0': 76, '1.77.2': 77, '1.78.0': 78, '1.79.0': 79, '1.80.1': 80,
    '1.81.0': 81, '1.82.0': 82, '1.83.0': 83, '1.84.1': 84, '1.85.1': 85,
    '1.86.0': 86, '1.87.0': 87, '1.88.0': 88, '1.89.0': 89, '1.90.0': 90,
}

baseline_version = '1.31.1'

# Process data and categorize impact.
impact_counts = {}
for crate in results:
    if crate['crate_name'] == 'CONTROL':
        continue

    oldest = crate['oldest_compatible']
    if oldest is None:
        continue

    versions_lost = rust_versions.get(oldest, 0) - rust_versions[baseline_version]

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

    impact_counts[impact] = impact_counts.get(impact, 0) + 1

# Create distribution chart.
color_map = cs.COLOR_MAP
impact_order = ["minimal", "low", "moderate", "high", "severe"]
counts = [impact_counts.get(imp, 0) for imp in impact_order]
colors = [color_map[imp] for imp in impact_order]

fig, ax = plt.subplots(figsize=cs.FIGURE_SIZE_DIST)
bars = ax.bar(impact_order, counts, color=colors, alpha=cs.BAR_ALPHA, edgecolor=cs.BAR_EDGE_COLOR)
ax.set_ylabel('Number of Crates', fontsize=int(cs.FONT_SUBTITLE*fs))
ax.set_xlabel('Impact Level', fontsize=int(cs.FONT_SUBTITLE*fs))
ax.set_title('Rust Compatibility Impact Distribution', fontsize=int(cs.FONT_TITLE*fs), fontweight='bold')
ax.grid(axis='y', alpha=cs.GRID_ALPHA)

# Add count labels on bars.
for bar, count in zip(bars, counts):
    if count > 0:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontsize=int(cs.FONT_COUNT_LABEL*fs), fontweight='bold')

plt.tight_layout()
plt.savefig('impact-distribution-rust.png', dpi=cs.DPI, bbox_inches='tight')
print("Saved: impact-distribution-rust.png")

if show_plot:
    plt.show()
