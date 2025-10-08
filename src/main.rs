use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::process::Command;
use tempfile::TempDir;

/// List of crates to test (name, version).
///
/// It should be the latest major version.
///
/// Only put the major version here (for >= 1.0),
/// or major.minor (for <= 1.0), to give a range of resolution options.
const CRATES: &[(&str, &str)] = &[
    ("anyhow", "1"),
    ("backtrace", "0.3"),
    ("bitflags", "1"),
    ("byteorder", "1"),
    ("cfg-if", "1"),
    ("chrono", "0.4"),
    ("crossbeam", "0.8"),
    ("env_logger", "0.11"),
    ("extension-trait", "1.0"),
    ("futures", "0.3"),
    ("hex", "0.4"),
    ("itertools", "0.13"),
    ("libc", "0.2"),
    ("log", "0.4"),
    ("mime", "0.3"),
    ("num_cpus", "1"),
    ("rand", "0.8"),
    ("rayon", "1"),
    ("regex", "1"),
    ("serde", "1"),
    ("semver", "1"),
    ("socket2", "0.5"),
    ("syn", "2"),
    ("tempfile", "3"),
    ("thiserror", "1"),
    ("toml", "0.8"),
    ("unicode-segmentation", "1"),
    ("url", "2"),
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
    println!("Starting dependency toolchain compatibility experiment");
    println!("Testing {} crates", CRATES.len());

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

/// Test the control case with no dependencies.
fn test_control_case() -> Result<ExperimentResult, Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let project_path = temp_dir.path();

    // Create a minimal Cargo.toml with no dependencies.
    let cargo_toml = r#"[package]
name = "control"
version = "0.1.0"
edition = "2018"

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
edition = "2018"

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
#[allow(unused_imports)]
use {};
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

    // Try to check the project.
    let check_output = Command::new("cargo")
        .arg(&format!("+{}", version))
        .arg("check")
        .current_dir(project_path)
        .output()?;

    Ok(check_output.status.success())
}
