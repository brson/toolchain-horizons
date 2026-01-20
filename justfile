default:
    @just --list

rust-experiment:
    @echo "Running Rust experiment..."
    cd rust && cargo run --release
    @echo "Rust experiment complete: rust/results.json"

rust-experiment-crate crate_name:
    @echo "Running Rust experiment for {{ crate_name }}..."
    cd rust && cargo run --release -- {{ crate_name }}
    @echo "Rust experiment complete: rust/result-{{ crate_name }}.json"

visualize-rust show='':
    @echo "Generating Rust compatibility visualizations..."
    uv run visualize-rust.py {{ if show == 'show' { '--show' } else { '' } }}

