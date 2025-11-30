# Dependency Toolchain Compatibility Experiment
#
# Reproducible experiments testing how dependencies affect
# toolchain version compatibility across Rust, Java, Python, Node.js, and Go

# Default recipe shows available commands
default:
    @just --list

# Check all prerequisites (toolchain managers)
check-prereqs:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Checking prerequisites..."
    echo ""

    missing=0

    # Check for just (meta!)
    if command -v just &> /dev/null; then
        echo "✓ just: $(just --version)"
    else
        echo "✗ just: NOT FOUND"
        echo "  Install: https://github.com/casey/just#installation"
        missing=$((missing + 1))
    fi

    # Check for rustup
    if command -v rustup &> /dev/null; then
        echo "✓ rustup: $(rustup --version | head -n1)"
    else
        echo "✗ rustup: NOT FOUND"
        echo "  Install: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
        missing=$((missing + 1))
    fi

    # Check for cargo
    if command -v cargo &> /dev/null; then
        echo "✓ cargo: $(cargo --version)"
    else
        echo "✗ cargo: NOT FOUND (should come with rustup)"
        missing=$((missing + 1))
    fi

    # Check for SDKMAN (Java)
    if [[ -f "$HOME/.sdkman/bin/sdkman-init.sh" ]]; then
        echo "✓ sdkman: Found at $HOME/.sdkman/"
    else
        echo "✗ sdkman: NOT FOUND"
        echo "  Install: curl -s 'https://get.sdkman.io' | bash"
        missing=$((missing + 1))
    fi

    # Check for uv (Python)
    if command -v uv &> /dev/null; then
        echo "✓ uv: $(uv --version)"
    else
        echo "✗ uv: NOT FOUND"
        echo "  Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
        missing=$((missing + 1))
    fi

    # Check for nvm (Node.js)
    if [[ -d "$HOME/.nvm" ]] || [[ -n "${NVM_DIR:-}" ]]; then
        echo "✓ nvm: Found at ${NVM_DIR:-$HOME/.nvm}"
    else
        echo "✗ nvm: NOT FOUND"
        echo "  Install: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
        missing=$((missing + 1))
    fi

    # Check for Maven (Java build tool)
    if [[ -f "$HOME/.sdkman/bin/sdkman-init.sh" ]]; then
        set +u  # Temporarily disable to source SDKMAN
        source "$HOME/.sdkman/bin/sdkman-init.sh"
        set -u
        if command -v mvn &> /dev/null; then
            echo "✓ mvn: $(mvn --version | head -n1)"
        else
            echo "✗ mvn: NOT FOUND"
            echo "  Install via SDKMAN: sdk install maven"
            missing=$((missing + 1))
        fi
    else
        echo "✗ mvn: NOT FOUND (SDKMAN not found)"
        missing=$((missing + 1))
    fi

    # Check for Go
    if command -v go &> /dev/null; then
        echo "✓ go: $(go version)"
    else
        echo "✗ go: NOT FOUND"
        echo "  Install: https://go.dev/doc/install"
        missing=$((missing + 1))
    fi

    echo ""
    if [[ $missing -eq 0 ]]; then
        echo "All prerequisites satisfied!"
        exit 0
    else
        echo "Missing $missing prerequisite(s). Please install the missing tools."
        exit 1
    fi

# Run all experiments sequentially
all-experiments: rust-experiment java-experiment python-experiment node-experiment go-experiment
    @echo ""
    @echo "All experiments completed!"
    @echo "Results written to:"
    @echo "  - rust/results.json"
    @echo "  - java/results.json"
    @echo "  - python/results.json"
    @echo "  - node/results.json"
    @echo "  - go/results.json"

# Run Rust experiment
rust-experiment:
    @echo "Running Rust experiment..."
    cd rust && cargo run --release
    @echo "Rust experiment complete: rust/results.json"

# Run Rust experiment on a single crate
rust-experiment-crate crate_name:
    @echo "Running Rust experiment for {{ crate_name }}..."
    cd rust && cargo run --release -- {{ crate_name }}
    @echo "Rust experiment complete: rust/result-{{ crate_name }}.json"

# Run Java experiment
java-experiment:
    @echo "Running Java experiment..."
    cd java && mvn -q compile exec:java
    @echo "Java experiment complete: java/results.json"

# Run Java experiment on a single package
java-experiment-package package_coordinate:
    @echo "Running Java experiment for {{ package_coordinate }}..."
    cd java && mvn -q compile exec:java -Dexec.args='{{ package_coordinate }}'
    @echo "Java experiment complete: java/result-{{ package_coordinate }}.json"

# Run Python experiment
python-experiment:
    @echo "Running Python experiment..."
    cd python && uv run experiment.py
    @echo "Python experiment complete: python/results.json"

# Run Node.js experiment
node-experiment:
    @echo "Running Node.js experiment..."
    cd node && bash -c "source ~/.config/nvm/nvm.sh && node experiment.js"
    @echo "Node.js experiment complete: node/results.json"

