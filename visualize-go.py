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
import chart_style as cs

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
color_map = cs.COLOR_MAP

# Create figure
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=cs.FIGURE_SIZE, gridspec_kw={'height_ratios': cs.HEIGHT_RATIOS})
fig.suptitle('Go Package Toolchain Compatibility Timeline\nGo Modules Era', fontsize=int(cs.FONT_TITLE*fs), fontweight='bold')

# Plot 1: Timeline bars
y_pos = 0
for package_name, oldest_ver, oldest_date_str, versions_lost, impact in packages_data:
    oldest_date = datetime.strptime(oldest_date_str, '%Y-%m-%d')

    # Calculate bar position and width (numeric days)
    bar_start = (oldest_date - baseline_date).days
    bar_width = (latest_date - oldest_date).days

    color = color_map[impact]

    # Draw bar from package's min version to latest
    ax1.barh(y_pos, bar_width, left=bar_start, height=cs.BAR_HEIGHT,
             color=color, alpha=cs.BAR_ALPHA, edgecolor=cs.BAR_EDGE_COLOR, linewidth=cs.BAR_EDGE_WIDTH)

    # Add package name (outside bar to the left)
    display_name = package_name.split('/')[-1]  # Show only last component
    ax1.text(cs.LABEL_OFFSET_X, y_pos, display_name, ha='right', va='center',
             fontsize=int(cs.FONT_PKG_NAME*fs), fontweight='bold')

    # Add version label on the bar
    text_x = bar_start + cs.VERSION_OFFSET_X
    ax1.text(text_x, y_pos, f'{oldest_ver}',
             ha='left', va='center', fontsize=int(cs.FONT_VERSION_LABEL*fs), color='black')

    y_pos += 1

# Timeline from baseline to latest
total_days = (latest_date - baseline_date).days
ax1.set_xlim(0, total_days)
ax1.set_ylim(-0.5, len(packages_data) - 0.5)
ax1.set_xlabel('Time', fontsize=int(cs.FONT_AXIS_LABEL*fs))
ax1.set_yticks([])

# Add year markers
year_markers = []
for year in range(2020, 2026):
    year_date = datetime(year, 1, 1)
    if year_date >= baseline_date and year_date <= latest_date:
        days_from_start = (year_date - baseline_date).days
        ax1.axvline(days_from_start, color='gray', linestyle='--', alpha=cs.GRID_ALPHA, linewidth=cs.MARKER_LINEWIDTH)
        year_markers.append((days_from_start, str(year)))

# Set x-axis labels to years
ax1.set_xticks([pos for pos, _ in year_markers])
ax1.set_xticklabels([label for _, label in year_markers])

# Add grid
ax1.grid(axis='x', alpha=cs.GRID_ALPHA)

# Add baseline indicator
baseline_line = ax1.axvline(0, color='green', linestyle='-', linewidth=cs.BASELINE_LINEWIDTH, alpha=cs.BASELINE_ALPHA)

# Plot 2: Impact distribution (categorical like Rust)
impact_counts = {}
for _, _, _, _, impact in packages_data:
    impact_counts[impact] = impact_counts.get(impact, 0) + 1

impact_order = ["minimal", "low", "moderate", "high", "severe"]
counts = [impact_counts.get(imp, 0) for imp in impact_order]
colors = [color_map[imp] for imp in impact_order]

bars = ax2.bar(impact_order, counts, color=colors, alpha=cs.BAR_ALPHA, edgecolor=cs.BAR_EDGE_COLOR)
ax2.set_ylabel('Number of Packages', fontsize=int(cs.FONT_SUBTITLE*fs))
ax2.set_xlabel('Impact Level', fontsize=int(cs.FONT_SUBTITLE*fs))
ax2.set_title('Distribution of Compatibility Impact', fontsize=int(cs.FONT_SUBTITLE*fs))
ax2.grid(axis='y', alpha=cs.GRID_ALPHA)

# Add count labels on bars
for bar, count in zip(bars, counts):
    if count > 0:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontsize=int(cs.FONT_COUNT_LABEL*fs), fontweight='bold')

# Create legend for impact levels
legend_elements = [
    mpatches.Patch(color=color_map["minimal"], label='Minimal (0 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["low"], label='Low (1-2 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["moderate"], label='Moderate (3-4 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["high"], label='High (5-6 versions lost)', alpha=cs.BAR_ALPHA),
    mpatches.Patch(color=color_map["severe"], label='Severe (7+ versions lost)', alpha=cs.BAR_ALPHA),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=int(cs.FONT_LEGEND*fs), title='Impact Severity')

plt.tight_layout()
plt.savefig('compatibility-timeline-go.png', dpi=cs.DPI, bbox_inches='tight')
print("Saved: compatibility-timeline-go.png")

# Create a second visualization: Lost versions chart
fig2, ax = plt.subplots(figsize=cs.FIGURE_SIZE_SECONDARY)

# Sort by versions lost (ascending, like Rust)
package_names = [p[0].split('/')[-1] for p in packages_data]
versions_lost_vals = [p[3] for p in packages_data]
colors_sorted = [color_map[p[4]] for p in packages_data]

# Create horizontal bar chart
bars = ax.barh(range(len(package_names)), versions_lost_vals, color=colors_sorted,
               alpha=cs.BAR_ALPHA, edgecolor=cs.BAR_EDGE_COLOR, linewidth=cs.BAR_EDGE_WIDTH)

ax.set_yticks(range(len(package_names)))
ax.set_yticklabels(package_names, fontsize=int(cs.FONT_PKG_NAME*fs))
ax.set_xlabel('Number of Go Versions Lost', fontsize=int(cs.FONT_AXIS_LABEL*fs))
ax.set_title(f'Toolchain Compatibility Loss by Package\n(Compared to no-dependency baseline of {baseline_total} versions)',
             fontsize=int(13*fs), fontweight='bold')
ax.grid(axis='x', alpha=cs.GRID_ALPHA)

# Add percentage labels
for i, (bar, lost) in enumerate(zip(bars, versions_lost_vals)):
    percentage = (lost / baseline_total) * 100
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
            f'{int(lost)} ({percentage:.0f}%)',
            ha='left', va='center', fontsize=int(cs.FONT_LEGEND*fs))

# Add baseline reference line
ax.axvline(0, color='green', linestyle='-', linewidth=cs.BASELINE_LINEWIDTH, alpha=0.5, label='Baseline (no deps)')

plt.tight_layout()
plt.savefig('versions-lost-go.png', dpi=cs.DPI, bbox_inches='tight')
print("Saved: versions-lost-go.png")

# Only show plot window if --show argument is passed
if show_plot:
    plt.show()
