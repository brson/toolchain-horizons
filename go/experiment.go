package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Package represents a Go package to test.
type Package struct {
	ImportPath string
	Version    string
}

// List of packages to test (import path, version).
//
// Using latest major versions to allow the resolver flexibility.
var packages = []Package{
	// Testing with just 3 packages first.
	{"github.com/stretchr/testify", "v1.10"},
	{"github.com/google/uuid", "v1.6"},
	{"github.com/pkg/errors", "v0.9"},
	// {"golang.org/x/sync", "v0.10"},
	// {"golang.org/x/time", "v0.8"},
	// {"github.com/gorilla/mux", "v1.8"},
	// {"gopkg.in/yaml.v3", "v3.0"},
	// {"github.com/spf13/cobra", "v1.8"},
	// {"go.uber.org/zap", "v1.27"},
	// {"github.com/sirupsen/logrus", "v1.9"},
}

// Go versions to test.
// Starting from 1.19 (earlier versions harder to work with).
var goVersions = []string{
	"1.19.0", "1.20.0", "1.21.0", "1.22.0", "1.23.0",
}

// ExperimentResult holds results for a single package test.
type ExperimentResult struct {
	PackageName       string  `json:"package_name"`
	VersionSpec       string  `json:"version_spec"`
	ResolvedVersion   *string `json:"resolved_version"`
	OldestCompatible  *string `json:"oldest_compatible"`
	LatestCompatible  *string `json:"latest_compatible"`
	Error             *string `json:"error"`
}

func main() {
	fmt.Println("Starting dependency toolchain compatibility experiment")
	fmt.Printf("Testing %d packages\n", len(packages))

	var results []ExperimentResult

	// First, test the control case (no dependencies).
	fmt.Println("\n=== Testing control case (no dependencies) ===")
	result, err := testControlCase()
	if err != nil {
		fmt.Printf("Control case failed: %v\n", err)
	} else {
		fmt.Printf("Control: oldest=%v, latest=%v\n",
			ptrStr(result.OldestCompatible), ptrStr(result.LatestCompatible))
		results = append(results, result)
	}

	// Test each package.
	for _, pkg := range packages {
		fmt.Printf("\n=== Testing %s ===\n", pkg.ImportPath)
		result, err := testPackage(pkg)
		if err != nil {
			fmt.Printf("%s failed: %v\n", pkg.ImportPath, err)
			errMsg := err.Error()
			results = append(results, ExperimentResult{
				PackageName:      pkg.ImportPath,
				VersionSpec:      pkg.Version,
				ResolvedVersion:  nil,
				OldestCompatible: nil,
				LatestCompatible: nil,
				Error:            &errMsg,
			})
		} else {
			fmt.Printf("%s: oldest=%v, latest=%v\n",
				pkg.ImportPath, ptrStr(result.OldestCompatible), ptrStr(result.LatestCompatible))
			results = append(results, result)
		}
	}

	// Write results.
	data, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Printf("Failed to marshal results: %v\n", err)
		os.Exit(1)
	}

	if err := os.WriteFile("results.json", data, 0644); err != nil {
		fmt.Printf("Failed to write results: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("\n=== Results written to results.json ===")
}

// testControlCase tests the control case with no dependencies.
func testControlCase() (ExperimentResult, error) {
	result := ExperimentResult{
		PackageName: "CONTROL",
		VersionSpec: "none",
	}

	oldest := findOldestCompatible("", "")
	result.OldestCompatible = oldest
	latest := goVersions[len(goVersions)-1]
	result.LatestCompatible = &latest

	return result, nil
}

// testPackage tests a single package.
func testPackage(pkg Package) (ExperimentResult, error) {
	result := ExperimentResult{
		PackageName: pkg.ImportPath,
		VersionSpec: pkg.Version,
	}

	// Get resolved version with latest Go.
	resolved, err := getResolvedVersion(pkg)
	if err != nil {
		return result, err
	}
	result.ResolvedVersion = &resolved

	// Find oldest compatible version.
	oldest := findOldestCompatible(pkg.ImportPath, pkg.Version)
	result.OldestCompatible = oldest
	latest := goVersions[len(goVersions)-1]
	result.LatestCompatible = &latest

	return result, nil
}

// getResolvedVersion gets the resolved version of a package with the latest Go.
func getResolvedVersion(pkg Package) (string, error) {
	tmpDir, err := os.MkdirTemp("", "go-exp-*")
	if err != nil {
		return "", err
	}
	defer os.RemoveAll(tmpDir)

	// Ensure latest Go version is installed.
	latestVer := goVersions[len(goVersions)-1]
	if !ensureGoInstalled(latestVer) {
		return "", fmt.Errorf("failed to install Go %s", latestVer)
	}

	// Create go.mod.
	modContent := fmt.Sprintf("module test\n\ngo %s\n\nrequire %s %s\n",
		latestVer[:4], pkg.ImportPath, pkg.Version)
	if err := os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(modContent), 0644); err != nil {
		return "", err
	}

	// Create main.go with import.
	mainContent := fmt.Sprintf("package main\n\nimport _ \"%s\"\n\nfunc main() {}\n", pkg.ImportPath)
	if err := os.WriteFile(filepath.Join(tmpDir, "main.go"), []byte(mainContent), 0644); err != nil {
		return "", err
	}

	// Run go mod download.
	goCmd := fmt.Sprintf("go%s", latestVer)
	cmd := exec.Command(goCmd, "mod", "download")
	cmd.Dir = tmpDir
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("go mod download failed: %w", err)
	}

	// Parse go.mod to get resolved version.
	modData, err := os.ReadFile(filepath.Join(tmpDir, "go.mod"))
	if err != nil {
		return "", err
	}

	lines := strings.Split(string(modData), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, pkg.ImportPath) {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				return parts[1], nil
			}
		}
	}

	return "", fmt.Errorf("could not find resolved version")
}

