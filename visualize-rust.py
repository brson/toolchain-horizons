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

# Data from experiment results
crates_data = [
    ("CONTROL", "1.16.0", "2017-03-16", 0, "baseline"),
    ("bitflags", "1.31.1", "2018-12-20", 15, "minimal"),
    ("serde", "1.31.1", "2018-12-20", 15, "minimal"),
    ("mime", "1.31.1", "2018-12-20", 15, "minimal"),
    ("cfg-if", "1.32.0", "2019-01-17", 16, "minimal"),
    ("hex", "1.36.0", "2019-07-04", 20, "low"),
    ("anyhow", "1.38.0", "2019-09-26", 22, "low"),
    ("regex", "1.51.0", "2021-03-25", 35, "moderate"),
    ("semver", "1.51.0", "2021-03-25", 35, "moderate"),
    ("byteorder", "1.60.0", "2022-04-07", 44, "high"),
    ("futures", "1.61.0", "2022-05-19", 45, "high"),
    ("log", "1.61.0", "2022-05-19", 45, "high"),
    ("crossbeam", "1.61.0", "2022-05-19", 45, "high"),
    ("extension-trait", "1.61.0", "2022-05-19", 45, "high"),
    ("syn", "1.61.0", "2022-05-19", 45, "high"),
    ("thiserror", "1.61.0", "2022-05-19", 45, "high"),
    ("chrono", "1.62.1", "2022-07-19", 46, "high"),
    ("itertools", "1.63.0", "2022-08-11", 47, "severe"),
    ("libc", "1.63.0", "2022-08-11", 47, "severe"),
    ("num_cpus", "1.63.0", "2022-08-11", 47, "severe"),
    ("rand", "1.63.0", "2022-08-11", 47, "severe"),
    ("socket2", "1.63.0", "2022-08-11", 47, "severe"),
    ("tempfile", "1.65.0", "2022-11-03", 49, "severe"),
    ("env_logger", "1.71.1", "2023-08-03", 55, "extreme"),
    ("rayon", "1.80.1", "2024-08-08", 64, "extreme"),
    ("backtrace", "1.82.0", "2024-10-17", 66, "extreme"),
]

# Timeline boundaries
baseline_date = datetime.strptime("2017-03-16", "%Y-%m-%d")
latest_date = datetime.strptime("2024-12-01", "%Y-%m-%d")  # Approximate "now"

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
fig.suptitle('Rust Crate Toolchain Compatibility Timeline\nEdition 2018', fontsize=16, fontweight='bold')

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
    ax1.text(-50, y_pos, crate_name, ha='right', va='center', fontsize=9, fontweight='bold')

    # Add version and date on the bar
    text_x = bar_start + 30
    ax1.text(text_x, y_pos, f'{rust_version}',
             ha='left', va='center', fontsize=7, color='black')

    y_pos += 1

# Timeline from baseline to now
total_days = (latest_date - baseline_date).days
ax1.set_xlim(0, total_days)
ax1.set_ylim(-0.5, len(crates_data) - 0.5)
ax1.set_xlabel('Time →', fontsize=12)
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
              fontsize=11, pad=10)

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
ax2.set_ylabel('Number of Crates', fontsize=11)
ax2.set_xlabel('Impact Level', fontsize=11)
ax2.set_title('Distribution of Compatibility Impact', fontsize=11)
ax2.grid(axis='y', alpha=0.2)

# Add count labels on bars
for bar, count in zip(bars, counts):
    if count > 0:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Create legend for impact levels
legend_elements = [
    mpatches.Patch(color=color_map["baseline"], label='Baseline (0% loss)', alpha=0.7),
    mpatches.Patch(color=color_map["minimal"], label='Minimal (15-20% loss)', alpha=0.7),
    mpatches.Patch(color=color_map["low"], label='Low (20-30% loss)', alpha=0.7),
    mpatches.Patch(color=color_map["moderate"], label='Moderate (35-47% loss)', alpha=0.7),
    mpatches.Patch(color=color_map["high"], label='High (44-62% loss)', alpha=0.7),
    mpatches.Patch(color=color_map["severe"], label='Severe (47-66% loss)', alpha=0.7),
    mpatches.Patch(color=color_map["extreme"], label='Extreme (74-89% loss)', alpha=0.7),
]
ax1.legend(handles=legend_elements, loc='upper left', fontsize=8, title='Impact Severity')

plt.tight_layout()
plt.savefig('compatibility-timeline-rust.png', dpi=300, bbox_inches='tight')
print("Visualization saved to compatibility-timeline-rust.png")

# Create a second visualization: Lost versions chart
fig2, ax = plt.subplots(figsize=(12, 8))

# Sort by versions lost
sorted_data = sorted(crates_data[1:], key=lambda x: x[3])  # Skip baseline
crate_names = [d[0] for d in sorted_data]
versions_lost = [d[3] for d in sorted_data]
impacts = [d[4] for d in sorted_data]
colors_sorted = [color_map[imp] for imp in impacts]

# Create horizontal bar chart
bars = ax.barh(range(len(crate_names)), versions_lost, color=colors_sorted,
               alpha=0.7, edgecolor='black')

ax.set_yticks(range(len(crate_names)))
ax.set_yticklabels(crate_names, fontsize=9)
ax.set_xlabel('Number of Rust Versions Lost', fontsize=12)
ax.set_title('Toolchain Compatibility Loss by Crate\n(Compared to no-dependency baseline of 74 versions)',
             fontsize=13, fontweight='bold')
ax.grid(axis='x', alpha=0.2)

# Add percentage labels
for i, (bar, lost) in enumerate(zip(bars, versions_lost)):
    percentage = (lost / 74) * 100
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
            f'{int(lost)} ({percentage:.0f}%)',
            ha='left', va='center', fontsize=8)

# Add baseline reference line
ax.axvline(0, color='green', linestyle='-', linewidth=2, alpha=0.5, label='Baseline (no deps)')

plt.tight_layout()
plt.savefig('versions-lost-rust.png', dpi=300, bbox_inches='tight')
print("Visualization saved to versions-lost-rust.png")

plt.show()
