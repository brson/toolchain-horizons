# Go Version Management Research

## The Bootstrapping Problem

Starting with Go 1.5, the Go toolchain is [written in Go itself](https://go.dev/doc/install/source) rather than C. This creates a bootstrapping problem: **you need Go to build Go**.

### Bootstrap Version Requirements

According to the [official Go documentation](https://go.dev/doc/install/source), the minimum bootstrap version has evolved over time:

- **Go ≤ 1.4**: Requires a C toolchain
- **Go 1.5–1.19**: Needs Go 1.4 compiler
- **Go 1.20–1.21**: Requires Go 1.17 compiler
- **Go 1.22–1.23**: Needs Go 1.20 compiler
- **Go 1.24+**: Requires Go 1.22.6+ (new policy: Go 1.N requires Go 1.M where M = (N-2) rounded down to even number)

Sources:
- [Go 1.20 bootstrap requirements](https://github.com/golang/go/issues/44505)
- [Go 1.22 bootstrap requirements](https://github.com/golang/go/issues/54265)

### Why This Matters for Testing

To test packages against old Go versions (e.g., Go 1.13–1.23), we need to:
1. Install a bootstrap version
2. Use it to build the target version
3. Test with the target version
4. Repeat for each version in the test matrix

This creates a dependency chain that must be carefully managed.

## GVM: The Traditional Approach

[GVM (Go Version Manager)](https://github.com/moovweb/gvm) is the traditional tool for managing multiple Go versions, similar to nvm for Node.js.

### The GVM Bootstrapping Issue

[Issue #204](https://github.com/moovweb/gvm/issues/204) describes the core problem: GVM doesn't automatically handle bootstrap dependencies. Users must manually install prerequisite versions.

**Manual workaround example:**
```bash
gvm install go1.4 -B && \
gvm use go1.4 && \
export GOROOT_BOOTSTRAP=$GOROOT && \
gvm install go1.8 && \
gvm use go1.8 --default
```

### GVM Limitations

1. **No automatic bootstrap chain**: Must manually install Go 1.4, then use it to build Go 1.5+
2. **Go 1.4 special case**: Go 1.4 requires `-B` flag to build from binary
3. **Environment complexity**: Requires shell modifications and GOROOT_BOOTSTRAP management
4. **Maintenance**: Less actively maintained compared to alternatives

## Alternative Approaches

### 1. Official Method: `golang.org/dl`

Go's [official approach](https://go.dev/doc/manage-install) for multiple versions:

```bash
# Install Go 1.22 wrapper
go install golang.org/dl/go1.22.0@latest
# Download the actual Go 1.22 toolchain
go1.22.0 download
# Use it
go1.22.0 version
go1.22.0 build
```

**Pros:**
- Official and well-maintained
- No bootstrapping complexity (downloads pre-built binaries)
- Versions installed to `~/sdk/goX.Y.Z`
- Simple version switching with `goX.Y.Z` commands

**Cons:**
- Requires an existing Go installation to start
- Each version command is separate (`go1.22.0`, `go1.23.0`, etc.)
- Not as seamless as language-agnostic version managers

### 2. goenv

[goenv](https://github.com/go-nv/goenv) is like pyenv/rbenv for Go.

**Pros:**
- Simple installation process
- Automatic version switching via `.go-version` files
- Well-documented

**Cons:**
- Requires pull requests for new Go releases
- Multi-step setup with `goenv rehash`
- Go-specific (not useful for multi-language projects)

### 3. g

[g](https://github.com/stefanmaric/g) is a minimal Go version manager.

**Pros:**
- Lightweight and simple
- No environment modifications
- Downloads pre-built binaries
- Works immediately with new Go releases

**Cons:**
- Less feature-rich than alternatives
- Go-specific

### 4. asdf

[asdf](https://github.com/bernardoduarte/awesome-version-managers) is a universal version manager supporting multiple languages.

**Pros:**
- Single tool for Go, Node, Python, Ruby, etc.
- Plugin-based architecture
- Unified commands across all languages
- Automatic version switching via `.tool-versions`

**Cons:**
- More complex setup
- Requires learning asdf's plugin system

## Recommendations for Our Tool

### Option 1: Official `golang.org/dl` Method (Recommended)

**Implementation:**
```go
func installGoVersion(version string) error {
    // Install wrapper command
    cmd := exec.Command("go", "install",
        fmt.Sprintf("golang.org/dl/go%s@latest", version))
    if err := cmd.Run(); err != nil {
        return err
    }

    // Download actual Go toolchain
    cmd = exec.Command(fmt.Sprintf("go%s", version), "download")
    return cmd.Run()
}

func testWithGoVersion(tmpDir, version string) bool {
    cmd := exec.Command(fmt.Sprintf("go%s", version), "build", ".")
    cmd.Dir = tmpDir
    return cmd.Run() == nil
}
```

**Why this is best:**
- No bootstrap complexity (uses pre-built binaries)
- Official and maintained by Go team
- Reliable and well-tested
- Works across all platforms
- No external dependencies beyond Go itself

### Option 2: GVM with Bootstrap Chain

**Implementation complexity:**
```bash
# Pseudo-code for bootstrap chain
install_go_1.4_binary()
use_go_1.4()
build_go_1.13()  # Oldest we want to test
build_go_1.14()
# ... continue chain
build_go_1.22()
```

**Challenges:**
1. Need to maintain bootstrap chain logic
2. Go 1.4 is ancient (2014) and may have platform issues
3. Building from source is slow (~5-10 minutes per version)
4. More failure points in the chain
5. GVM installation and configuration complexity

### Option 3: Hybrid Approach

Use `golang.org/dl` for most versions, but:
- Cache installed versions
- Test only subset of versions (e.g., 1.13, 1.16, 1.18, 1.20, 1.22, 1.23)
- Allow user to specify versions to test

**Example:**
```go
var goVersionsToTest = []string{
    "1.13", "1.16", "1.18", "1.20", "1.22", "1.23",
}

func ensureGoVersion(version string) error {
    // Check if already installed
    cmd := exec.Command(fmt.Sprintf("go%s", version), "version")
    if cmd.Run() == nil {
        return nil // Already installed
    }

    // Install if not present
    return installGoVersion(version)
}
```

## Implementation Plan for Our Experiment

### Phase 1: Basic Support (Current)
- ✅ Test with current Go version only
- ✅ Verify packages compile
- ✅ Generate compatibility report

### Phase 2: Multiple Version Support
1. Use `golang.org/dl` method
2. Test against 6 representative versions: 1.13, 1.16, 1.18, 1.20, 1.22, 1.23
3. Use binary search like Rust experiment
4. Cache installed versions between runs

### Phase 3: Optimizations
1. Parallel version testing
2. Incremental testing (only test changed packages)
3. Result caching
4. Optional: support for user-specified version ranges

## Estimated Complexity

### Using `golang.org/dl` (Recommended):
- **Implementation time**: 2-3 hours
- **Additional dependencies**: None (just Go itself)
- **Reliability**: High (official method)
- **Maintenance burden**: Low

### Using GVM:
- **Implementation time**: 6-8 hours
- **Additional dependencies**: GVM, shell scripting, binary Go 1.4
- **Reliability**: Medium (bootstrap chain can fail)
- **Maintenance burden**: High (need to handle GVM updates, bootstrap chain)

### Using asdf or goenv:
- **Implementation time**: 3-4 hours
- **Additional dependencies**: asdf/goenv installation
- **Reliability**: Medium-High
- **Maintenance burden**: Medium

## Conclusion

**Recommendation**: Implement Phase 2 using the official `golang.org/dl` method.

**Reasoning**:
1. No bootstrap complexity
2. Official and reliable
3. Fast installation (pre-built binaries)
4. Works consistently across platforms
5. Minimal maintenance burden
6. Same pattern as other experiments (Rust uses rustup, Java uses SDKMAN)

The GVM approach, while interesting from a bootstrapping perspective, adds significant complexity for minimal benefit in our use case.

## Sources

- [Go Version Manager (GVM)](https://github.com/moovweb/gvm)
- [GVM Bootstrapping Issue #204](https://github.com/moovweb/gvm/issues/204)
- [Go Install from Source Documentation](https://go.dev/doc/install/source)
- [Go 1.20 Bootstrap Requirements](https://github.com/golang/go/issues/44505)
- [Go 1.22 Bootstrap Requirements](https://github.com/golang/go/issues/54265)
- [Managing Go Installations](https://go.dev/doc/manage-install)
- [Multiple Go Versions Guide](https://stackoverflow.com/questions/61280008/multiple-versions-of-go)
- [Go Version Manager Alternatives](https://github.com/bernardoduarte/awesome-version-managers)
- [g - Simple Go Version Manager](https://github.com/stefanmaric/g)
- [goenv - Go Version Manager](https://github.com/go-nv/goenv)
