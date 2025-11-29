# Reproducing the Dependency Toolchain Compatibility Experiment

This guide explains how to reproduce the experiments that measure how dependencies affect toolchain version compatibility across four programming ecosystems: Rust, Java, Python, and Node.js.

## Prerequisites

This experiment requires several toolchain managers. Run the prerequisite checker to verify your setup:

```bash
just check-prereqs
```

### Required Tools

1. **just** - Command runner (https://github.com/casey/just)
2. **rustup** - Rust toolchain manager
3. **cargo** - Rust package manager (comes with rustup)
4. **SDKMAN** - Java/JVM version manager (https://sdkman.io/)
5. **Maven** - Java build tool (install via SDKMAN: `sdk install maven`)
6. **uv** - Python package manager (https://astral.sh/uv)
7. **nvm** - Node.js version manager (https://github.com/nvm-sh/nvm)

### Quick Installation

```bash
# Install just
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin

# Install rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install SDKMAN
curl -s "https://get.sdkman.io" | bash
source ~/.sdkman/bin/sdkman-init.sh
sdk install maven

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
```

## Running Experiments

### Run All Experiments

To run all four experiments sequentially:

```bash
just all-experiments
```

This will:
1. Run the Rust experiment (~15-30 minutes)
2. Run the Java experiment (~10-20 minutes)
3. Run the Python experiment (~5-10 minutes)
4. Run the Node.js experiment (~5-10 minutes)

Results will be written to `{language}/results.json` for each experiment.

### Run Individual Experiments

```bash
just rust-experiment      # Rust only
just java-experiment      # Java only
just python-experiment    # Python only
just node-experiment      # Node.js only
```

## Generating Visualizations

After running experiments, generate visualizations:

```bash
just visualize-rust       # Rust timeline charts
just visualize-all        # Cross-language comparison (TODO)
```

The `visualize-rust` command uses `uv` to automatically install required dependencies (matplotlib, numpy) and generates:
- `compatibility-timeline.png` - Timeline showing compatibility windows
- `versions-lost.png` - Bar chart of version losses

## Validating Results

Check that all experiments completed successfully:

```bash
just validate-results
```

This validates that all four `results.json` files exist and contain valid JSON.

## Viewing Installed Toolchains

To see what toolchain versions are installed:

```bash
just list-versions
```

## Cleaning Up

Remove experiment results and generated files:

```bash
just clean                # Clean all artifacts
just clean-rust           # Clean Rust artifacts only
just clean-java           # Clean Java artifacts only
just clean-python         # Clean Python artifacts only
just clean-node           # Clean Node.js artifacts only
just clean-visualizations # Clean PNG files only
```

## Experiment Methodology

Each experiment follows the same pattern:

1. **Control Case**: Test a project with no dependencies to establish a baseline
2. **Individual Testing**: Test each package/crate individually
3. **Binary Search**: Use binary search to find the oldest compatible toolchain version
4. **Version Range**: Test a reasonable range of historical versions for each ecosystem

### Rust Experiment

- Tests 29 foundational crates from the Rust ecosystem
- Range: Rust 1.0.0 to 1.90.0 (74 versions, ~7.4 years)
- Uses `rustup` to install versions and `cargo check` to test compatibility
- Baseline (no dependencies): Compatible with Rust 1.16.0+

### Java Experiment

- Tests 26 foundational Java libraries
- Range: Java 8, 11, 17, 21, 23 (LTS versions + latest)
- Uses SDKMAN to manage Java versions
- Baseline: All tested packages compatible with Java 8-23

### Python Experiment

- Tests 19 foundational Python packages
- Range: Python 3.8 to 3.13
- Uses `uv` for version management and package installation
- Baseline: Most packages compatible across all tested versions

### Node.js Experiment

- Tests 21 foundational Node.js packages
- Range: Node 14, 16, 18, 20, 22, 24
- Uses `nvm` for version management
- Two-phase testing: engine-strict validation + runtime testing
- Baseline: Significant restrictions (many require Node 18+)

## Results Format

Each experiment produces a `results.json` file with similar structure:

```json
[
  {
    "package_name": "example",
    "dependency_spec": "1.0",
    "resolved_version": "1.2.3",
    "oldest_compatible": "1.45.0",
    "latest_compatible": "1.90.0",
    "error": null
  }
]
```

Field names vary slightly by language (snake_case vs camelCase).

## Troubleshooting

### "command not found" errors

Make sure toolchain managers are sourced in your shell:

```bash
# Add to ~/.bashrc or ~/.zshrc
source ~/.sdkman/bin/sdkman-init.sh
source ~/.nvm/nvm.sh
```

### Slow experiment execution

Experiments can take 30-60 minutes total due to:
- Downloading and installing multiple toolchain versions
- Binary search across version ranges
- Dependency resolution and compilation testing

Consider running individual experiments or using previously generated results.

### Version installation failures

Some older toolchain versions may fail to install on modern systems. The experiments handle this gracefully and report errors in results.json.

## Contributing

To extend the experiments:

1. Add new packages to the test lists in each experiment source file
2. Adjust version ranges if needed
3. Run the updated experiment
4. Validate results with `just validate-results`

## License

See project LICENSE file.