// findOldestCompatible finds the oldest compatible Go version using binary search.
func findOldestCompatible(importPath, version string) *string {
	left := 0
	right := len(goVersions)
	var oldest *string

	for left < right {
		mid := left + (right-left)/2
		ver := goVersions[mid]

		fmt.Printf("  Testing Go %s\n", ver)

		if testGoVersion(ver, importPath, version) {
			oldest = &ver
			right = mid
		} else {
			left = mid + 1
		}
	}

	return oldest
}

// testGoVersion tests if a package works with a specific Go version.
func testGoVersion(goVersion, importPath, version string) bool {
	// Ensure Go version is installed.
	if !ensureGoInstalled(goVersion) {
		return false
	}

	tmpDir, err := os.MkdirTemp("", "go-exp-*")
	if err != nil {
		return false
	}
	defer os.RemoveAll(tmpDir)

	// Create go.mod.
	var modContent string
	if importPath == "" {
		// Control case.
		modContent = fmt.Sprintf("module test\n\ngo %s\n", goVersion[:4])
	} else {
		modContent = fmt.Sprintf("module test\n\ngo %s\n\nrequire %s %s\n",
			goVersion[:4], importPath, version)
	}

	if err := os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(modContent), 0644); err != nil {
		return false
	}

	// Create main.go.
	var mainContent string
	if importPath == "" {
		// Control case.
		mainContent = "package main\n\nfunc main() {}\n"
	} else {
		mainContent = fmt.Sprintf("package main\n\nimport _ \"%s\"\n\nfunc main() {}\n", importPath)
	}

	if err := os.WriteFile(filepath.Join(tmpDir, "main.go"), []byte(mainContent), 0644); err != nil {
		return false
	}

	// Run go build (this does type checking).
	goCmd := fmt.Sprintf("go%s", goVersion)
	cmd := exec.Command(goCmd, "build")
	cmd.Dir = tmpDir
	if err := cmd.Run(); err != nil {
		return false
	}

	return true
}

// ensureGoInstalled ensures a Go version is installed.
func ensureGoInstalled(version string) bool {
	goCmd := fmt.Sprintf("go%s", version)

	// Add GOPATH/bin to PATH if not already there.
	gopath := os.Getenv("GOPATH")
	if gopath == "" {
		gopath = filepath.Join(os.Getenv("HOME"), "go")
	}
	gopathBin := filepath.Join(gopath, "bin")
	path := os.Getenv("PATH")
	if !strings.Contains(path, gopathBin) {
		os.Setenv("PATH", gopathBin+":"+path)
	}

	// Check if already installed.
	if _, err := exec.LookPath(goCmd); err == nil {
		return true
	}

	// Install the version installer.
	dlPath := fmt.Sprintf("golang.org/dl/go%s@latest", version)
	cmd := exec.Command("go", "install", dlPath)
	if err := cmd.Run(); err != nil {
		fmt.Printf("    Failed to install %s installer: %v\n", version, err)
		return false
	}

	// Download the actual version.
	cmd = exec.Command(goCmd, "download")
	if err := cmd.Run(); err != nil {
		fmt.Printf("    Failed to download %s: %v\n", version, err)
		return false
	}

	return true
}

// ptrStr dereferences a string pointer, returning "nil" if nil.
func ptrStr(s *string) string {
	if s == nil {
		return "nil"
	}
	return *s
}
