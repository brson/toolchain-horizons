package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Package represents a Go module to test.
type Package struct {
	ImportPath   string
	VersionSpec  string
	ImportExample string // Actual import to use in test code
}

// List of popular Go packages to test.
// Note: For v2+ modules, the module path includes the version suffix.
var packages = []Package{
	{"github.com/gorilla/mux", "v1", "github.com/gorilla/mux"},
	{"github.com/gin-gonic/gin", "v1", "github.com/gin-gonic/gin"},
	{"github.com/stretchr/testify", "v1", "github.com/stretchr/testify/assert"},
	{"github.com/spf13/cobra", "v1", "github.com/spf13/cobra"},
	{"github.com/urfave/cli/v2", "v2", "github.com/urfave/cli/v2"},
	{"github.com/sirupsen/logrus", "v1", "github.com/sirupsen/logrus"},
	{"go.uber.org/zap", "v1", "go.uber.org/zap"},
	{"github.com/go-resty/resty/v2", "v2", "github.com/go-resty/resty/v2"},
	{"gopkg.in/yaml.v3", "v3", "gopkg.in/yaml.v3"},
	{"github.com/lib/pq", "v1", "github.com/lib/pq"},
	{"github.com/go-sql-driver/mysql", "v1", "github.com/go-sql-driver/mysql"},
	{"github.com/google/uuid", "v1", "github.com/google/uuid"},
	{"github.com/pkg/errors", "v0.9", "github.com/pkg/errors"},
	{"github.com/hashicorp/go-multierror", "v1", "github.com/hashicorp/go-multierror"},
	{"github.com/prometheus/client_golang", "v1", "github.com/prometheus/client_golang/prometheus"},
	{"github.com/gorilla/websocket", "v1", "github.com/gorilla/websocket"},
	{"github.com/julienschmidt/httprouter", "v1", "github.com/julienschmidt/httprouter"},
	{"github.com/dgrijalva/jwt-go", "v3", "github.com/dgrijalva/jwt-go"},
	{"golang.org/x/sync", "v0.10", "golang.org/x/sync/errgroup"},
	{"golang.org/x/crypto", "v0.31", "golang.org/x/crypto/bcrypt"},
	{"github.com/go-chi/chi/v5", "v5", "github.com/go-chi/chi/v5"},
	{"github.com/labstack/echo/v4", "v4", "github.com/labstack/echo/v4"},
	{"github.com/gomodule/redigo", "v1", "github.com/gomodule/redigo/redis"},
	{"github.com/elastic/go-elasticsearch/v7", "v7", "github.com/elastic/go-elasticsearch/v7"},
	{"github.com/aws/aws-sdk-go", "v1", "github.com/aws/aws-sdk-go/aws"},
	{"google.golang.org/grpc", "v1", "google.golang.org/grpc"},
}

// Go versions to test.
// The golang.org/dl naming changed around 1.21 to include patch version.
var goVersions = []string{
	"1.13", "1.14", "1.15", "1.16", "1.17", "1.18",
	"1.19", "1.20", "1.21.0", "1.22.0", "1.23.0", "1.24.0",
}

// Get the Go binary path for a version.
func goBinPath(version string) string {
	gopath := os.Getenv("GOPATH")
	if gopath == "" {
		home, _ := os.UserHomeDir()
		gopath = filepath.Join(home, "go")
	}
	return filepath.Join(gopath, "bin", fmt.Sprintf("go%s", version))
}

// Check if a Go version wrapper is installed.
func goVersionInstalled(version string) bool {
	binPath := goBinPath(version)
	_, err := os.Stat(binPath)
	return err == nil
}

// Install a Go version wrapper via golang.org/dl.
func installGoWrapper(version string) error {
	dlPath := fmt.Sprintf("golang.org/dl/go%s@latest", version)
	cmd := exec.Command("go", "install", dlPath)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("install wrapper: %v: %s", err, output)
	}
	return nil
}

// Ensure a Go version is installed and downloaded.
func ensureGoVersion(version string) error {
	if !goVersionInstalled(version) {
		fmt.Printf("    Installing Go %s wrapper...\n", version)
		if err := installGoWrapper(version); err != nil {
			return err
		}
	}

	// Always try download - it's fast if already present.
	binPath := goBinPath(version)
	cmd := exec.Command(binPath, "download")
	cmd.Stdout = nil
	cmd.Stderr = nil
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("download SDK: %v", err)
	}

	return nil
}

// Update go.mod to use a specific Go version directive.
func updateGoModVersion(tmpDir, version string) error {
	goModPath := filepath.Join(tmpDir, "go.mod")
	content, err := os.ReadFile(goModPath)
	if err != nil {
		return err
	}

	lines := strings.Split(string(content), "\n")
	for i, line := range lines {
		if strings.HasPrefix(strings.TrimSpace(line), "go ") {
			lines[i] = fmt.Sprintf("go %s", version)
			break
		}
	}

	return os.WriteFile(goModPath, []byte(strings.Join(lines, "\n")), 0644)
}

