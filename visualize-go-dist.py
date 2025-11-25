#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
# ]
# ///
"""
Visualize Go package compatibility impact distribution.
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
with open('go/results.json', 'r') as f:
    results = json.load(f)

# Go version indices for calculating versions lost.
go_versions = {
    '1.13': 0, '1.14': 1, '1.15': 2, '1.16': 3, '1.17': 4,
    '1.18': 5, '1.19': 6, '1.20': 7, '1.21': 8, '1.21.0': 8,
    '1.22': 9, '1.22.0': 9, '1.23': 10, '1.23.0': 10,
    '1.24': 11, '1.24.0': 11,
}

baseline_version = '1.13'

# Process data and categorize impact.
impact_counts = {}
for package in results:
    if package.get('package_name') == 'CONTROL':
        continue

    oldest = package.get('oldest_compatible')
    if oldest is None:
        continue

    versions_lost = go_versions.get(oldest, 0) - go_versions[baseline_version]

    if versions_lost <= 2:
        impact = 'minimal'
    elif versions_lost <= 4:
        impact = 'low'
    elif versions_lost <= 6:
        impact = 'moderate'
    elif versions_lost <= 8:
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
ax.set_ylabel('Number of Packages', fontsize=int(cs.FONT_SUBTITLE*fs))
ax.set_xlabel('Impact Level', fontsize=int(cs.FONT_SUBTITLE*fs))
ax.set_title('Go Compatibility Impact Distribution', fontsize=int(cs.FONT_TITLE*fs), fontweight='bold')
ax.grid(axis='y', alpha=cs.GRID_ALPHA)

# Add count labels on bars.
for bar, count in zip(bars, counts):
    if count > 0:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontsize=int(cs.FONT_COUNT_LABEL*fs), fontweight='bold')

plt.tight_layout()
plt.savefig('impact-distribution-go.png', dpi=cs.DPI, bbox_inches='tight')
print("Saved: impact-distribution-go.png")

if show_plot:
    plt.show()
