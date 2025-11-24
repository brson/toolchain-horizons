#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
#   "numpy>=1.24.0",
# ]
# ///
"""
Visualize Java package toolchain compatibility on a timeline.
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
with open('java/results.json', 'r') as f:
    results = json.load(f)

# Java version release dates and indices.
java_versions = {
    '8.0.432-tem': ('2014-03-18', 0),    # Java 8
    '11.0.25-tem': ('2018-09-25', 1),    # Java 11
    '17.0.13-tem': ('2021-09-14', 2),    # Java 17
    '21.0.5-tem': ('2023-09-19', 3),     # Java 21
    '23.0.1-tem': ('2024-09-17', 4),     # Java 23
}

# Baseline.
baseline_version = '8.0.432-tem'
baseline_date = datetime.strptime(java_versions[baseline_version][0], '%Y-%m-%d')
latest_date = datetime.strptime(java_versions['23.0.1-tem'][0], '%Y-%m-%d')

# Process data.
packages_data = []
for package in results:
    # Handle both snake_case and camelCase for backward compatibility
    package_name = package.get('package_name') or package.get('packageName')
    if package_name == 'CONTROL':
        continue

    oldest = package.get('oldest_compatible') or package.get('oldestCompatible')
    if oldest is None:
        # Package doesn't work with any tested version.
        continue

    package_date = datetime.strptime(java_versions[oldest][0], '%Y-%m-%d')
    versions_lost = java_versions[oldest][1] - java_versions[baseline_version][1]

    # Categorize impact.
    if versions_lost == 0:
        impact = 'minimal'
    elif versions_lost == 1:
        impact = 'low'
    elif versions_lost == 2:
        impact = 'moderate'
    elif versions_lost == 3:
        impact = 'high'
    else:
        impact = 'severe'

    packages_data.append((
        package_name,
        oldest,
        java_versions[oldest][0],
        versions_lost,
        impact
    ))

# Sort by versions lost.
packages_data.sort(key=lambda x: x[3])

# Calculate total versions in baseline range.
baseline_total = java_versions['23.0.1-tem'][1] - java_versions[baseline_version][1]

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
fig.suptitle('Java Package Toolchain Compatibility Timeline', fontsize=int(16*fs), fontweight='bold')

# Plot 1: Timeline bars
y_pos = 0
for package_name, java_version, date_str, versions_lost, impact in packages_data:
    package_date = datetime.strptime(date_str, "%Y-%m-%d")

    # Calculate bar position and width
    bar_start = (package_date - baseline_date).days
    bar_width = (latest_date - package_date).days

    color = color_map[impact]

    # Draw bar from package's min version to latest
    ax1.barh(y_pos, bar_width, left=bar_start, height=0.8,
             color=color, alpha=0.7, edgecolor='black', linewidth=0.5)

    # Add package name
    ax1.text(-50, y_pos, package_name, ha='right', va='center', fontsize=int(9*fs), fontweight='bold')

    # Add version and date on the bar
    text_x = bar_start + 30
    version_label = java_version.split('.')[0]  # "8.0.432-tem" -> "8"
    ax1.text(text_x, y_pos, f'Java {version_label}',
             ha='left', va='center', fontsize=int(7*fs), color='black')

    y_pos += 1

# Timeline from baseline to now
total_days = (latest_date - baseline_date).days
ax1.set_xlim(0, total_days)
ax1.set_ylim(-0.5, len(packages_data) - 0.5)
ax1.set_xlabel('Time', fontsize=int(12*fs))
ax1.set_yticks([])

# Add year markers
year_markers = []
for year in range(2014, 2025):
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
ax1.set_title('Compatibility Window by Package\n(Each bar shows the range of supported Java versions)',
              fontsize=int(11*fs), pad=10)

# Add baseline indicator
baseline_line = ax1.axvline(0, color='green', linestyle='-', linewidth=2, alpha=0.8)

# Plot 2: Impact distribution
impact_counts = {}
for _, _, _, _, impact in packages_data:
    if impact != "baseline":
        impact_counts[impact] = impact_counts.get(impact, 0) + 1

impact_order = ["minimal", "low", "moderate", "high", "severe"]
counts = [impact_counts.get(imp, 0) for imp in impact_order]
colors = [color_map[imp] for imp in impact_order]

bars = ax2.bar(impact_order, counts, color=colors, alpha=0.7, edgecolor='black')
ax2.set_ylabel('Number of Packages', fontsize=int(11*fs))
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
    mpatches.Patch(color=color_map["minimal"], label='Minimal (0 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["low"], label='Low (1 version lost)', alpha=0.7),
    mpatches.Patch(color=color_map["moderate"], label='Moderate (2 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["high"], label='High (3 versions lost)', alpha=0.7),
    mpatches.Patch(color=color_map["severe"], label='Severe (4+ versions lost)', alpha=0.7),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=int(8*fs), title='Impact Severity')

plt.tight_layout()
plt.savefig('compatibility-timeline-java.png', dpi=300, bbox_inches='tight')
print("Visualization saved to compatibility-timeline-java.png")

# Create a second visualization: Lost versions chart
fig2, ax = plt.subplots(figsize=(12, 8))

# Use the already sorted packages_data (CONTROL was already filtered out).
package_names = [d[0] for d in packages_data]
versions_lost = [d[3] for d in packages_data]
impacts = [d[4] for d in packages_data]
colors_sorted = [color_map[imp] for imp in impacts]

# Create horizontal bar chart
bars = ax.barh(range(len(package_names)), versions_lost, color=colors_sorted,
               alpha=0.7, edgecolor='black')

ax.set_yticks(range(len(package_names)))
ax.set_yticklabels(package_names, fontsize=int(9*fs))
ax.set_xlabel('Number of Java Versions Lost', fontsize=int(12*fs))
ax.set_title(f'Toolchain Compatibility Loss by Package\n(Compared to no-dependency baseline of {baseline_total} versions)',
             fontsize=int(13*fs), fontweight='bold')
ax.grid(axis='x', alpha=0.2)

# Add percentage labels
for i, (bar, lost) in enumerate(zip(bars, versions_lost)):
    percentage = (lost / baseline_total) * 100 if baseline_total > 0 else 0
    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
            f'{int(lost)} ({percentage:.0f}%)',
            ha='left', va='center', fontsize=int(8*fs))

# Add baseline reference line
ax.axvline(0, color='green', linestyle='-', linewidth=2, alpha=0.5, label='Baseline (no deps)')

plt.tight_layout()
plt.savefig('versions-lost-java.png', dpi=300, bbox_inches='tight')
print("Visualization saved to versions-lost-java.png")

# Only show plot window if --show argument is passed
if show_plot:
    plt.show()
