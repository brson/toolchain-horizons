use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::process::Command;
use tempfile::TempDir;

/// List of crates to test (name, version).
///
/// Top 100 crates by crates.io download count (excluding Windows-specific crates).
///
/// Only put the major version here (for >= 1.0),
/// or major.minor (for < 1.0), to give a range of resolution options.
const CRATES: &[(&str, &str)] = &[
    // Top 100 from crates.io by downloads (excluding windows-* platform crates)
    ("aho-corasick", "1"),
    ("ahash", "0.8"),
    ("anyhow", "1"),
    ("autocfg", "1"),
    ("backtrace", "0.3"),
    ("base64", "0.22"),
    ("bitflags", "2"),
    ("block-buffer", "0.11"),
    ("bytes", "1"),
    ("byteorder", "1"),
    ("cc", "1"),
    ("cfg-if", "1"),
    ("chrono", "0.4"),
    ("clap", "4"),
    ("clap_lex", "0.7"),
    ("crossbeam", "0.8"),
    ("crossbeam-utils", "0.8"),
    ("digest", "0.10"),
    ("either", "1"),
    ("env_logger", "0.11"),
    ("fastrand", "2"),
    ("fnv", "1"),
    ("futures", "0.3"),
    ("futures-channel", "0.3"),
    ("futures-core", "0.3"),
    ("futures-io", "0.3"),
    ("futures-sink", "0.3"),
    ("futures-task", "0.3"),
    ("futures-util", "0.3"),
    ("generic-array", "1"),
    ("getrandom", "0.3"),
    ("h2", "0.4"),
    ("hashbrown", "0.15"),
    ("heck", "0.5"),
    ("hex", "0.4"),
    ("http", "1"),
    ("http-body", "1"),
    ("hyper", "1"),
    ("idna", "1"),
    ("indexmap", "2"),
    ("itertools", "0.14"),
    ("itoa", "1"),
    ("lazy_static", "1"),
    ("libc", "0.2"),
    ("linux-raw-sys", "0.9"),
    ("lock_api", "0.4"),
    ("log", "0.4"),
    ("memchr", "2"),
    ("memoffset", "0.9"),
    ("mime", "0.3"),
    ("miniz_oxide", "0.8"),
    ("mio", "1"),
    ("num-traits", "0.2"),
    ("num_cpus", "1"),
    ("once_cell", "1"),
    ("parking_lot", "0.12"),
    ("parking_lot_core", "0.9"),
    ("percent-encoding", "2"),
    ("pin-project-lite", "0.2"),
    ("pin-utils", "0.1"),
    ("ppv-lite86", "0.2"),
    ("proc-macro2", "1"),
    ("quote", "1"),
    ("rand", "0.9"),
    ("rand_chacha", "0.9"),
    ("rand_core", "0.9"),
    ("rayon", "1"),
    ("regex", "1"),
    ("regex-automata", "0.4"),
    ("regex-syntax", "0.8"),
    ("rustix", "1"),
    ("rustls", "0.23"),
    ("ryu", "1"),
    ("scopeguard", "1"),
    ("semver", "1"),
    ("serde", "1"),
    ("serde_derive", "1"),
    ("serde_json", "1"),
    ("sha2", "0.10"),
    ("slab", "0.4"),
    ("smallvec", "1"),
    ("socket2", "0.6"),
    ("strsim", "0.11"),
    ("syn", "2"),
    ("tempfile", "3"),
    ("thiserror", "2"),
    ("time", "0.3"),
    ("tokio", "1"),
    ("tokio-util", "0.7"),
    ("toml", "0.9"),
    ("tracing", "0.1"),
    ("tracing-core", "0.1"),
    ("typenum", "1"),
    ("unicode-ident", "1"),
    ("unicode-segmentation", "1"),
    ("unicode-width", "0.2"),
    ("url", "2"),
    ("uuid", "1"),
    ("version_check", "0.9"),
    ("walkdir", "2"),
];

#[derive(Debug, Serialize, Deserialize)]
struct ExperimentResult {
    crate_name: String,
    dependency_spec: String,
    resolved_version: Option<String>,
    oldest_compatible: Option<String>,
    latest_compatible: Option<String>,
    error: Option<String>,
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    // Check if a specific crate was requested.
    let specific_crate = if args.len() > 1 {
        Some(args[1].as_str())
    } else {
        None
    };

    if let Some(crate_name) = specific_crate {
        println!("Testing single crate: {}", crate_name);
        run_single_crate_experiment(crate_name);
    } else {
        println!("Starting dependency toolchain compatibility experiment");
        println!("Testing {} crates", CRATES.len());
        run_full_experiment();
    }
}

