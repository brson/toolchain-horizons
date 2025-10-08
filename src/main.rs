use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;
use std::process::Command;
use tempfile::TempDir;

/// List of crates to test.
const CRATES: &[&str] = &[
    "bitflags",
    "byteorder",
    "cfg-if",
    "futures",
    "log",
    "num_cpus",
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
    for crate_name in CRATES {
        println!("\n=== Testing {} ===", crate_name);
        match test_crate(crate_name) {
            Ok(result) => {
                println!("{}: oldest={:?}, latest={:?}",
                    crate_name, result.oldest_compatible, result.latest_compatible);
                results.push(result);
            }
            Err(e) => {
                eprintln!("{} failed: {}", crate_name, e);
                results.push(ExperimentResult {
                    crate_name: crate_name.to_string(),
                    dependency_spec: format!("\"{}\"", get_version_spec(crate_name)),
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
edition = "2021"

[dependencies]
"#;
    fs::write(project_path.join("Cargo.toml"), cargo_toml)?;

    // Create src/lib.rs.
    fs::create_dir(project_path.join("src"))?;
    fs::write(project_path.join("src/lib.rs"), "// Control case with no dependencies\n")?;

    let versions = get_rust_versions()?;
    let oldest = find_oldest_compatible(&versions, project_path)?;
    let latest = versions.last().cloned();

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
fn test_crate(crate_name: &str) -> Result<ExperimentResult, Box<dyn std::error::Error>> {
    let temp_dir = TempDir::new()?;
    let project_path = temp_dir.path();

    let version_spec = get_version_spec(crate_name);

    // Create Cargo.toml.
    let cargo_toml = format!(
        r#"[package]
name = "test-{}"
version = "0.1.0"
edition = "2021"

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

    let versions = get_rust_versions()?;
    let oldest = find_oldest_compatible(&versions, project_path)?;
    let latest = versions.last().cloned();

    Ok(ExperimentResult {
        crate_name: crate_name.to_string(),
        dependency_spec: version_spec,
        resolved_version: Some(resolved_version),
        oldest_compatible: oldest,
        latest_compatible: latest,
        error: None,
    })
}

/// Get the version spec for a crate (major.minor format).
fn get_version_spec(crate_name: &str) -> String {
    // For most crates, use the major version.
    // Some special cases where we want to be more specific.
    match crate_name {
        "extension-trait" => "1.0".to_string(),
        _ => {
            // We'll try to fetch the latest version and use major.minor.
            // For now, use common patterns.
            "1".to_string()
        }
    }
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

/// Get list of Rust versions to test.
fn get_rust_versions() -> Result<Vec<String>, Box<dyn std::error::Error>> {
    // For now, return a curated list of important versions.
    // In a full implementation, we'd fetch from rustup or parse release data.
    Ok(vec![
        "1.0.0".to_string(),
        "1.10.0".to_string(),
        "1.20.0".to_string(),
        "1.30.0".to_string(),
        "1.40.0".to_string(),
        "1.50.0".to_string(),
        "1.60.0".to_string(),
        "1.70.0".to_string(),
        "1.80.0".to_string(),
        "1.85.0".to_string(),
    ])
}

/// Find the oldest compatible Rust version using binary search.
fn find_oldest_compatible(
    versions: &[String],
    project_path: &Path,
) -> Result<Option<String>, Box<dyn std::error::Error>> {
    let mut left = 0;
    let mut right = versions.len();
    let mut oldest = None;

    while left < right {
        let mid = left + (right - left) / 2;
        let version = &versions[mid];

        println!("  Testing Rust {}", version);

        if test_rust_version(project_path, version)? {
            oldest = Some(version.clone());
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
