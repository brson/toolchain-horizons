# How To: Remove every dependency from the TigerBeetle Rust client

I [previously conducted an experiment](blog1.md)
to help me understand how depending on Rust crates
affected my own ability to support prior Rust toolchain versions
in the [TigerBeetle] Rust client.

[TigerBeetle]: https://github.com/tigerbeetle/tigerbeetle

As part of that experiment I removed every dependency from the Rust client,
and also pushed back the minimum supported Rust version as far
as I could, to version 1.39 (released todo date).
Supporting toolchains prior to 1.39 requires not using
the `async` / `await` syntax,
which in this case I judged too burdensome to consider.

This followup describes in detail each step I took
to establish a very early MSVR on a very small Rust project.
As an exploration of Rust's language evolution
it may be interesting to some Rust programmers.

> Not all this work is in mainline TigerBeetle;
  it is [on my own branch](https://github.com/brson/tigerbeetle/tree/rustclient-no-deps-do-not-delete).

The below table shows what I had to do to support progressively
older versions of the Rust compiler.
Links generally go to interesting places,
with the "step" links leading to a detailed description of
how I enabled compatibility with that version.

I have tried to represent the technical details here
as accurately as reasonable,
but I am reconstructing this after the original work so there will be mistakes.
The code examples are representative and not always
exactly what I did.


| Step | Rust | Commit   | Action   | Features                                                              |
|------|------|----------|----------|-----------------------------------------------------------------------|
| [1]  | *    | [`4c85`] | Remove   | [`ignore`]                                                            |
| [2]  | *    | [`e67f`] | Remove   | [`walkdir`]                                                           |
| [3]  | *    | [`4bef`] | Remove   | [`anyhow`]                                                            |
| [4]  | 1.61 | [`65d9`] | Remove   | [`thiserror`]                                                         |
| [5]  | 1.56 | [`f7cc`] | Split    | [`futures`] → `-channel`, `-executor`, `-util`                        |
| [6]  | 1.56 | [`abd5`] | Polyfill | [`futures-executor`]                                                  |
| [7]  | 1.56 | [`632b`] | Polyfill | [`futures-util`]                                                      |
| [8]  | 1.56 | [`381d`] | Polyfill | [`futures-channel`]                                                   |
| [9]  | 1.56 | [`46bf`] | Polyfill | [`bitflags`]                                                          |
| [10] | 1.56 | [`fcc1`] | Rework   | [format string captures], [`Path::try_exists`], [`const Mutex::new`]  |
| [11] | 1.56 | [`db93`] | Remove   | [`rust-version`] (manifest)                                           |
| [12] | 1.55 | [`71b5`] | Rework   | [Edition 2021]→2018, [`TryFrom`]                                      |
| [13] | 1.53 | [`dad2`] | Replace  | [`CARGO_TARGET_TMPDIR`]                                               |
| [14] | 1.51 | [`c459`] | Rework   | [`IntoIterator` for arrays] (introduced 1.53)                         |
| [15] | 1.50 | [`ff9c`] | Rework   | [const generics] (introduced 1.51)                                    |
| [16] | 1.45 | [`76d5`] | Rework   | [array impls] for lengths > 32 (extended 1.47)                        |
| [17] | 1.42 | [`f0db`] | Replace  | [associated constants] ([`u64::MAX`]) (introduced 1.43)               |
| [18] | 1.41 | [`f3ac`] | Replace  | [`matches!`] (stabilized 1.42)                                        |
| [19] | 1.39 | [`02a8`] | Rework   | [`todo!`], [`mem::take`], [`#[non_exhaustive]`] (stabilized 1.40)     |

> *: `ignore` and `walkdir` are highly compatible back to Edition 2018 (Rust 1.31),
  and neither declares a `rust-version`.
  I removed them anyway as a matter of [TigerStyle](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md).

[`65d9`]: https://github.com/brson/tigerbeetle/commit/65d9b96fa
[`4c85`]: https://github.com/brson/tigerbeetle/commit/4c85201a2
[`e67f`]: https://github.com/brson/tigerbeetle/commit/e67f1867f
[`4bef`]: https://github.com/brson/tigerbeetle/commit/4befa9de6
[`f7cc`]: https://github.com/brson/tigerbeetle/commit/f7cc94b53
[`abd5`]: https://github.com/brson/tigerbeetle/commit/abd5b9774
[`632b`]: https://github.com/brson/tigerbeetle/commit/632b5ed6d
[`381d`]: https://github.com/brson/tigerbeetle/commit/381de6c81
[`46bf`]: https://github.com/brson/tigerbeetle/commit/46bf3a169
[`fcc1`]: https://github.com/brson/tigerbeetle/commit/fcc17d9f6
[`db93`]: https://github.com/brson/tigerbeetle/commit/db933c48e
[`71b5`]: https://github.com/brson/tigerbeetle/commit/71b5aa071
[`dad2`]: https://github.com/brson/tigerbeetle/commit/dad28699b
[`c459`]: https://github.com/brson/tigerbeetle/commit/c459efc97
[`ff9c`]: https://github.com/brson/tigerbeetle/commit/ff9cc6c39
[`76d5`]: https://github.com/brson/tigerbeetle/commit/76d588f28
[`f0db`]: https://github.com/brson/tigerbeetle/commit/f0db34be3
[`f3ac`]: https://github.com/brson/tigerbeetle/commit/f3ac2dd2a
[`02a8`]: https://github.com/brson/tigerbeetle/commit/02a82dfa1

[1]: #user-content-step-1-remove-ignore
[2]: #user-content-step-2-remove-walkdir
[3]: #user-content-step-3-remove-anyhow
[4]: #user-content-step-4-remove-thiserror
[5]: #user-content-step-5-split-futures
[6]: #user-content-step-6-polyfill-futures-executor
[7]: #user-content-step-7-polyfill-futures-utils
[8]: #user-content-step-8-polyfill-futures-channel
[9]: #user-content-step-9-polyfill-bitflags
[10]: #user-content-step-10-support-rust-156
[11]: #user-content-step-11-remove-rust-version
[12]: #user-content-step-12-edition-2018
[13]: #user-content-step-13-replace-cargo_target_tmpdir
[14]: #user-content-step-14-support-rust-151
[15]: #user-content-step-15-support-rust-150
[16]: #user-content-step-16-support-rust-145
[17]: #user-content-step-17-support-rust-142
[18]: #user-content-step-18-support-rust-141
[19]: #user-content-step-19-support-rust-139

[`ignore`]: https://crates.io/crates/ignore
[`walkdir`]: https://crates.io/crates/walkdir
[`anyhow`]: https://crates.io/crates/anyhow
[`thiserror`]: https://crates.io/crates/thiserror
[`futures`]: https://crates.io/crates/futures
[`futures-executor`]: https://crates.io/crates/futures-executor
[`futures-util`]: https://crates.io/crates/futures-util
[`futures-channel`]: https://crates.io/crates/futures-channel
[`bitflags`]: https://crates.io/crates/bitflags

[format string captures]: https://blog.rust-lang.org/2022/01/13/Rust-1.58.0.html#captured-identifiers-in-format-strings
[`Path::try_exists`]: https://doc.rust-lang.org/std/path/struct.Path.html#method.try_exists
[`const Mutex::new`]: https://doc.rust-lang.org/std/sync/struct.Mutex.html#method.new
[`rust-version`]: https://doc.rust-lang.org/cargo/reference/manifest.html#the-rust-version-field
[Edition 2021]: https://doc.rust-lang.org/edition-guide/rust-2021/index.html
[`TryFrom`]: https://doc.rust-lang.org/std/convert/trait.TryFrom.html
[`CARGO_TARGET_TMPDIR`]: https://doc.rust-lang.org/cargo/reference/environment-variables.html#environment-variables-cargo-sets-for-crates
[`IntoIterator` for arrays]: https://doc.rust-lang.org/std/primitive.array.html#impl-IntoIterator-for-%5BT;+N%5D
[const generics]: https://blog.rust-lang.org/2021/02/26/Rust-1.51.0.html#const-generics-mvp
[array impls]: https://blog.rust-lang.org/2020/10/08/Rust-1.47.html
[associated constants]: https://blog.rust-lang.org/2019/04/11/Rust-1.34.0.html#library-stabilizations
[`u64::MAX`]: https://doc.rust-lang.org/std/primitive.u64.html#associatedconstant.MAX
[`matches!`]: https://doc.rust-lang.org/std/macro.matches.html
[`todo!`]: https://doc.rust-lang.org/std/macro.todo.html
[`mem::take`]: https://doc.rust-lang.org/std/mem/fn.take.html
[`#[non_exhaustive]`]: https://doc.rust-lang.org/reference/attributes/type_system.html#the-non_exhaustive-attribute




## Step 1: Remove `ignore`

Many of our dependencies were in the build script,
which needs to orchestrate linking of the native `tb_client`
library in platform-specific ways,
and to arrange for the inclusion of various static assets.

The `ignore` crate is for walking the file system
while following `.gitignore` rules.
An easy approximation can be written with the simpler `walkdir` crate.




## Step 2: Remove `walkdir`

We used `walkdir` in the build script to find source files
for which to emit `cargo:rerun-if-changed` directives,
allowing cargo to rebuild if non-Rust input files change.

For this specific purpose we can just ask `git ls-files`
for the information we need.

```rust
// Before: walkdir with custom filtering
use walkdir::{DirEntry, WalkDir};

fn is_hidden(entry: &DirEntry) -> bool {
    entry.file_name().to_str()
        .map(|s| s.starts_with('.'))
        .unwrap_or(false)
}

for entry in WalkDir::new(&tigerbeetle_root)
    .into_iter()
    .filter_entry(|e| !is_hidden(e))
    .filter_map(|e| e.ok())
{
    if let Some(ext) = entry.path().extension() {
        if ext == "zig" {
            println!("cargo:rerun-if-changed={}", entry.path().display());
        }
    }
}

// After: shell out to git
let output = std::process::Command::new("git")
    .args(["ls-files", "-z"])
    .current_dir(&tigerbeetle_root)
    .output()?;

let stdout = String::from_utf8(output.stdout)?;
for file_path in stdout.split('\0') {
    if !file_path.is_empty() && file_path.ends_with(".zig") {
        println!("cargo:rerun-if-changed={}/{}", tigerbeetle_root, file_path);
    }
}
```




## Step 3: Remove `anyhow`

The `anyhow` crate makes it easy to handle errors correctly
without thinking hard about precise error scenarios.
We used `anyhow` for convenience in the build script &mdash;
within the crate itself we use precise error types.

I replaced `anyhow::Result` with `Result<T, Box<dyn std::error::Error>>`:

```rust
// Before
fn main() -> anyhow::Result<()> { ... }
fn test_client() -> anyhow::Result<tb::Client> { ... }
fn smoke() -> anyhow::Result<()> { ... }

// After
fn main() -> Result<(), Box<dyn std::error::Error>> { ... }
fn test_client() -> Result<tb::Client, Box<dyn std::error::Error>> { ... }
fn smoke() -> Result<(), Box<dyn std::error::Error>> { ... }
```

The resulting types are unpleasant to read,
so this isn't a transformation I favor for anything other
than small codebases.




## Step 4: Remove `thiserror`

The `thiserror` crate makes it easy to maintain _precise_ error types.
Using `thiserror` requires significant metadata annotations,
and as Rust's `Error` trait has improved
the cost-benefit of using `thiserror` over hand-writing
error trait implementations has become less clear.

Replacing it generally requires adding a one-liner
that implements the `Error` trait,
plus a full-boilerplate implementation of the `Display` trait,
the code duplication for which is actually not bad,
and which has comparable readability to the `thiserror`-annotated version.

```rust
// Before: thiserror derive macro
#[derive(thiserror::Error, Debug, Copy, Clone)]
#[non_exhaustive]
pub enum CreateAccountResult {
    #[error("linked event failed")]
    LinkedEventFailed,
    #[error("linked event chain open")]
    LinkedEventChainOpen,
    #[error("id must not be zero")]
    IdMustNotBeZero,
    // ... 20+ more variants
}

// After: manual impls
#[derive(Debug, Copy, Clone)]
#[non_exhaustive]
pub enum CreateAccountResult {
    LinkedEventFailed,
    LinkedEventChainOpen,
    IdMustNotBeZero,
    // ...
}

impl std::error::Error for CreateAccountResult {}

impl core::fmt::Display for CreateAccountResult {
    fn fmt(&self, f: &mut core::fmt::Formatter) -> core::fmt::Result {
        match self {
            Self::LinkedEventFailed => f.write_str("linked event failed"),
            Self::LinkedEventChainOpen => f.write_str("linked event chain open"),
            Self::IdMustNotBeZero => f.write_str("id must not be zero"),
            // ...
        }
    }
}
```




## Step 5: Split futures

The vital `futures` crate is a façade that minimally-wraps
other crates.
The first step to removing it is to split it
into the sub-crates containing the features we use:
message channels,
the basic `block_on` async executor,
and the `Stream` trait.

```toml
# Before
[dependencies]
futures = "0.3.31"
```

```toml
# After
[dependencies]
futures-channel = "0.3.31"

[dev-dependencies]
futures-executor = "0.3.31"
futures-util = "0.3.31"
```




## Step 6: Polyfill futures-executor

Implemented a minimal `block_on` executor (88 lines) using raw waker API and condition variables:

```rust
// Usage change
// Before: futures::executor::block_on(main_async())
// After:  tb::futures_polyfills::block_on(main_async())

struct Parker {
    mutex: Mutex<bool>,
    condvar: Condvar,
}

impl Parker {
    fn new() -> Self {
        Parker { mutex: Mutex::new(false), condvar: Condvar::new() }
    }

    fn unpark(&self) {
        *self.mutex.lock().unwrap() = true;
        self.condvar.notify_one();
    }

    fn park(&self) {
        let mut notified = self.mutex.lock().unwrap();
        while !*notified {
            notified = self.condvar.wait(notified).unwrap();
        }
        *notified = false;
    }
}

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

// Plus raw waker vtable implementation for clone/wake/wake_by_ref/drop
```

## Step 7: Polyfill futures-utils

Extended `futures_polyfills.rs` with `join` and `select` utilities for tests.

## Step 8: Polyfill futures-channel

Implemented custom oneshot channel using `Arc`, `Mutex`, and `Waker`.
This was the **final runtime dependency**.

```rust
struct OneshotShared<T> {
    waker: Mutex<Option<Waker>>,
    value: Mutex<Option<T>>,
}

struct OneshotSender<T> {
    shared: Arc<OneshotShared<T>>,
}

impl<T> OneshotSender<T> {
    fn send(self, value: T) {
        *self.shared.value.lock().unwrap() = Some(value);
        if let Some(waker) = self.shared.waker.lock().unwrap().take() {
            waker.wake();
        }
    }
}

struct OneshotFuture<T> {
    shared: Arc<OneshotShared<T>>,
}

impl<T> Future for OneshotFuture<T> {
    type Output = T;

    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<T> {
        if let Some(value) = self.shared.value.lock().unwrap().take() {
            return Poll::Ready(value);
        }
        *self.shared.waker.lock().unwrap() = Some(cx.waker().clone());
        Poll::Pending
    }
}
```

## Step 9: Polyfill bitflags

Implemented a complete `bitflags!` macro (418 lines) compatible with bitflags 2.6 API:

```rust
pub trait Flags: Sized + Copy {
    type Bits: Bits;

    fn bits(&self) -> Self::Bits;
    fn from_bits_retain(bits: Self::Bits) -> Self;
    fn empty() -> Self { Self::from_bits_retain(Self::Bits::EMPTY) }
    fn all() -> Self;
    fn from_bits(bits: Self::Bits) -> Option<Self>;
    fn from_bits_truncate(bits: Self::Bits) -> Self;
    fn is_empty(&self) -> bool { self.bits() == Self::Bits::EMPTY }
    fn is_all(&self) -> bool;
    fn intersects(&self, other: Self) -> bool;
    fn contains(&self, other: Self) -> bool;
    fn insert(&mut self, other: Self);
    fn remove(&mut self, other: Self);
    fn toggle(&mut self, other: Self);
    fn intersection(self, other: Self) -> Self;
    fn union(self, other: Self) -> Self;
    fn difference(self, other: Self) -> Self;
    fn symmetric_difference(self, other: Self) -> Self;
    fn complement(self) -> Self;
}

pub trait Bits: Copy + PartialEq
    + BitAnd<Output = Self> + BitOr<Output = Self>
    + BitXor<Output = Self> + Not<Output = Self>
{
    const EMPTY: Self;
}

impl Bits for u16 { const EMPTY: Self = 0; }
// ... plus macro to generate flag types
```

## Step 10: Support Rust 1.56

```rust
// Captured identifiers (stabilized 1.58)
// Before
panic!("Unknown CreateAccountResult: {v}");
// After
panic!("Unknown CreateAccountResult: {}", v);

// Path::try_exists (stabilized 1.63)
// Before
if !Path::new(&format!("{cargo_manifest_dir}/assets/tb_client.h")).try_exists()? {
// After
if !Path::new(&format!("{}/assets/tb_client.h", cargo_manifest_dir)).exists() {

// const Mutex::new (stabilized 1.63)
// Before
static GLOBAL_GENERATOR: Mutex<Option<TbidGenerator>> = Mutex::new(None);
// After
static ONCE: Once = Once::new();
static mut GLOBAL_GENERATOR: MaybeUninit<Mutex<TbidGenerator>> = MaybeUninit::uninit();

ONCE.call_once(|| unsafe {
    GLOBAL_GENERATOR.as_mut_ptr().write(Mutex::new(TbidGenerator::new()));
});
```

## Step 11: Remove rust-version

```toml
# Before
[package]
rust-version = "1.63"

# After: field removed entirely
```

## Step 12: Edition 2018

```rust
// Cargo.toml: edition = "2021" → edition = "2018"

// TryFrom is in the 2021 prelude but not 2018
// Before (implicit)
let x: u32 = value.try_into()?;

// After (explicit import needed)
use std::convert::TryFrom;
let x: u32 = value.try_into()?;
```

## Step 13: Replace CARGO_TARGET_TMPDIR

```rust
// Before (stabilized 1.54)
let tmp_dir = env!("CARGO_TARGET_TMPDIR");

// After
let manifest_dir = env!("CARGO_MANIFEST_DIR");
let tmp_dir = format!("{}/target/tmp", manifest_dir);
```

## Step 14: Support Rust 1.51

```rust
// IntoIterator for arrays (stabilized 1.53)
// Before
.args(["ls-files", "-z"])

// After
.args(&["ls-files", "-z"])
```

## Step 15: Support Rust 1.50

```rust
// Const generics (stabilized 1.51)
// Before
pub struct Reserved<const N: usize>([u8; N]);
pub reserved: Reserved<4>,
pub reserved: Reserved<58>,

// After: macro-generated specific types
macro_rules! reserved_type {
    ($name:ident, $size:expr) => {
        #[repr(transparent)]
        #[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
        pub struct $name([u8; $size]);

        impl Default for $name {
            fn default() -> $name { $name([0; $size]) }
        }
    };
}

reserved_type!(Reserved4, 4);
reserved_type!(Reserved6, 6);
reserved_type!(Reserved56, 56);
reserved_type!(Reserved58, 58);
```

## Step 16: Support Rust 1.45

Array trait impls for lengths > 32 were extended in 1.47.
For types containing large arrays, manual trait impls are needed:

```rust
// The Reserved58 type contains [u8; 58], which didn't have
// automatic Debug/Copy/Clone/etc impls before 1.47
impl Debug for Reserved58 {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_tuple("Reserved58").field(&&self.0[..]).finish()
    }
}
```

## Step 17: Support Rust 1.42

```rust
// Associated constants on primitives (stabilized 1.43)
// Before
u64::MAX

// After
core::u64::MAX
```

## Step 18: Support Rust 1.41

```rust
// matches! macro (stabilized 1.42)
// Before
assert!(matches!(client, Err(tb::InitStatus::AddressInvalid)));

// After
assert!(match client { Err(tb::InitStatus::AddressInvalid) => true, _ => false });
```

## Step 19: Support Rust 1.39

```rust
// todo! macro (stabilized 1.40)
// Before
_ => todo!(),
// After
_ => unimplemented!(),

// mem::take (stabilized 1.40)
// Before
let server_stdout = mem::take(&mut server.stdout).unwrap();
// After
let server_stdout = mem::replace(&mut server.stdout, None).unwrap();

// #[non_exhaustive] attribute (stabilized 1.40)
// Before
#[non_exhaustive]
pub enum CreateAccountResult { ... }
// After: attribute removed (breaking change for downstream)
pub enum CreateAccountResult { ... }
```
