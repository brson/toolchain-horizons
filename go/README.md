# Go Dependency Toolchain Compatibility Experiment

This experiment mirrors the Rust version but for Go packages.

## Methodology

- Take a list of foundational Go packages.
- Make a project that depends on a recent major version using version specifiers
  like `v1.8` to allow flexibility in resolution.
- Find the oldest Go toolchain we can use while still being able to use
  the latest Go toolchain. They can use different resolved versions
  (like different lockfiles), but must use the same dependency specification.

## Tool: go

This experiment uses Go's built-in toolchain management:
- `go install golang.org/dl/go1.21.0@latest` - Install version installer
- `go1.21.0 download` - Download the actual Go toolchain
- `go1.21.0 build` - Build with specific version (includes type checking)

This is analogous to the Rust experiment using `rustup` and `cargo`.

## The package list

github.com/stretchr/testify
golang.org/x/sync
golang.org/x/time
github.com/google/uuid
github.com/gorilla/mux
github.com/pkg/errors
gopkg.in/yaml.v3
github.com/spf13/cobra
go.uber.org/zap
github.com/sirupsen/logrus

## Running

```bash
cd go
go run experiment.go
```

Results will be written to `results.json`.

## Type Checking

Unlike Python, Go's `go build` command performs full type checking,
making it comparable to Rust's `cargo check`. This validates:
- Type correctness
- API compatibility
- Compile-time checks
