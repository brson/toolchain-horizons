#!/usr/bin/env python3
"""
Dependency toolchain compatibility experiment for Python.

This experiment tests how adding a single dependency affects the range
of Python versions that can successfully install and import that dependency.

Uses uv for both Python version management and package installation.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# List of packages to test (name, version spec).
#
# Using major version specs to allow the resolver flexibility.
PACKAGES = [
    ("certifi", ">=2024.0"),
    ("charset-normalizer", ">=3.0"),
    ("click", ">=8.0"),
    ("idna", ">=3.0"),
    ("jinja2", ">=3.0"),
    ("markupsafe", ">=2.0"),
    ("numpy", ">=1.26"),
    ("packaging", ">=24.0"),
    ("pillow", ">=10.0"),
    ("platformdirs", ">=4.0"),
    ("pluggy", ">=1.0"),
    ("pytest", ">=8.0"),
    ("python-dateutil", ">=2.8"),
    ("pytz", ">=2024.1"),
    ("pyyaml", ">=6.0"),
    ("requests", ">=2.32"),
    ("setuptools", ">=75.0"),
    ("six", ">=1.16"),
    ("urllib3", ">=2.0"),
]

# Python versions to test.
# Starting from 3.8 (older versions are EOL and harder to get).
PYTHON_VERSIONS = [
    "3.8", "3.9", "3.10", "3.11", "3.12", "3.13",
]


class ExperimentResult:
    """Results for a single package test."""

    def __init__(self, package_name: str, version_spec: str):
        self.package_name = package_name
        self.version_spec = version_spec
        self.resolved_version: Optional[str] = None
        self.oldest_compatible: Optional[str] = None
        self.latest_compatible: Optional[str] = None
        self.error: Optional[str] = None

    def to_dict(self):
        return {
            "package_name": self.package_name,
            "version_spec": self.version_spec,
            "resolved_version": self.resolved_version,
            "oldest_compatible": self.oldest_compatible,
            "latest_compatible": self.latest_compatible,
            "error": self.error,
        }


def main():
    print("Starting dependency toolchain compatibility experiment")
    print(f"Testing {len(PACKAGES)} packages")

    results = []

    # First, test the control case (no dependencies).
    print("\n=== Testing control case (no dependencies) ===")
    try:
        result = test_control_case()
        print(f"Control: oldest={result.oldest_compatible}, latest={result.latest_compatible}")
        results.append(result.to_dict())
    except Exception as e:
        print(f"Control case failed: {e}")

    # Test each package.
    for package_name, version_spec in PACKAGES:
        print(f"\n=== Testing {package_name} ===")
        try:
            result = test_package(package_name, version_spec)
            print(f"{package_name}: oldest={result.oldest_compatible}, latest={result.latest_compatible}")
            results.append(result.to_dict())
        except Exception as e:
            print(f"{package_name} failed: {e}")
            error_result = ExperimentResult(package_name, version_spec)
            error_result.error = str(e)
            results.append(error_result.to_dict())

    # Write results.
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n=== Results written to results.json ===")


def test_control_case() -> ExperimentResult:
    """Test the control case with no dependencies."""
    result = ExperimentResult("CONTROL", "none")

    oldest = find_oldest_compatible(None, None)
    result.oldest_compatible = oldest
    result.latest_compatible = PYTHON_VERSIONS[-1]

    return result


def test_package(package_name: str, version_spec: str) -> ExperimentResult:
    """Test a single package."""
    result = ExperimentResult(package_name, version_spec)

    # Get resolved version with latest Python.
    resolved = get_resolved_version(package_name, version_spec)
    result.resolved_version = resolved

    # Find oldest compatible version.
    oldest = find_oldest_compatible(package_name, version_spec)
    result.oldest_compatible = oldest
    result.latest_compatible = PYTHON_VERSIONS[-1]

    return result


def get_resolved_version(package_name: str, version_spec: str) -> Optional[str]:
    """Get the resolved version of a package with the latest Python."""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"

        # Ensure Python version is installed.
        python_version = PYTHON_VERSIONS[-1]
        ensure_python_installed(python_version)

        # Create venv with uv.
        try:
            subprocess.run(
                ["uv", "venv", "--python", python_version, str(venv_path)],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

        # Install package.
        try:
            subprocess.run(
                ["uv", "pip", "install", "--python", str(venv_path / "bin" / "python"),
                 f"{package_name}{version_spec}"],
                check=True,
                capture_output=True,
                timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

        # Get installed version.
        try:
            output = subprocess.run(
                ["uv", "pip", "show", "--python", str(venv_path / "bin" / "python"),
                 package_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in output.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

    return None


def find_oldest_compatible(
    package_name: Optional[str],
    version_spec: Optional[str]
) -> Optional[str]:
    """Find the oldest compatible Python version using binary search."""
    left = 0
    right = len(PYTHON_VERSIONS)
    oldest = None

    while left < right:
        mid = left + (right - left) // 2
        version = PYTHON_VERSIONS[mid]

        print(f"  Testing Python {version}")

        if test_python_version(version, package_name, version_spec):
            oldest = version
            right = mid
        else:
            left = mid + 1

    return oldest


def test_python_version(
    python_version: str,
    package_name: Optional[str],
    version_spec: Optional[str]
) -> bool:
    """Test if a package works with a specific Python version."""
    # Ensure Python version is installed.
    if not ensure_python_installed(python_version):
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"

        # Create venv with uv.
        try:
            subprocess.run(
                ["uv", "venv", "--python", python_version, str(venv_path)],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

        python_exe = venv_path / "bin" / "python"

        # If this is the control case, just verify Python works.
        if package_name is None:
            try:
                subprocess.run(
                    [str(python_exe), "-c", "print('Hello')"],
                    check=True,
                    capture_output=True,
                    timeout=10,
                )
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return False

        # Install package.
        try:
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python_exe),
                 f"{package_name}{version_spec}"],
                check=True,
                capture_output=True,
                timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

        # Try to import it.
        import_name = package_name.replace("-", "_")
        try:
            subprocess.run(
                [str(python_exe), "-c", f"import {import_name}"],
                check=True,
                capture_output=True,
                timeout=10,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


def ensure_python_installed(version: str) -> bool:
    """Ensure a Python version is installed via uv."""
    try:
        subprocess.run(
            ["uv", "python", "install", version],
            check=True,
            capture_output=True,
            timeout=300,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


if __name__ == "__main__":
    main()