/// Run the full experiment on all crates.
fn run_full_experiment() {
    let mut results = Vec::new();

    // First, test the control case (no dependencies).
    println!("\n=== Testing control case (no dependencies) ===");
    match test_control_case() {
        Ok(result) => {
            println!("Control: oldest={:?}, latest={:?}",
                result.oldest_compatible, result.latest_compatible);
            results.push(result);
        }
        Err(e) => {
            eprintln!("Control case failed: {}", e);
        }
    }

    // Test each crate.
    for (crate_name, version) in CRATES {
        println!("\n=== Testing {} ===", crate_name);
        match test_crate(crate_name, version) {
            Ok(result) => {
                println!("{}: oldest={:?}, latest={:?}",
                    crate_name, result.oldest_compatible, result.latest_compatible);
                results.push(result);
            }
            Err(e) => {
                eprintln!("{} failed: {}", crate_name, e);
                results.push(ExperimentResult {
                    crate_name: crate_name.to_string(),
                    dependency_spec: version.to_string(),
                    resolved_version: None,
                    oldest_compatible: None,
                    latest_compatible: None,
                    error: Some(e.to_string()),
                });
            }
        }
    }

    // Write results.
    let json = serde_json::to_string_pretty(&results).unwrap();
    fs::write("results.json", json).unwrap();
    println!("\n=== Results written to results.json ===");
}

/// Run experiment on a single crate.
fn run_single_crate_experiment(crate_name: &str) {
    // Find the crate in our list.
    let crate_entry = CRATES.iter().find(|(name, _)| *name == crate_name);

    let (version_spec, found_in_list) = match crate_entry {
        Some((_, version)) => (*version, true),
        None => {
            println!("Warning: '{}' not found in predefined list, using version '1'", crate_name);
            ("1", false)
        }
    };

    println!("\n=== Testing {} (version spec: {}) ===", crate_name, version_spec);

    match test_crate(crate_name, version_spec) {
        Ok(result) => {
            println!("\nResults for {}:", crate_name);
            println!("  Dependency spec: {}", result.dependency_spec);
            println!("  Resolved version: {}", result.resolved_version.as_ref().unwrap_or(&"N/A".to_string()));
            println!("  Oldest compatible: {}", result.oldest_compatible.as_ref().unwrap_or(&"N/A".to_string()));
            println!("  Latest compatible: {}", result.latest_compatible.as_ref().unwrap_or(&"N/A".to_string()));

            // Write single result to a file.
            let json = serde_json::to_string_pretty(&result).unwrap();
            let filename = format!("result-{}.json", crate_name);
            fs::write(&filename, json).unwrap();
            println!("\n=== Result written to {} ===", filename);

            if !found_in_list {
                println!("\nNote: This crate was not in the predefined list.");
                println!("To add it permanently, update the CRATES constant in src/main.rs");
            }
        }
        Err(e) => {
            eprintln!("\nFailed to test {}: {}", crate_name, e);
            std::process::exit(1);
        }
    }
}

/// Test the control case with no dependencies.
fn test_control_case() -> Result<ExperimentResult, Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let project_path = temp_dir.path();

    // Create a minimal Cargo.toml with no dependencies.
    let cargo_toml = r#"[package]
name = "control"
version = "0.1.0"
edition = "2015"

[dependencies]
"#;
    fs::write(project_path.join("Cargo.toml"), cargo_toml)?;

    // Create src/lib.rs.
    fs::create_dir(project_path.join("src"))?;
    fs::write(project_path.join("src/lib.rs"), "// Control case with no dependencies\n")?;

    let oldest = find_oldest_compatible(project_path)?;
    let latest = RUST_VERSIONS.last().map(|s| s.to_string());

    Ok(ExperimentResult {
        crate_name: "CONTROL".to_string(),
        dependency_spec: "none".to_string(),
        resolved_version: None,
        oldest_compatible: oldest,
        latest_compatible: latest,
        error: None,
    })
}

/// Test a single crate.
fn test_crate(crate_name: &str, version_spec: &str) -> Result<ExperimentResult, Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let project_path = temp_dir.path();

    // Create Cargo.toml.
    let cargo_toml = format!(
        r#"[package]
name = "test-{}"
version = "0.1.0"
edition = "2015"

[dependencies]
{} = "{}"
"#,
        crate_name, crate_name, version_spec
    );
    fs::write(project_path.join("Cargo.toml"), cargo_toml)?;

    // Create src/lib.rs with a basic usage.
    fs::create_dir(project_path.join("src"))?;
    let lib_rs = generate_lib_rs(crate_name);
    fs::write(project_path.join("src/lib.rs"), lib_rs)?;

    // Get resolved version with latest stable.
    let resolved_version = get_resolved_version(project_path, crate_name)?;

    let oldest = find_oldest_compatible(project_path)?;
    let latest = RUST_VERSIONS.last().map(|s| s.to_string());

    Ok(ExperimentResult {
        crate_name: crate_name.to_string(),
        dependency_spec: version_spec.to_string(),
        resolved_version: Some(resolved_version),
        oldest_compatible: oldest,
        latest_compatible: latest,
        error: None,
    })
}

/// Generate lib.rs content that uses the crate.
fn generate_lib_rs(crate_name: &str) -> String {
    let safe_name = crate_name.replace('-', "_");
    format!(
        r#"// Test usage of {}
#[allow(unused_extern_crates)]
extern crate {};
"#,
        crate_name, safe_name
    )
}

