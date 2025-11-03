#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Visualize Node.js package toolchain compatibility on a timeline.
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
with open('node/results.json', 'r') as f:
    results = json.load(f)

# Node.js version release dates (approximate)
node_versions = {
    'v14.21.3': ('2023-02-21', 0, 'Fermium LTS'),
    'v16.20.2': ('2023-08-09', 1, 'Gallium LTS'),
    'v18.20.8': ('2024-04-10', 2, 'Hydrogen LTS'),
    'v20.19.5': ('2024-12-19', 3, 'Iron LTS'),
    'v22.20.0': ('2024-04-24', 4, 'Jod LTS'),
    'v24.0.2': ('2024-10-29', 5, 'Current'),
}

# Baseline
baseline_version = 'v14.21.3'
baseline_date = datetime.strptime(node_versions[baseline_version][0], '%Y-%m-%d')
latest_date = datetime.strptime(node_versions['v24.0.2'][0], '%Y-%m-%d')

# Process data
packages_data = []
for pkg in results:
    if pkg['packageName'] == 'CONTROL':
        continue

    oldest = pkg['oldestCompatible']
    if oldest is None:
        # Package doesn't work with any tested version
        continue

    pkg_date = datetime.strptime(node_versions[oldest][0], '%Y-%m-%d')
    versions_lost = node_versions[oldest][1]

    # Categorize impact
    if versions_lost == 0:
        impact = 'none'
    elif versions_lost == 1:
        impact = 'minimal'
    elif versions_lost == 2:
        impact = 'moderate'
    elif versions_lost >= 3:
        impact = 'high'

    packages_data.append((
        pkg['packageName'],
        oldest,
        node_versions[oldest][0],
        versions_lost,
        impact,
        pkg['hasEngines']
    ))

# Sort by versions lost
packages_data.sort(key=lambda x: x[3])

# Color scheme
color_map = {
    'none': '#2E7D32',      # Green
    'minimal': '#66BB6A',   # Light green
    'moderate': '#FFB74D',  # Orange
    'high': '#E53935',      # Red
}

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle('Node.js Package Compatibility Timeline', fontsize=int(16*fs), fontweight='bold')

# Plot 1: Timeline bars
y_pos = 0
for name, oldest, date_str, versions_lost, impact, has_engines in packages_data:
    pkg_date = datetime.strptime(date_str, '%Y-%m-%d')

    # Calculate bar position and width
    bar_start = (pkg_date - baseline_date).days
    bar_width = (latest_date - pkg_date).days

    color = color_map[impact]

    # Draw bar
    ax1.barh(y_pos, bar_width, left=bar_start, height=0.8,
             color=color, alpha=0.7, edgecolor='black', linewidth=0.5)

    # Add package name
    marker = '*' if has_engines else ''
    ax1.text(-50, y_pos, f'{name}{marker}', ha='right', va='center', fontsize=int(9*fs), fontweight='bold')

    # Add version on bar
    text_x = bar_start + 30
    ax1.text(text_x, y_pos, f'{oldest}', ha='left', va='center', fontsize=int(7*fs), color='black')

    y_pos += 1

# Timeline setup
total_days = (latest_date - baseline_date).days
ax1.set_xlim(0, total_days)
ax1.set_ylim(-0.5, len(packages_data) - 0.5)
ax1.set_xlabel('Time', fontsize=int(12*fs))
ax1.set_yticks([])

# Add year/version markers
markers = []
for version, (date_str, idx, name) in node_versions.items():
    date = datetime.strptime(date_str, '%Y-%m-%d')
    days = (date - baseline_date).days
    ax1.axvline(days, color='gray', linestyle='--', alpha=0.3, linewidth=1)
    markers.append((days, f'{version}\n{name}'))

ax1.set_xticks([pos for pos, _ in markers])
ax1.set_xticklabels([label for _, label in markers], fontsize=int(8*fs))

# Grid
ax1.grid(axis='x', alpha=0.2)
ax1.set_title('Compatibility Window by Package (* = has engines declaration)\n(Each bar shows the range of supported Node.js versions)',
              fontsize=int(11*fs), pad=10)

# Baseline indicator
ax1.axvline(0, color='green', linestyle='-', linewidth=2, alpha=0.8)

# Plot 2: Impact distribution
impact_counts = {}
for _, _, _, _, impact, _ in packages_data:
    impact_counts[impact] = impact_counts.get(impact, 0) + 1

impact_order = ['none', 'minimal', 'moderate', 'high']
counts = [impact_counts.get(imp, 0) for imp in impact_order]
colors = [color_map[imp] for imp in impact_order]

bars = ax2.bar(impact_order, counts, color=colors, alpha=0.7, edgecolor='black')
ax2.set_ylabel('Number of Packages', fontsize=int(11*fs))
ax2.set_xlabel('Impact Level', fontsize=int(11*fs))
ax2.set_title('Distribution of Compatibility Impact', fontsize=int(11*fs))
ax2.grid(axis='y', alpha=0.2)

# Add count labels
for bar, count in zip(bars, counts):
    if count > 0:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontsize=int(10*fs), fontweight='bold')

# Legend
legend_elements = [
    mpatches.Patch(color=color_map['none'], label='No loss (v14+)', alpha=0.7),
    mpatches.Patch(color=color_map['minimal'], label='Minimal (v16+ required)', alpha=0.7),
    mpatches.Patch(color=color_map['moderate'], label='Moderate (v18+ required)', alpha=0.7),
    mpatches.Patch(color=color_map['high'], label='High (v20+ required)', alpha=0.7),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=int(8*fs), title='Impact Severity')

plt.tight_layout()
plt.savefig('compatibility-timeline-node.png', dpi=300, bbox_inches='tight')
print('Visualization saved to compatibility-timeline-node.png')

# Create versions lost chart
fig2, ax = plt.subplots(figsize=(12, 8))

package_names = [d[0] for d in packages_data]
versions_lost_list = [d[3] for d in packages_data]
impacts = [d[4] for d in packages_data]
colors_sorted = [color_map[imp] for imp in impacts]

# Horizontal bar chart
bars = ax.barh(range(len(package_names)), versions_lost_list, color=colors_sorted,
               alpha=0.7, edgecolor='black')

ax.set_yticks(range(len(package_names)))
ax.set_yticklabels(package_names, fontsize=int(9*fs))
ax.set_xlabel('Number of Node.js LTS Versions Lost', fontsize=int(12*fs))
ax.set_title('Toolchain Compatibility Loss by Package\n(Compared to no-dependency baseline of v14.21.3)',
             fontsize=int(13*fs), fontweight='bold')
ax.grid(axis='x', alpha=0.2)

# Add labels
for i, (bar, lost) in enumerate(zip(bars, versions_lost_list)):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
            f'{int(lost)}',
            ha='left', va='center', fontsize=int(8*fs))

# Baseline reference
ax.axvline(0, color='green', linestyle='-', linewidth=2, alpha=0.5, label='Baseline (no deps)')

plt.tight_layout()
plt.savefig('versions-lost-node.png', dpi=300, bbox_inches='tight')
print('Visualization saved to versions-lost-node.png')

# Only show plot window if --show argument is passed
if show_plot:
    plt.show()
