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

Much of this work is not in mainline TigerBeetle
as the benefits and tradeoffs are not clear;
lined commits are [on my own branch](https://github.com/brson/tigerbeetle/tree/rustclient-no-deps-do-not-delete).

My starting `Cargo.toml` was

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
| [11] | 1.55 | [`db93`] | Remove   | [`rust-version`] (stabilized 1.56)                                    |
| [12] | 1.55 | [`71b5`] | Rework   | [Edition 2021]→2018, [`TryFrom`]                                      |
| [13] | 1.53 | [`dad2`] | Replace  | [`CARGO_TARGET_TMPDIR`] (stabilized 1.54)                             |
| [14] | 1.51 | [`c459`] | Rework   | [`IntoIterator` for arrays] (stabilized 1.53)                         |
| [15] | 1.50 | [`ff9c`] | Rework   | [const generics] (stabilized 1.51)                                    |
| [16] | 1.45 | [`76d5`] | Rework   | [array impls] for lengths > 32 (stabilized 1.47)                      |
| [17] | 1.42 | [`f0db`] | Replace  | [associated constants] ([`u64::MAX`]) (stabilized 1.43)               |
| [18] | 1.41 | [`f3ac`] | Replace  | [`matches!`] (stabilized 1.42)                                        |
| [19] | 1.39 | [`02a8`] | Rework   | [`todo!`], [`mem::take`], [`non_exhaustive`] (stabilized 1.40)        |

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
[`non_exhaustive`]: https://doc.rust-lang.org/reference/attributes/type_system.html#the-non_exhaustive-attribute




## Step 1: Remove `ignore`

Many of our dependencies were in the build script,
which needs to orchestrate linking of the native `tb_client`
library in platform-specific ways,
and to arrange for the inclusion of various static assets.

The `ignore` crate is for walking the file system
while following `.gitignore` rules.
An easy approximation can be written with the simpler `walkdir` crate.

```rust
// Before: ignore crate handles .gitignore automatically
use ignore::Walk;

for entry in Walk::new(&tigerbeetle_root) {
    let entry = entry?;
    // ...
}
```

```rust
// After: walkdir with manual hidden-file filtering
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
    // ...
}
```




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
```

```rust
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
```

```rust
// After
fn main() -> Result<(), Box<dyn std::error::Error>> { ... }
fn test_client() -> Result<tb::Client, Box<dyn std::error::Error>> { ... }
fn smoke() -> Result<(), Box<dyn std::error::Error>> { ... }
```

The resulting types are unpleasant to read
(especially for code that needs to account for `Send`, `Sync`, and `'static` bounds),
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
```

```rust
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




## Step 6: Polyfill `futures-executor`

From `futures-executor`,
`block_on` is a simple async executor
useful for non-I/O async tasks,
and for writing runtime-agnostic test-cases.

Impleminting the most basic Rust executor is not super hard,
but involves some unsafe code with careful semantics.


```rust
// Before
futures::executor::block_on(main_async());
```

```
// After
tigerbeetle::futures_polyfills::block_on(main_async());

// where the implementation looks like this:

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
```

---

&nbsp;

**That was the easy part. Then there's this unsafe goop:**

&nbsp;

---


```rust
fn parker_into_waker(parker: Arc<Parker>) -> Waker {
    let raw_waker = parker_into_raw_waker(parker);
    unsafe { Waker::from_raw(raw_waker) }
}

fn parker_into_raw_waker(parker: Arc<Parker>) -> RawWaker {
    RawWaker::new(Arc::into_raw(parker) as *const (), &VTABLE)
}

const VTABLE: RawWakerVTable = RawWakerVTable::new(clone, wake, wake_by_ref, drop);

unsafe fn clone(ptr: *const ()) -> RawWaker {
    let parker = Arc::from_raw(ptr as *const Parker);
    let cloned = parker.clone();
    let _ = Arc::into_raw(parker); // don't drop the original
    parker_into_raw_waker(cloned)
}

unsafe fn wake(ptr: *const ()) {
    let parker = Arc::from_raw(ptr as *const Parker);
    parker.unpark();
}

unsafe fn wake_by_ref(ptr: *const ()) {
    let parker = Arc::from_raw(ptr as *const Parker);
    parker.unpark();
    let _ = Arc::into_raw(parker); // don't drop
}

unsafe fn drop(ptr: *const ()) {
    let _ = Arc::from_raw(ptr as *const Parker);
}
```




## Step 7: Polyfill `futures-util`

We use the `unfold` method of the `Stream` trait
specifically to write one test case and one doc-comment example,
both specifically needing to demonstate usage of the `unfold` method.
So we need to polyfill `unfold` in a way that reads plausibly like the real `unfold`.

`unfold`'s function signature looks like this:

```rust
pub fn unfold<T, F, Fut, Item>(init: T, f: F) -> Unfold<T, F, Fut>where
    F: FnMut(T) -> Fut,
    Fut: Future<Output = Option<(Item, T)>>,
```

It's a lot to understand and implement,
but what it does is convert repeated calls to a future-returning closure
into a stream of futures.
It's like a closure-to-iterator adapter but for streams.

Here's how to implement it:

```rust
pub trait Stream {
    type Item;
    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>>;
}

pub trait StreamExt: Stream {
    fn next(&mut self) -> Next<'_, Self> where Self: Unpin {
        Next { stream: self }
    }
}

impl<T: Stream + ?Sized> StreamExt for T {}

pub struct Next<'a, S: ?Sized> {
    stream: &'a mut S,
}

impl<S: Stream + Unpin + ?Sized> Future for Next<'_, S> {
    type Output = Option<S::Item>;

    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        Pin::new(&mut *self.stream).poll_next(cx)
    }
}

pub fn unfold<T, F, Fut, Item>(init: T, f: F) -> Unfold<T, F, Fut>
where
    F: FnMut(T) -> Fut,
    Fut: Future<Output = Option<(Item, T)>>,
{
    Unfold { state: Some(init), f, fut: None }
}

pub struct Unfold<T, F, Fut> {
    state: Option<T>,
    f: F,
    fut: Option<Fut>,
}

impl<T, F, Fut> Unpin for Unfold<T, F, Fut> {}

impl<T, F, Fut, Item> Stream for Unfold<T, F, Fut>
where
    F: FnMut(T) -> Fut,
    Fut: Future<Output = Option<(Item, T)>>,
{
    type Item = Item;

    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        let this = unsafe { self.get_unchecked_mut() };

        loop {
            if let Some(fut) = &mut this.fut {
                let fut = unsafe { Pin::new_unchecked(fut) };
                match fut.poll(cx) {
                    Poll::Ready(Some((item, next_state))) => {
                        this.fut = None;
                        this.state = Some(next_state);
                        return Poll::Ready(Some(item));
                    }
                    Poll::Ready(None) => {
                        this.fut = None;
                        this.state = None;
                        return Poll::Ready(None);
                    }
                    Poll::Pending => return Poll::Pending,
                }
            }

            if let Some(state) = this.state.take() {
                this.fut = Some((this.f)(state));
            } else {
                return Poll::Ready(None);
            }
        }
    }
}
```




## Step 8: Polyfill `futures-channel`

We needed [`oneshot`] channels.
This is actually used in the production code path, not just tests,
so we need to be confident about it.

The following is the naive safe implementation I went with.
The real implementation uses atomics directly and is the kind of code one
should consider with extreme suspicion before writing it themselves in production code.

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




## Step 9: Polyfill `bitflags`

`bitflags` fills a Rust language gap for bit-addressable scalar values or bitfields.
The TigerBeetle client has a bitfield in the public API,
so polyfilling it is a fairly big task.

```rust
pub trait Flags: Sized + Copy {
    type Bits: Bits;

    fn bits(&self) -> Self::Bits;
    fn from_bits_retain(bits: Self::Bits) -> Self;

    fn empty() -> Self {
        Self::from_bits_retain(Self::Bits::EMPTY)
    }

    fn all() -> Self;

    fn from_bits(bits: Self::Bits) -> Option<Self> {
        if bits & !Self::all().bits() == Self::Bits::EMPTY {
            Some(Self::from_bits_retain(bits))
        } else {
            None
        }
    }

    fn from_bits_truncate(bits: Self::Bits) -> Self {
        Self::from_bits_retain(bits & Self::all().bits())
    }

    fn is_empty(&self) -> bool {
        self.bits() == Self::Bits::EMPTY
    }

    fn is_all(&self) -> bool {
        (self.bits() & Self::all().bits()) == Self::all().bits()
    }

    fn intersects(&self, other: Self) -> bool {
        (self.bits() & other.bits()) != Self::Bits::EMPTY
    }

    fn contains(&self, other: Self) -> bool {
        (self.bits() & other.bits()) == other.bits()
    }

    fn insert(&mut self, other: Self) {
        *self = Self::from_bits_retain(self.bits() | other.bits());
    }

    fn remove(&mut self, other: Self) {
        *self = Self::from_bits_retain(self.bits() & !other.bits());
    }

    fn toggle(&mut self, other: Self) {
        *self = Self::from_bits_retain(self.bits() ^ other.bits());
    }

    fn set(&mut self, other: Self, value: bool) {
        if value { self.insert(other); } else { self.remove(other); }
    }

    fn intersection(self, other: Self) -> Self {
        Self::from_bits_retain(self.bits() & other.bits())
    }

    fn union(self, other: Self) -> Self {
        Self::from_bits_retain(self.bits() | other.bits())
    }

    fn difference(self, other: Self) -> Self {
        Self::from_bits_retain(self.bits() & !other.bits())
    }

    fn symmetric_difference(self, other: Self) -> Self {
        Self::from_bits_retain(self.bits() ^ other.bits())
    }

    fn complement(self) -> Self {
        Self::from_bits_truncate(!self.bits())
    }
}

pub trait Bits:
    Copy + PartialEq
    + BitAnd<Output = Self> + BitOr<Output = Self>
    + BitXor<Output = Self> + Not<Output = Self>
{
    const EMPTY: Self;
}

impl Bits for u8 { const EMPTY: Self = 0; }
impl Bits for u16 { const EMPTY: Self = 0; }
impl Bits for u32 { const EMPTY: Self = 0; }
impl Bits for u64 { const EMPTY: Self = 0; }
```

Then the macro that generates the actual flag types:

```rust
macro_rules! bitflags {
    (
        $(#[$outer:meta])*
        $vis:vis struct $name:ident: $repr:ty {
            $(
                $(#[$flag_meta:meta])*
                const $flag:ident = $value:expr;
            )*
        }
    ) => {
        $(#[$outer])*
        $vis struct $name($repr);

        #[allow(non_upper_case_globals)]
        impl $name {
            $(
                $(#[$flag_meta])*
                pub const $flag: Self = Self($value);
            )*

            pub const fn bits(&self) -> $repr { self.0 }
            pub const fn empty() -> Self { Self(0) }
            pub const fn all() -> Self { Self(0 $(| $value)*) }

            pub fn from_bits(bits: $repr) -> Option<Self> {
                <Self as Flags>::from_bits(bits)
            }

            pub const fn from_bits_truncate(bits: $repr) -> Self {
                Self(bits & Self::all().bits())
            }

            pub const fn from_bits_retain(bits: $repr) -> Self { Self(bits) }
            pub const fn is_empty(&self) -> bool { self.0 == 0 }
            pub const fn is_all(&self) -> bool {
                (self.0 & Self::all().bits()) == Self::all().bits()
            }
            pub const fn intersects(&self, other: Self) -> bool {
                (self.0 & other.0) != 0
            }
            pub const fn contains(&self, other: Self) -> bool {
                (self.0 & other.0) == other.0
            }

            pub fn insert(&mut self, other: Self) { self.0 |= other.0; }
            pub fn remove(&mut self, other: Self) { self.0 &= !other.0; }
            pub fn toggle(&mut self, other: Self) { self.0 ^= other.0; }
            pub fn set(&mut self, other: Self, value: bool) {
                if value { self.insert(other); } else { self.remove(other); }
            }

            pub const fn intersection(self, other: Self) -> Self { Self(self.0 & other.0) }
            pub const fn union(self, other: Self) -> Self { Self(self.0 | other.0) }
            pub const fn difference(self, other: Self) -> Self { Self(self.0 & !other.0) }
            pub const fn symmetric_difference(self, other: Self) -> Self { Self(self.0 ^ other.0) }
            pub const fn complement(self) -> Self { Self(!self.0 & Self::all().bits()) }
        }

        impl Flags for $name {
            type Bits = $repr;
            fn bits(&self) -> Self::Bits { self.0 }
            fn from_bits_retain(bits: Self::Bits) -> Self { Self(bits) }
            fn all() -> Self { Self(0 $(| $value)*) }
        }

        impl ::core::ops::BitOr for $name {
            type Output = Self;
            fn bitor(self, other: Self) -> Self { self.union(other) }
        }

        impl ::core::ops::BitOrAssign for $name {
            fn bitor_assign(&mut self, other: Self) { self.insert(other); }
        }

        impl ::core::ops::BitAnd for $name {
            type Output = Self;
            fn bitand(self, other: Self) -> Self { self.intersection(other) }
        }

        impl ::core::ops::BitAndAssign for $name {
            fn bitand_assign(&mut self, other: Self) { *self = self.intersection(other); }
        }

        impl ::core::ops::BitXor for $name {
            type Output = Self;
            fn bitxor(self, other: Self) -> Self { self.symmetric_difference(other) }
        }

        impl ::core::ops::BitXorAssign for $name {
            fn bitxor_assign(&mut self, other: Self) { self.toggle(other); }
        }

        impl ::core::ops::Sub for $name {
            type Output = Self;
            fn sub(self, other: Self) -> Self { self.difference(other) }
        }

        impl ::core::ops::SubAssign for $name {
            fn sub_assign(&mut self, other: Self) { self.remove(other); }
        }

        impl ::core::ops::Not for $name {
            type Output = Self;
            fn not(self) -> Self { self.complement() }
        }

        impl ::core::iter::Extend<$name> for $name {
            fn extend<T: ::core::iter::IntoIterator<Item = $name>>(&mut self, iter: T) {
                for item in iter { self.insert(item); }
            }
        }

        impl ::core::iter::FromIterator<$name> for $name {
            fn from_iter<T: ::core::iter::IntoIterator<Item = $name>>(iter: T) -> Self {
                let mut result = Self::empty();
                result.extend(iter);
                result
            }
        }
    };
}
```




## Step 10: Support Rust 1.56

Can't use [`format` captures] anymore.

```rust
// Before
panic!("Unknown CreateAccountResult: {v}");

// After
panic!("Unknown CreateAccountResult: {}", v);
```

Replace [`Path::try_exists`] with [`Path:::exists`].
`try_exists` is more precise about error handling.

```rust
// Before
if !Path::new(&format!("{cargo_manifest_dir}/assets/tb_client.h")).try_exists()? {
// After
if !Path::new(&format!("{}/assets/tb_client.h", cargo_manifest_dir)).exists() {
```

Can`t use [`Mutex`] in `static`s because `Mutex` isn`t `const`.
Need to use [`Once`] or the [`lazy_static`] crate.

```rust
// Before
static GLOBAL_GENERATOR: Mutex<Option<TbidGenerator>> = Mutex::new(None);

// After
static ONCE: Once = Once::new();
static mut GLOBAL_GENERATOR: MaybeUninit<Mutex<TbidGenerator>> = MaybeUninit::uninit();

ONCE.call_once(|| unsafe {
    GLOBAL_GENERATOR.as_mut_ptr().write(Mutex::new(TbidGenerator::new()));
});
```


## Step 11: Remove `rust-version`

`cargo` uses [`rust-version`] manifest field to
verify whether modules are compatible with the Rust toolchain,
introduced in Rust 1.56.

```toml
# Before
[package]
rust-version = "1.63"
```

I think previous toolchains ignore or warn when they see this field.


## Step 12: Edition 2018

Rust Edition 2018 was stabilized in Rust 1.56.
The only significant fallout for the TigerBeetle client
was that the [`TryFrom`] trait was not part of the
prelude in the 2018 edition.

```rust
// Before (implicit)
let x: u32 = value.try_into()?;

// After (explicit import needed)
use std::convert::TryFrom;
let x: u32 = value.try_into()?;
```


## Step 13: Replace `CARGO_TARGET_TMPDIR`

Modern `cargo` provides a temporary directory in its `target` directory
for build scripts to use for their own purpose.
The fix was just to hardcode that same path (`target/tmp`).

```rust
// Before
let tmp_dir = env!("CARGO_TARGET_TMPDIR");

// After
let manifest_dir = env!("CARGO_MANIFEST_DIR");
let tmp_dir = format!("{}/target/tmp", manifest_dir);
```

This fix may not be correct for workspace-based projects
since the `target` directory will not be directly
under the manifest directory.


## Step 14: Support Rust 1.51

The `IntoIterator` trait that enables coercion
from containers to iterators wasn't always defined for arrays.

The only fallout from this was that I needed
to make this one argument a slice instead of array:

```rust
// Before
.args(["ls-files", "-z"])

// After
.args(&["ls-files", "-z"])
```


## Step 15: Support Rust 1.50

[`const` generics] were stabilized in Rust 1.51.
This is the ability to make types and functions
generic over integers.

We use this to make a generic type that holds
an arbitrary number of reserved bytes.

```rust
// Before
pub struct Reserved<const N: usize>([u8; N]);
pub reserved: Reserved<4>,
pub reserved: Reserved<58>,
```

```rust
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

Various trait impls for arrays of lengths > 32 were added in 1.47.
Prior to that, types containing large arrays need manual trait impls.
We had `Reserved` types containing `[u8; 56]`, `[u8; 58]`, etc.,
so derive macros no longer work.

```rust
#[derive(Copy, Clone, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct Reserved58([u8; 58]);
```

```rust
// After: manual impls required for arrays > 32 elements
pub struct Reserved58([u8; 58]);

impl Copy for Reserved58 {}

impl Clone for Reserved58 {
    fn clone(&self) -> Self {
        *self
    }
}

impl Default for Reserved58 {
    fn default() -> Self {
        Self([0; 58])
    }
}

impl core::fmt::Debug for Reserved58 {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        f.debug_tuple("Reserved58").field(&"...").finish()
    }
}

impl Eq for Reserved58 {}

impl PartialEq for Reserved58 {
    fn eq(&self, other: &Self) -> bool {
        self.0[..] == other.0[..]
    }
}

impl Ord for Reserved58 {
    fn cmp(&self, other: &Self) -> core::cmp::Ordering {
        self.0[..].cmp(&other.0[..])
    }
}

impl PartialOrd for Reserved58 {
    fn partial_cmp(&self, other: &Self) -> Option<core::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl core::hash::Hash for Reserved58 {
    fn hash<H: core::hash::Hasher>(&self, state: &mut H) {
        self.0[..].hash(state);
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
