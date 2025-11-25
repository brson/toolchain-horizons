#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Visualize Go package toolchain compatibility on a timeline.
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
with open('go/results.json', 'r') as f:
    results = json.load(f)

# Go version release dates and indices.
go_versions = {
    '1.13': ('2019-09-03', 0),
    '1.14': ('2020-02-25', 1),
    '1.15': ('2020-08-11', 2),
    '1.16': ('2021-02-16', 3),
    '1.17': ('2021-08-16', 4),
    '1.18': ('2022-03-15', 5),
    '1.19': ('2022-08-02', 6),
    '1.20': ('2023-02-01', 7),
    '1.21': ('2023-08-08', 8),
    '1.21.0': ('2023-08-08', 8),
    '1.22': ('2024-02-06', 9),
    '1.22.0': ('2024-02-06', 9),
    '1.23': ('2024-08-13', 10),
    '1.23.0': ('2024-08-13', 10),
    '1.24': ('2025-02-11', 11),
    '1.24.0': ('2025-02-11', 11),
}

# Baseline.
baseline_version = '1.13'
baseline_date = datetime.strptime(go_versions[baseline_version][0], '%Y-%m-%d')
latest_date = datetime.strptime(go_versions['1.24'][0], '%Y-%m-%d')

# Process data.
packages_data = []
for package in results:
    package_name = package.get('package_name')
    if package_name == 'CONTROL':
        continue

    oldest = package.get('oldest_compatible')
    if oldest is None:
        # Package doesn't work with any tested version.
        continue

    package_date = datetime.strptime(go_versions[oldest][0], '%Y-%m-%d')
    versions_lost = go_versions[oldest][1] - go_versions[baseline_version][1]

    # Categorize impact.
    if versions_lost == 0:
        impact = 'minimal'
    elif versions_lost <= 2:
        impact = 'low'
    elif versions_lost <= 4:
        impact = 'moderate'
    elif versions_lost <= 6:
        impact = 'high'
    else:
        impact = 'severe'

    packages_data.append((
        package_name,
        oldest,
        go_versions[oldest][0],
        versions_lost,
        impact
    ))

# Sort by versions lost.
packages_data.sort(key=lambda x: x[3])

# Calculate total versions in baseline range.
baseline_total = go_versions['1.24'][1] - go_versions[baseline_version][1]

# Color scheme based on impact
color_map = {
    "baseline": "#2E7D32",  # Green
    "minimal": "#66BB6A",   # Light green
    "low": "#FDD835",       # Yellow
    "moderate": "#FFB74D",  # Orange
    "high": "#FF7043",      # Deep orange
    "severe": "#E53935",    # Red
}

# Create figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle('Go Package Toolchain Compatibility Timeline', fontsize=int(16*fs), fontweight='bold')

# Plot 1: Timeline bars
y_pos = 0

# Baseline bar
ax1.barh(y_pos, (latest_date - baseline_date).days, left=baseline_date,
         height=0.8, color=color_map["baseline"], label="Baseline (no deps)")
ax1.text(baseline_date, y_pos, ' Baseline (no deps)', va='center', ha='left',
         fontsize=int(8*fs), color='white', fontweight='bold')
y_pos += 1

# Package bars
for package_name, oldest_ver, oldest_date_str, versions_lost, impact in packages_data:
    oldest_date = datetime.strptime(oldest_date_str, '%Y-%m-%d')

    # Lost compatibility region (red/orange)
    if versions_lost > 0:
        ax1.barh(y_pos, (oldest_date - baseline_date).days, left=baseline_date,
                height=0.8, color='#CCCCCC', alpha=0.3)

    # Compatible region
    ax1.barh(y_pos, (latest_date - oldest_date).days, left=oldest_date,
             height=0.8, color=color_map[impact])

    # Package name
    display_name = package_name.split('/')[-1]  # Show only last component
    ax1.text(oldest_date, y_pos, f' {display_name}', va='center', ha='left',
             fontsize=int(7*fs))

    # Version lost label
    if versions_lost > 0:
        mid_date = baseline_date + (oldest_date - baseline_date) / 2
        ax1.text(mid_date, y_pos, f'-{versions_lost}', va='center', ha='center',
                fontsize=int(7*fs), color='#666666', fontweight='bold')

    y_pos += 1

