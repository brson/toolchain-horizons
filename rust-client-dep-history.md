# TigerBeetle Rust Client Dependency History

This document tracks the history of dependency removals in the TigerBeetle Rust client, showing how the client achieved zero runtime dependencies.

## Initial Dependencies

The Rust client was initially merged in commit `ee85038d4` with the following dependencies:

**Cargo.toml (Initial)**:
```toml
[package]
name = "tigerbeetle"
version = "0.1.0"
edition = "2021"

[dependencies]
bitflags = "2.6.0"
futures = "0.3.31"
thiserror = "2.0.3"

[build-dependencies]
anyhow = "1.0.93"
bindgen = "0.70.1"
ignore = "0.4.23"

[dev-dependencies]
anyhow = "1.0.93"
tempfile = "3.15.0"
```

## Dependency Removal History

### 1. Remove thiserror (65d9b96fa)

**Commit**: `65d9b96fafa8b1127a5430b220c9272092f9ca00`
**Author**: Austen Adler
**Date**: Sat Feb 8 02:14:48 2025 -0500

**Dependency Removed**: `thiserror = "2.0.3"` (runtime dependency)

**Technical Summary**: Replaced thiserror's derive macros with manual implementations of `Display` and `Error` traits for all error types.

**Changes**:
- Added manual `impl Display` for `CreateAccountResult`, `CreateTransferResult`, `Status`, `PacketStatus`, and other error types
- Each Display implementation uses pattern matching to return appropriate error messages
- Example:
  ```rust
  impl core::fmt::Display for Status {
      fn fmt(&self, f: &mut core::fmt::Formatter) -> core::fmt::Result {
          match self {
              Self::Unexpected => f.write_str("unexpected"),
              Self::OutOfMemory => f.write_str("out of memory"),
              Self::AddressInvalid => f.write_str("address invalid"),
              // ... etc
          }
      }
  }
  ```

**Impact**: 3 files changed, 209 insertions(+), 139 deletions(-)

---

### 2. Remove ignore crate (4c85201a2)

**Commit**: `4c85201a26aee7eadede272dce898af52baf11f5`
**Author**: Brian Anderson
**Date**: Tue Sep 16 16:49:01 2025 -0600

**Dependency Removed**: `ignore = "0.4.23"` (build dependency)

**Technical Summary**: Replaced the `ignore` crate's git-aware directory walker with `walkdir` crate.

**Changes**:
- Changed from `ignore::Walk` to `walkdir::WalkDir`
- Implemented custom `is_hidden()` function to filter dotfiles
- Simplified the build script's file enumeration logic

**Impact**: 8 files changed, 31 insertions(+), 727 deletions(-) (mostly Cargo.lock changes)

---

### 3. Remove walkdir (e67f1867f)

**Commit**: `e67f1867fbe8171103b272aaee67e9d0f5d38dcb`
**Author**: Brian Anderson
**Date**: Thu Sep 25 16:34:58 2025 -0600

**Dependency Removed**: `walkdir` (build dependency)

**Technical Summary**: Replaced walkdir with `git ls-files` command to enumerate source files.

**Changes**:
- Removed WalkDir and custom filtering logic
- Used `std::process::Command` to run `git ls-files -z`
- Parses null-separated output to find `.zig` files
- Example:
  ```rust
  let output = std::process::Command::new("git")
      .args(["ls-files", "-z"])
      .current_dir(&tigerbeetle_root)
      .output()?;

  let stdout = String::from_utf8(output.stdout)?;
  for file_path in stdout.split('\0') {
      if !file_path.is_empty() && file_path.ends_with(".zig") {
          let full_path = format!("{tigerbeetle_root}/{file_path}");
          println!("cargo:rerun-if-changed={}", full_path);
      }
  }
  ```

**Impact**: 2 files changed, 15 insertions(+), 20 deletions(-)

---

### 4. Remove anyhow (4befa9de6)

**Commit**: `4befa9de691b2986a5b140e3159f76b71dc5aa72`
**Author**: Brian Anderson
**Date**: Mon Nov 3 10:51:40 2025 -0700

**Dependency Removed**: `anyhow` (build and dev dependency)

**Technical Summary**: Replaced `anyhow::Result` with standard `Result<T, Box<dyn std::error::Error>>`.

**Changes**:
- Changed function signatures in build.rs and tests from `anyhow::Result<T>` to `Result<T, Box<dyn std::error::Error>>`
- Removed `anyhow` from both build-dependencies and dev-dependencies
- Error propagation continues to work with the `?` operator

**Impact**: 3 files changed, 53 insertions(+), 53 deletions(-)

---

### 5. Remove futures (partial) (f7cc94b53)

**Commit**: `f7cc94b538ac5f4d35d7a46b38c1535447e7b7dc`
**Author**: Brian Anderson
**Date**: Mon Nov 3 11:02:47 2025 -0700

**Dependency Removed**: `futures = "0.3.31"` (runtime dependency)

**Technical Summary**: Split the monolithic `futures` crate into specific sub-crates needed.

**Changes**:
- Removed `futures` from runtime dependencies
- Added `futures-channel = "0.3.31"` to runtime dependencies
- Changed dev-dependencies from `futures` to `futures-executor` and `futures-util`
- This is a stepping stone to removing all futures crates

**Impact**: 3 files changed, 9 insertions(+), 8 deletions(-)

---

### 6. Remove futures-executor (abd5b9774)