/// Get the resolved version from Cargo.lock.
fn get_resolved_version(
    project_path: &Path,
    crate_name: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    // Run cargo check to generate Cargo.lock.
    let output = Command::new("cargo")
        .arg("check")
        .current_dir(project_path)
        .output()?;

    if !output.status.success() {
        return Err("Failed to run cargo check".into());
    }

    // Parse Cargo.lock to find the resolved version.
    let lock_content = fs::read_to_string(project_path.join("Cargo.lock"))?;
    let mut lines = lock_content.lines();
    let mut found_package = false;

    while let Some(line) = lines.next() {
        if line.starts_with("[[package]]") {
            found_package = false;
        }

        if line.starts_with("name = ") && line.contains(&format!("\"{}\"", crate_name)) {
            found_package = true;
        }

        if found_package && line.starts_with("version = ") {
            let version = line
                .trim()
                .trim_start_matches("version = ")
                .trim_matches('"')
                .to_string();
            return Ok(version);
        }
    }

    Err("Could not find version in Cargo.lock".into())
}

/// All stable Rust releases (latest point releases only).
const RUST_VERSIONS: &[&str] = &[
    "1.0.0", "1.1.0", "1.2.0", "1.3.0", "1.4.0", "1.5.0", "1.6.0", "1.7.0", "1.8.0", "1.9.0",
    "1.10.0", "1.11.0", "1.12.1", "1.13.0", "1.14.0", "1.15.1", "1.16.0", "1.17.0", "1.18.0", "1.19.0",
    "1.20.0", "1.21.0", "1.22.1", "1.23.0", "1.24.1", "1.25.0", "1.26.2", "1.27.2", "1.28.0", "1.29.2",
    "1.30.1", "1.31.1", "1.32.0", "1.33.0", "1.34.2", "1.35.0", "1.36.0", "1.37.0", "1.38.0", "1.39.0",
    "1.40.0", "1.41.1", "1.42.0", "1.43.1", "1.44.1", "1.45.2", "1.46.0", "1.47.0", "1.48.0", "1.49.0",
    "1.50.0", "1.51.0", "1.52.1", "1.53.0", "1.54.0", "1.55.0", "1.56.1", "1.57.0", "1.58.1", "1.59.0",
    "1.60.0", "1.61.0", "1.62.1", "1.63.0", "1.64.0", "1.65.0", "1.66.1", "1.67.1", "1.68.2", "1.69.0",
    "1.70.0", "1.71.1", "1.72.1", "1.73.0", "1.74.1", "1.75.0", "1.76.0", "1.77.2", "1.78.0", "1.79.0",
    "1.80.1", "1.81.0", "1.82.0", "1.83.0", "1.84.1", "1.85.1", "1.86.0", "1.87.0", "1.88.0", "1.89.0",
    "1.90.0",
];

/// Find the oldest compatible Rust version using binary search.
fn find_oldest_compatible(
    project_path: &Path,
) -> Result<Option<String>, Box<dyn std::error::Error>> {
    let mut left = 0;
    let mut right = RUST_VERSIONS.len();
    let mut oldest = None;

    while left < right {
        let mid = left + (right - left) / 2;
        let version = RUST_VERSIONS[mid];

        println!("  Testing Rust {}", version);

        if test_rust_version(project_path, version)? {
            oldest = Some(version.to_string());
            right = mid;
        } else {
            left = mid + 1;
        }
    }

    Ok(oldest)
}

/// Compare two version strings (e.g., "1.15.1" < "1.16.0").
fn version_less_than(a: &str, b: &str) -> bool {
    let parse = |v: &str| -> (u32, u32, u32) {
        let parts: Vec<u32> = v.split('.').filter_map(|s| s.parse().ok()).collect();
        (
            parts.get(0).copied().unwrap_or(0),
            parts.get(1).copied().unwrap_or(0),
            parts.get(2).copied().unwrap_or(0),
        )
    };
    parse(a) < parse(b)
}

/// Test if a project compiles with a specific Rust version.
fn test_rust_version(project_path: &Path, version: &str) -> Result<bool, Box<dyn std::error::Error>> {
    // First, ensure the toolchain is installed.
    let install_output = Command::new("rustup")
        .args(&["toolchain", "install", version])
        .output()?;

    if !install_output.status.success() {
        println!("    Failed to install {}", version);
        return Ok(false);
    }

    // Remove Cargo.lock to allow version to generate its own.
    let lock_path = project_path.join("Cargo.lock");
    if lock_path.exists() {
        fs::remove_file(lock_path)?;
    }

    // Use `cargo build` for versions before 1.16.0 (when `cargo check` was added).
    let subcommand = if version_less_than(version, "1.16.0") {
        "build"
    } else {
        "check"
    };

    let check_output = Command::new("cargo")
        .arg(&format!("+{}", version))
        .arg(subcommand)
        .current_dir(project_path)
        .output()?;

    Ok(check_output.status.success())
}