# Format timeline axis
ax1.set_ylim(-0.5, y_pos - 0.5)
ax1.set_xlim(baseline_date, latest_date)
ax1.set_xlabel('Go Release Date', fontsize=int(12*fs))
ax1.set_yticks([])
ax1.grid(axis='x', alpha=0.3)

# Add version markers
for version, (date_str, _) in go_versions.items():
    date = datetime.strptime(date_str, '%Y-%m-%d')
    ax1.axvline(date, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
    ax1.text(date, y_pos - 0.5, f'Go\n{version}',
             ha='center', va='top', fontsize=int(7*fs), color='gray')

# Legend
impact_patches = [
    mpatches.Patch(color=color_map["minimal"], label='Minimal impact (0 versions lost)'),
    mpatches.Patch(color=color_map["low"], label='Low impact (1-2 versions lost)'),
    mpatches.Patch(color=color_map["moderate"], label='Moderate impact (3-4 versions lost)'),
    mpatches.Patch(color=color_map["high"], label='High impact (5-6 versions lost)'),
    mpatches.Patch(color=color_map["severe"], label='Severe impact (7+ versions lost)'),
]
ax1.legend(handles=impact_patches, loc='upper left', fontsize=int(9*fs))

# Plot 2: Versions lost distribution
versions_lost_counts = {}
for _, _, _, versions_lost, _ in packages_data:
    versions_lost_counts[versions_lost] = versions_lost_counts.get(versions_lost, 0) + 1

x_vals = sorted(versions_lost_counts.keys())
y_vals = [versions_lost_counts[x] for x in x_vals]
colors = [color_map[
    'minimal' if x == 0 else
    'low' if x <= 2 else
    'moderate' if x <= 4 else
    'high' if x <= 6 else
    'severe'
] for x in x_vals]

ax2.bar(x_vals, y_vals, color=colors, alpha=0.8, edgecolor='black')
ax2.set_xlabel('Go Versions Lost', fontsize=int(12*fs))
ax2.set_ylabel('Number of Packages', fontsize=int(12*fs))
ax2.set_title('Distribution of Compatibility Loss', fontsize=int(12*fs))
ax2.grid(axis='y', alpha=0.3)

# Add count labels on bars
for x, y in zip(x_vals, y_vals):
    ax2.text(x, y + 0.1, str(y), ha='center', va='bottom', fontsize=int(9*fs), fontweight='bold')

plt.tight_layout()

# Save or show
if show_plot:
    plt.show()
else:
    plt.savefig('compatibility-timeline-go.png', dpi=150, bbox_inches='tight')
    print("Saved: compatibility-timeline-go.png")

    # Create second chart: versions lost
    fig2, ax = plt.subplots(figsize=(12, 8))

    # Sort packages by versions lost
    packages_sorted = sorted(packages_data, key=lambda x: x[3], reverse=True)

    package_names = [p[0].split('/')[-1] for p in packages_sorted]
    versions_lost_vals = [p[3] for p in packages_sorted]
    colors = [color_map[p[4]] for p in packages_sorted]

    y_positions = range(len(package_names))
    bars = ax.barh(y_positions, versions_lost_vals, color=colors, alpha=0.8, edgecolor='black')

    ax.set_yticks(y_positions)
    ax.set_yticklabels(package_names, fontsize=int(9*fs))
    ax.set_xlabel('Go Versions Lost from Baseline (Go 1.13)', fontsize=int(12*fs))
    ax.set_title('Go Package Toolchain Compatibility Impact', fontsize=int(14*fs), fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, versions_lost_vals)):
        ax.text(val + 0.1, i, str(val), va='center', fontsize=int(9*fs), fontweight='bold')

    # Add legend
    ax.legend(handles=impact_patches, loc='lower right', fontsize=int(9*fs))

    plt.tight_layout()
    plt.savefig('versions-lost-go.png', dpi=150, bbox_inches='tight')
    print("Saved: versions-lost-go.png")
