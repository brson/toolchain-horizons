# Experiment Enhancement Plan

## Completed

- [x] Create comprehensive justfile with 19 recipes
- [x] Implement prerequisite checker for all toolchain managers
- [x] Add individual experiment runners (rust, java, python, node, go)
- [x] Update visualize.py to use uv with PEP 723 inline metadata
- [x] Add cleanup recipes for each language
- [x] Add validation and utility recipes
- [x] Delete old venv/ directory
- [x] Create REPRODUCING.md documentation
- [x] Test all recipes end-to-end
- [x] Install Maven via SDKMAN

## Key Findings

### Java: Bytecode Distribution vs Source Distribution

**Discovery:** Maven downloads pre-compiled bytecode (.class files in JARs), not source code. This is fundamentally different from Rust/Cargo, which downloads source code and recompiles for each target.

**Implications:**
- The Java experiment tests **bytecode compatibility**, not source language features
- Libraries can compile to older Java bytecode (e.g., Java 8) even if they document newer requirements (e.g., Java 11+)
- Runtime API usage incompatibilities cannot be detected at compile time
- This explains why all 26 tested Java packages showed Java 8 compatibility

**Critical Fix Applied:**
Initially, the test generated an empty `Main.java` class that didn't actually import or use any library code:
```java
public class Main { public static void main(String[] args) {} }
```

This was fixed to generate code that imports and references library classes:
```java
import com.google.inject.Guice;

public class Main {
    public static void main(String[] args) {
        Class<?> cls = com.google.inject.Guice.class;
    }
}
```

**Why Results Differ from Rust:**
- **Java libraries:** Maintain aggressive backward bytecode compatibility (most compile to Java 8)
- **Rust crates:** Often use newer language features, requiring recent MSRV
- **Java dependency model:** Pre-compiled bytecode downloaded once, shared across projects
- **Rust dependency model:** Source code recompiled for each project with its toolchain

**Verification:**
- Single package test confirmed: Guice 7.0 compiles successfully with Java 8 despite docs claiming Java 11+ requirement
- The test now properly imports library classes to verify compilation compatibility
- File: `java/src/main/java/Experiment.java:345` (testJavaVersion method)

## Next Steps

### High Priority

#### 1. Cross-Language Visualization
Create `visualize-all.py` to compare all four ecosystems on a single chart.

**Features:**
- Timeline showing compatibility loss across Rust, Java, Python, Node.js
- Bar chart comparing average version loss by ecosystem
- Heat map showing which ecosystems have the most restrictions
- Use same PEP 723 metadata pattern as visualize.py

**Implementation:**
```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = [
#   "matplotlib>=3.7.0",
#   "numpy>=1.24.0",
# ]
# ///
```

**Justfile integration:**
Update `visualize-all` recipe to actually run the script instead of TODO message.

#### 2. Result Collation Tool
Create `scripts/collate-results.py` to aggregate and normalize results.

**Current issues:**
- Rust uses: `crate_name`, `oldest_compatible`, `latest_compatible`
- Java uses: `packageName`, `oldestCompatible`, `latestCompatible`
- Inconsistent field naming across experiments

**Options:**
- A) Update each experiment to use snake_case (most consistent)
- B) Create converter that normalizes to common schema
- C) Both: update experiments + provide converter for backwards compatibility

**Output format:**
```json
{
  "metadata": {
    "generated_at": "2025-10-29T...",
    "experiments": ["rust", "java", "python", "node"]
  },
  "rust": [...],
  "java": [...],
  "python": [...],
  "node": [...]
}
```

### Medium Priority

#### 3. Parallel Experiment Execution
Add `just all-experiments-parallel` for faster execution.

**Implementation considerations:**
- Use bash background jobs: `cmd1 & cmd2 & cmd3 & wait`
- Or use GNU parallel if available
- Capture output from each experiment separately
- Report status of each as they complete

**Estimated time savings:**
- Sequential: ~60 minutes total
- Parallel: ~30 minutes total (limited by longest experiment)

#### 4. Result Validation Enhancement
Improve `validate-results` to check content, not just JSON validity.

**Additional checks:**
- Verify control case exists in each results.json
- Check that package counts match expected values
- Validate version format (semver-like)
- Report statistics: packages tested, failures, average compatibility

#### 5. CI/GitHub Actions Integration
Add `.github/workflows/experiments.yml` to run experiments on schedule.