# Run Go experiment
go-experiment:
    @echo "Running Go experiment..."
    cd go && go run experiment.go
    @echo "Go experiment complete: go/results.json"

# Run Go experiment on a single package
go-experiment-package package_name:
    @echo "Running Go experiment for {{ package_name }}..."
    cd go && go run experiment.go {{ package_name }}
    @echo "Go experiment complete: go/result-{{ package_name }}.json"

# Visualize Rust results (pass 'show' to display plot window)
visualize-rust show='':
    @echo "Generating Rust compatibility visualizations..."
    uv run visualize-rust.py {{ if show == 'show' { '--show' } else { '' } }}
    cp compatibility-timeline-rust.png docs/assets/

# Visualize Java results (pass 'show' to display plot window)
visualize-java show='':
    @echo "Generating Java compatibility visualizations..."
    uv run visualize-java.py {{ if show == 'show' { '--show' } else { '' } }}

# Visualize Node.js results (pass 'show' to display plot window)
visualize-node show='':
    @echo "Generating Node.js compatibility visualizations..."
    uv run visualize-node.py {{ if show == 'show' { '--show' } else { '' } }}

# Visualize Go results (pass 'show' to display plot window)
visualize-go show='':
    @echo "Generating Go compatibility visualizations..."
    uv run visualize-go.py {{ if show == 'show' { '--show' } else { '' } }}
    cp compatibility-timeline-go.png docs/assets/

# Visualize all language results (cross-language comparison)
visualize-all show='':
    @echo "Generating cross-language comparison..."
    @echo "TODO: Create visualize-all.py"

# Generate all visualizations (pass 'show' to display plot windows)
visualize show='': (visualize-rust show) (visualize-java show) (visualize-node show) (visualize-go show)
    @echo "All visualizations generated!"

# Serve the impress.js presentation on localhost:8000
serve-presentation:
    @echo "Starting presentation server on http://localhost:8000"
    @echo "Press Ctrl+C to stop"
    cd docs && python3 -m http.server 8000

# Open the presentation in the default browser
open-presentation:
    @echo "Opening presentation in browser..."
    xdg-open http://localhost:8000 || open http://localhost:8000 || echo "Please manually open http://localhost:8000"

# Clean all results and generated files
clean: clean-rust clean-java clean-python clean-node clean-go clean-visualizations
    @echo "All artifacts cleaned!"

# Clean Rust artifacts
clean-rust:
    @echo "Cleaning Rust artifacts..."
    rm -f rust/results.json
    rm -f rust/result-*.json
    rm -f rust/*.png

# Clean Java artifacts
clean-java:
    @echo "Cleaning Java artifacts..."
    rm -f java/results.json
    rm -f java/result-*.json
    rm -f java/*.png
    rm -rf java/target/

# Clean Python artifacts
clean-python:
    @echo "Cleaning Python artifacts..."
    rm -f python/results.json
    rm -rf venv/
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean Node.js artifacts
clean-node:
    @echo "Cleaning Node.js artifacts..."
    rm -f node/results.json

# Clean Go artifacts
clean-go:
    @echo "Cleaning Go artifacts..."
    rm -f go/results.json
    rm -f go/result-*.json
    rm -f go/*.png

# Clean visualization outputs
clean-visualizations:
    @echo "Cleaning visualization outputs..."
    rm -f *.png

# Validate all results.json files exist and are valid JSON
validate-results:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Validating experiment results..."
    echo ""

    valid=0
    invalid=0

    for result in rust/results.json java/results.json python/results.json node/results.json go/results.json; do
        if [[ -f "$result" ]]; then
            if python3 -m json.tool "$result" > /dev/null 2>&1; then
                echo "✓ $result: Valid JSON"
                valid=$((valid + 1))
            else
                echo "✗ $result: Invalid JSON"
                invalid=$((invalid + 1))
            fi
        else
            echo "✗ $result: Not found"
            invalid=$((invalid + 1))
        fi
    done

    echo ""
    echo "Results: $valid valid, $invalid invalid/missing"
    [[ $invalid -eq 0 ]] && exit 0 || exit 1

# List installed toolchain versions
list-versions:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Installed toolchain versions:"
    echo ""

    # Rust
    if command -v rustup &> /dev/null; then
        echo "Rust toolchains (rustup):"
        rustup toolchain list | head -n 5
        echo ""
    fi

    # Java
    if [[ -f "$HOME/.sdkman/bin/sdkman-init.sh" ]]; then
        echo "Java versions (sdkman):"
        bash -c "source ~/.sdkman/bin/sdkman-init.sh && sdk list java | grep installed | head -n 5"
        echo ""
    fi

    # Python
    if command -v uv &> /dev/null; then
        echo "Python versions (uv):"
        uv python list | head -n 5
        echo ""
    fi

    # Node.js
    if [[ -d "$HOME/.nvm" ]]; then
        echo "Node.js versions (nvm):"
        bash -c "source ~/.nvm/nvm.sh && nvm list | head -n 5"
        echo ""
    fi

    # Go
    if command -v go &> /dev/null; then
        echo "Go versions:"
        go version
        echo ""
    fi