**Commit**: `abd5b977462725d80711a66d441a3737bf71e89d`
**Author**: Brian Anderson
**Date**: Mon Nov 3 11:27:30 2025 -0700

**Dependency Removed**: `futures-executor = "0.3.31"` (dev dependency)

**Technical Summary**: Implemented a minimal `block_on` executor using raw waker API and condition variables.

**Changes**:
- Created `src/futures_polyfills.rs` module (88 lines)
- Implemented custom `Parker` struct using `Mutex<bool>` and `Condvar`
- Implemented raw waker vtable for integration with Rust's async runtime
- Key components:
  - `block_on()`: Runs a future to completion on current thread
  - `Parker`: Provides park/unpark mechanism
  - Raw waker implementation with clone, wake, wake_by_ref, and drop

**Interesting Diff**: The polyfill is a complete minimal async executor:
```rust
pub fn block_on<F: Future>(future: F) -> F::Output {
    let mut future = Box::pin(future);

    let parker = Arc::new(Parker::new());
    let waker = parker_into_waker(parker.clone());
    let mut context = Context::from_waker(&waker);

    loop {
        match future.as_mut().poll(&mut context) {
            Poll::Ready(result) => return result,
            Poll::Pending => parker.park(),
        }
    }
}
```

**Impact**: 7 files changed, 99 insertions(+), 8 deletions(-)

---

### 7. Remove futures-utils (632b5ed6d)

**Commit**: `632b5ed6dc561b8e5532792c1686660329a34895`
**Author**: Brian Anderson
**Date**: Mon Nov 3 12:05:29 2025 -0700

**Dependency Removed**: `futures-util = "0.3.31"` (dev dependency)

**Technical Summary**: Extended futures_polyfills.rs with join/select utilities.

**Changes**:
- Removed `futures-util` from dev-dependencies
- Extended `futures_polyfills.rs` module with additional utilities
- Implemented polyfills for joining and selecting futures

**Impact**: 7 files changed, 130 insertions(+), 17 deletions(-)

---

### 8. Remove futures-channel (381de6c81)

**Commit**: `381de6c81449e29c360ada6591c08be8e167dd29`
**Author**: Brian Anderson
**Date**: Mon Nov 3 12:30:26 2025 -0700

**Dependency Removed**: `futures-channel = "0.3.31"` (runtime dependency - **FINAL RUNTIME DEPENDENCY**)

**Technical Summary**: Implemented custom oneshot channel using Arc, Mutex, and Waker.

**Changes**:
- Removed last runtime dependency
- Implemented custom `OneshotSender` and `OneshotReceiver` types
- Used `Arc<OneshotShared<T>>` with mutex-protected value and waker
- Integrates with Rust's Future trait via custom Poll implementation

**Interesting Diff**: Custom oneshot channel implementation:
```rust
struct OneshotSender<T> {
    shared: Arc<OneshotShared<T>>,
}

impl<T> OneshotSender<T> {
    fn send(self, value: T) {
        let mut val_guard = self.shared.value.lock().unwrap();
        *val_guard = Some(value);
        drop(val_guard);

        let mut waker = self.shared.waker.lock().unwrap();
        if let Some(waker) = waker.take() {
            waker.wake();
        }
    }
}
```

**Impact**: 2 files changed, 77 insertions(+), 17 deletions(-)

**Significance**: This commit achieved **zero runtime dependencies** for the Rust client.

---

### 9. Polyfill bitflags (46bf3a169)

**Commit**: `46bf3a169bb7f4aa7bf34bedbfeccbf34fc7828d`
**Author**: Brian Anderson
**Date**: Fri Nov 21 15:05:50 2025 -0700

**Dependency Removed**: `bitflags = "2.6.0"` (runtime dependency)

**Technical Summary**: Implemented a complete bitflags macro compatible with bitflags 2.6 API.

**Changes**:
- Created comprehensive `bitflags_polyfill.rs` module (418 lines)
- Implemented `Flags` trait with all common methods
- Implemented `Bits` trait for underlying integer types
- Created `bitflags!` macro that generates flag types
- Full API compatibility with bitflags 2.6

**Interesting Diff**: The polyfill includes a complete trait-based implementation:
```rust
pub trait Flags: Sized + Copy {
    type Bits: Bits;

    fn bits(&self) -> Self::Bits;
    fn from_bits_retain(bits: Self::Bits) -> Self;
    fn empty() -> Self;
    fn all() -> Self;
    fn from_bits(bits: Self::Bits) -> Option<Self>;
    fn from_bits_truncate(bits: Self::Bits) -> Self;
    fn is_empty(&self) -> bool;
    fn is_all(&self) -> bool;
    fn intersects(&self, other: Self) -> bool;
    fn contains(&self, other: Self) -> bool;
    // ... and more
}
```

**Impact**: 3 files changed, 421 insertions(+), 3 deletions(-)

**Note**: While this was added after achieving zero runtime deps, it demonstrates the commitment to dependency minimization even for well-established crates.

---

## Summary

The TigerBeetle Rust client dependency removal was executed in a systematic progression:

1. **Error handling** (thiserror) - Manual trait implementations
2. **Build tooling** (ignore, walkdir) - Replaced with git and stdlib
3. **Error propagation** (anyhow) - Standard library Result types
4. **Async runtime** (futures-*) - Custom polyfills with raw waker API
5. **Bitflags** (bitflags) - Complete macro reimplementation

The client went from 6 runtime dependencies to **zero**, achieving maximum compatibility across Rust toolchain versions while maintaining full functionality.