**Benefits:**
- Detect ecosystem changes over time
- Verify experiments still work as toolchains evolve
- Generate updated charts automatically

**Workflow:**
```yaml
name: Run Experiments
on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly
  workflow_dispatch:      # Manual trigger

jobs:
  experiments:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install prerequisites
        run: |
          # Install rustup, sdkman, uv, nvm, go
      - name: Run experiments
        run: just all-experiments
      - name: Generate visualizations
        run: just visualize
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: results
          path: |
            */results.json
            *.png
```

### Low Priority

#### 6. Interactive Results Explorer
Create a web-based dashboard to explore results.

**Technology:**
- Simple HTML + JavaScript
- Or Python Flask/FastAPI + Chart.js
- Or Jupyter notebook with interactive widgets

**Features:**
- Filter by language, package, version range
- Compare specific packages across ecosystems
- Timeline scrubber to see compatibility at different dates

#### 7. Result Archival
Store historical results to track changes over time.

**Structure:**
```
results-archive/
  2025-10-29/
    rust/results.json
    java/results.json
    ...
  2025-11-29/
    rust/results.json
    ...
```

**Analysis:**
- How has compatibility changed as new package versions release?
- Which ecosystems are getting more restrictive over time?
- Impact of major language releases (Rust edition, Python 3.13, etc.)

#### 8. Blog Post Integration
Update blog post generation to automatically include latest results.

**Automation:**
- Template-based blog post generation
- Auto-update statistics from results.json
- Regenerate charts for blog
- Keep blog post in sync with experiment findings

#### 9. Package Version Updates
Regularly update the package version specs in experiments.

**Current state:**
- Package lists were defined at project start
- May be testing old versions now
- Some packages may have new major versions

**Maintenance:**
- Quarterly review of package lists
- Update version specs to latest major versions
- Document when/why packages were added/removed

## Technical Decisions Needed

### Question 1: Result Format Standardization
Which approach for JSON field naming?

- **Option A:** Update all experiments to snake_case (consistent with Rust)
- **Option B:** Create converter tool, leave experiments as-is
- **Option C:** Both - normalize going forward + support legacy format

**Recommendation:** Option A (snake_case everywhere) for long-term consistency.

### Question 2: Go Experiment Package Selection
Which packages to include in expanded Go test list?

Need balance of:
- Foundational packages (widely used)
- Different categories (web, CLI, data, etc.)
- Reasonable test runtime
- Package stability (avoid rapidly changing APIs)

### Question 3: Visualization Library
Continue with matplotlib or explore alternatives?

**matplotlib (current):**
- Pro: Full-featured, well-documented
- Con: Heavy dependency, slow startup

**Alternatives:**
- plotly: Interactive charts, lighter weight
- seaborn: Better defaults, built on matplotlib
- altair: Declarative, good for web

**Recommendation:** Stick with matplotlib for now (working well).

### Question 4: Cross-Language Comparison Metrics
What metrics best compare ecosystems?

**Candidates:**
- Average version loss percentage
- Median oldest compatible version date
- Percentage of packages requiring recent toolchain
- Time horizon collapse (years lost)
- Version lockout threshold (% requiring latest)

**Recommendation:** Use multiple metrics, no single number tells full story.

## Timeline Estimates

**High Priority Items:**
- Cross-language visualization: 2-3 hours
- Result collation tool: 1-2 hours
- **Total: 3-5 hours**

**Medium Priority Items:**
- Parallel execution: 1-2 hours
- Enhanced validation: 1 hour
- CI integration: 2-3 hours
- **Total: 4-6 hours**

**Low Priority Items:**
- Interactive explorer: 8-16 hours
- Result archival: 2-3 hours
- Blog automation: 2-4 hours
- Package updates: 1-2 hours (recurring)
- **Total: 13-25 hours**

## Open Questions

1. Should we add more languages (Go, C++, C#, Ruby, PHP, etc.)?
2. Should experiments test pre-release/beta toolchain versions?
3. What's the best way to share results (GitHub Pages, blog, paper)?
4. Should we measure compile/check time in addition to compatibility?
5. Would testing actual dependency combinations (not just individual) be valuable?
6. Should we weight packages by popularity/download counts?

## Resources

- Justfile documentation: https://github.com/casey/just
- PEP 723 (inline script metadata): https://peps.python.org/pep-0723/
- uv documentation: https://docs.astral.sh/uv/
- matplotlib gallery: https://matplotlib.org/stable/gallery/