// Test if a project compiles with a specific Go version.
func testGoVersion(tmpDir, version string) (bool, error) {
	// Ensure toolchain is installed and downloaded.
	if err := ensureGoVersion(version); err != nil {
		return false, err
	}

	binPath := goBinPath(version)

	// Clean go.sum to allow fresh resolution.
	os.Remove(filepath.Join(tmpDir, "go.sum"))

	// Update go.mod to match the version being tested.
	if err := updateGoModVersion(tmpDir, version); err != nil {
		return false, err
	}

	// Try mod tidy with this version.
	tidyCmd := exec.Command(binPath, "mod", "tidy")
	tidyCmd.Dir = tmpDir
	if _, err := tidyCmd.CombinedOutput(); err != nil {
		return false, nil
	}

	// Try build.
	buildCmd := exec.Command(binPath, "build", ".")
	buildCmd.Dir = tmpDir
	if err := buildCmd.Run(); err != nil {
		return false, nil
	}

	return true, nil
}

// ExperimentResult stores the result for a single package test.
type ExperimentResult struct {
	PackageName       string  `json:"package_name"`
	DependencySpec    string  `json:"dependency_spec"`
	ResolvedVersion   *string `json:"resolved_version"`
	OldestCompatible  *string `json:"oldest_compatible"`
	LatestCompatible  *string `json:"latest_compatible"`
	Error             *string `json:"error"`
}

func main() {
	args := os.Args[1:]

	if len(args) > 0 {
		// Single package mode
		packageName := args[0]
		fmt.Printf("Testing single package: %s\n", packageName)
		runSinglePackageExperiment(packageName)
	} else {
		// Full experiment mode
		fmt.Println("Starting Go dependency toolchain compatibility experiment")
		fmt.Printf("Testing %d packages\n", len(packages))
		runFullExperiment()
	}
}

func runFullExperiment() {
	results := []ExperimentResult{}

	// Test control case
	fmt.Println("\n=== Testing control case (no dependencies) ===")
	controlResult, err := testControlCase()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Control case failed: %v\n", err)
	} else {
		fmt.Printf("Control: oldest=%v, latest=%v\n",
			ptrString(controlResult.OldestCompatible),
			ptrString(controlResult.LatestCompatible))
		results = append(results, controlResult)
	}

	// Test each package
	for _, pkg := range packages {
		fmt.Printf("\n=== Testing %s ===\n", pkg.ImportPath)
		result, err := testPackage(pkg)
		if err != nil {
			fmt.Fprintf(os.Stderr, "%s failed: %v\n", pkg.ImportPath, err)
			errStr := err.Error()
			results = append(results, ExperimentResult{
				PackageName:    pkg.ImportPath,
				DependencySpec: pkg.VersionSpec,
				Error:          &errStr,
			})
		} else {
			fmt.Printf("%s: oldest=%v, latest=%v\n",
				pkg.ImportPath,
				ptrString(result.OldestCompatible),
				ptrString(result.LatestCompatible))
			results = append(results, result)
		}
	}

	// Write results
	jsonData, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to marshal results: %v\n", err)
		os.Exit(1)
	}

	err = os.WriteFile("results.json", jsonData, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to write results.json: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("\n=== Results written to results.json ===")
}

func runSinglePackageExperiment(packageName string) {
	// Find package in list
	var pkg *Package
	for i := range packages {
		if packages[i].ImportPath == packageName {
			pkg = &packages[i]
			break
		}
	}

	if pkg == nil {
		fmt.Printf("Warning: '%s' not found in predefined list\n", packageName)
		fmt.Println("Testing anyway with version spec 'v1'...")
		pkg = &Package{
			ImportPath:   packageName,
			VersionSpec:  "v1",
			ImportExample: packageName,
		}
	}

	fmt.Printf("\n=== Testing %s (version spec: %s) ===\n", pkg.ImportPath, pkg.VersionSpec)

	result, err := testPackage(*pkg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "\nFailed to test %s: %v\n", packageName, err)
		os.Exit(1)
	}

	fmt.Printf("\nResults for %s:\n", packageName)
	fmt.Printf("  Dependency spec: %s\n", result.DependencySpec)
	fmt.Printf("  Resolved version: %s\n", ptrString(result.ResolvedVersion))
	fmt.Printf("  Oldest compatible: %s\n", ptrString(result.OldestCompatible))
	fmt.Printf("  Latest compatible: %s\n", ptrString(result.LatestCompatible))

	// Write result to file
	jsonData, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to marshal result: %v\n", err)
		os.Exit(1)
	}

	filename := fmt.Sprintf("result-%s.json", filepath.Base(packageName))
	err = os.WriteFile(filename, jsonData, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to write %s: %v\n", filename, err)
		os.Exit(1)
	}

	fmt.Printf("\n=== Result written to %s ===\n", filename)
}

func testControlCase() (ExperimentResult, error) {
	tmpDir, err := os.MkdirTemp("", "go-exp-control-")
	if err != nil {
		return ExperimentResult{}, err
	}
	defer os.RemoveAll(tmpDir)

	// Create go.mod
	goMod := `module control

go 1.18
`
	err = os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(goMod), 0644)
	if err != nil {
		return ExperimentResult{}, err
	}

	// Create main.go
	mainGo := `package main

func main() {
	// Control case with no dependencies
}
`
	err = os.WriteFile(filepath.Join(tmpDir, "main.go"), []byte(mainGo), 0644)
	if err != nil {
		return ExperimentResult{}, err
	}

	oldest := findOldestCompatible(tmpDir, Package{})
	latest := stringPtr(goVersions[len(goVersions)-1])

	return ExperimentResult{
		PackageName:      "CONTROL",
		DependencySpec:   "none",
		OldestCompatible: oldest,
		LatestCompatible: latest,
	}, nil
}

func testPackage(pkg Package) (ExperimentResult, error) {
	tmpDir, err := os.MkdirTemp("", "go-exp-")
	if err != nil {
		return ExperimentResult{}, err
	}
	defer os.RemoveAll(tmpDir)

	// Create minimal go.mod without dependencies
	goMod := `module test

go 1.18
`
	err = os.WriteFile(filepath.Join(tmpDir, "go.mod"), []byte(goMod), 0644)
	if err != nil {
		return ExperimentResult{}, err
	}

	// Create main.go that imports the package
	mainGo := fmt.Sprintf(`package main

import (
	_ "%s"
)

func main() {
	// Import package to verify it compiles
}
`, pkg.ImportExample)

	err = os.WriteFile(filepath.Join(tmpDir, "main.go"), []byte(mainGo), 0644)
	if err != nil {
		return ExperimentResult{}, err
	}

	// Use go get to add the dependency with proper version resolution
	// This will automatically pick a version compatible with our Go version
	getCmd := exec.Command("go", "get", pkg.ImportExample+"@latest")
	getCmd.Dir = tmpDir
	getOutput, err := getCmd.CombinedOutput()
	if err != nil {
		return ExperimentResult{}, fmt.Errorf("go get failed: %v\n%s", err, getOutput)
	}

	// Get resolved version
	resolvedVersion, err := getResolvedVersion(tmpDir, pkg.ImportPath)
	if err != nil {
		return ExperimentResult{}, err
	}

	oldest := findOldestCompatible(tmpDir, pkg)
	latest := stringPtr(goVersions[len(goVersions)-1])

	return ExperimentResult{
		PackageName:      pkg.ImportPath,
		DependencySpec:   pkg.VersionSpec,
		ResolvedVersion:  &resolvedVersion,
		OldestCompatible: oldest,
		LatestCompatible: latest,
	}, nil
}

func getResolvedVersion(tmpDir, importPath string) (string, error) {
	// Run go mod download to resolve dependencies
	cmd := exec.Command("go", "mod", "download")
	cmd.Dir = tmpDir
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("go mod download failed: %v\n%s", err, output)
	}

	// Run go list to get the resolved version
	cmd = exec.Command("go", "list", "-m", importPath)
	cmd.Dir = tmpDir
	output, err = cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("go list failed: %v\n%s", err, output)
	}

	// Parse output: "module version"
	parts := strings.Fields(string(output))
	if len(parts) >= 2 {
		return parts[1], nil
	}

	return "", fmt.Errorf("could not parse version from go list output")
}

// Find the oldest compatible Go version using binary search.
func findOldestCompatible(tmpDir string, pkg Package) *string {
	left := 0
	right := len(goVersions)
	var oldest *string

	for left < right {
		mid := left + (right-left)/2
		version := goVersions[mid]

		fmt.Printf("  Testing Go %s\n", version)

		works, err := testGoVersion(tmpDir, version)
		if err != nil {
			fmt.Printf("    Error: %v\n", err)
			left = mid + 1
			continue
		}

		if works {
			fmt.Printf("    OK\n")
			oldest = stringPtr(version)
			right = mid
		} else {
			fmt.Printf("    Failed\n")
			left = mid + 1
		}
	}

	return oldest
}

// Find the latest compatible Go version.
func findLatestCompatible(tmpDir string) *string {
	// Start from newest and work backward.
	for i := len(goVersions) - 1; i >= 0; i-- {
		version := goVersions[i]
		works, err := testGoVersion(tmpDir, version)
		if err != nil {
			continue
		}
		if works {
			return stringPtr(version)
		}
	}
	return nil
}

func stringPtr(s string) *string {
	return &s
}

func ptrString(s *string) string {
	if s == nil {
		return "N/A"
	}
	return *s
}
