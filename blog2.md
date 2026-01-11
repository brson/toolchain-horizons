# How To: Remove every dependency from the TigerBeetle Rust client

I [previously conducted an experiment](blog1.md)
to help me understand how depending on Rust crates
affected my own ability to support prior Rust toolchain versions
in the [TigerBeetle] Rust client.

As part of that experiment I removed every dependency,
and also pushed back the minimum supported Rust version as far
as I could, to version 1.39 (from todo date).

This followup describes in detail each step I took
to establish a very early MSVR on a very small Rust project.
May it be interesting to some Rust programmers.

> Not all this work is in mainline TigerBeetle;
  it is [on my own branch](https://github.com/brson/tigerbeetle/tree/rustclient-no-deps-do-not-delete).

The below table shows what I had to do to support progressively
older versions of the Rust compiler.
Links generally go to interesting places,
with the "step" links leading to a detailed description of
how I enabled compatibility with that version.


| Step | Rust | Commit   | Action   | Features                                                     |
|------|------|----------|----------|--------------------------------------------------------------|
| [1]  | *    | [`4c85`] | Remove   | `ignore`                                                     |
| [2]  | *    | [`e67f`] | Remove   | `walkdir`                                                    |
| [3]  | *    | [`4bef`] | Remove   | `anyhow`                                                     |
| [4]  | 1.61 | [`65d9`] | Remove   | `thiserror`                                                  |
| [5]  | 1.56 | [`f7cc`] | Split    | `futures` → `-channel`, `-executor`, `-util`                 |
| [6]  | 1.56 | [`abd5`] | Polyfill | `futures-executor`                                           |
| [7]  | 1.56 | [`632b`] | Polyfill | `futures-utils`                                              |
| [8]  | 1.56 | [`381d`] | Polyfill | `futures-channel`                                            |
| [9]  | 1.56 | [`46bf`] | Polyfill | `bitflags`                                                   |
| [10] | 1.56 | [`fcc1`] | Rework   | format string captures, `Path::try_exists`, `const Mutex::new` |
| [11] | 1.56 | [`db93`] | Remove   | `rust-version` (manifest)                                    |
| [12] | 1.55 | [`71b5`] | Rework   | Edition 2021→2018, `use std::convert::TryFrom`               |
| [13] | 1.53 | [`dad2`] | Replace  | `CARGO_TARGET_TMPDIR`                                        |
| [14] | 1.51 | [`c459`] | Rework   | `IntoIterator` for arrays (introduced 1.53)                  |
| [15] | 1.50 | [`ff9c`] | Rework   | `const` generics (introduced 1.51)                           |
| [16] | 1.45 | [`76d5`] | Rework   | `Array` impl for lengths > 32 (extended 1.47)                |
| [17] | 1.42 | [`f0db`] | Replace  | associated constants (`u64::MAX`) (introduced 1.43)          |
| [18] | 1.41 | [`f3ac`] | Replace  | `matches!` (stabilized 1.42)                                 |
| [19] | 1.39 | [`02a8`] | Rework   | `todo!`, `mem::take`, `#[non_exhaustive]` (stabilized 1.40)  |

> *: `ignore` and `walkdir` are highly compatible back to Edition 2018 (Rust 1.31),
  and neither declares a `rust-version`.
  I removed them anyway as part of this exercise.

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

## Step 1: Remove ignore

Replaced the `ignore` crate's git-aware directory walker with `walkdir`.

## Step 2: Remove walkdir

Replaced `walkdir` with `git ls-files` command to enumerate source files:

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

## Step 3: Remove anyhow

Replaced `anyhow::Result` with `Result<T, Box<dyn std::error::Error>>`.

## Step 4: Remove thiserror

Replaced thiserror's derive macros with manual `Display` and `Error` impls:

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

## Step 5: Split futures

Split the monolithic `futures` crate into `futures-channel`, `futures-executor`, and `futures-util`.

## Step 6: Polyfill futures-executor

Implemented a minimal `block_on` executor using raw waker API and condition variables:

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

## Step 7: Polyfill futures-utils

Extended `futures_polyfills.rs` with join/select utilities.

## Step 8: Polyfill futures-channel

Implemented custom oneshot channel using `Arc`, `Mutex`, and `Waker`:

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

This achieved **zero runtime dependencies**.

## Step 9: Polyfill bitflags

Implemented a complete `bitflags!` macro compatible with bitflags 2.6 API:

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

## Step 10: Support Rust 1.56

- `{variable}` → `{}, variable` (captured identifiers stabilized 1.58)
- `Path::try_exists()` → `Path::exists()` (stabilized 1.63)
- `const Mutex::new()` → `Once` + `MaybeUninit` pattern (stabilized 1.63)

## Step 11: Remove rust-version

Remove `rust-version` field from Cargo.toml to allow building on older toolchains.

## Step 12: Edition 2018

- Edition 2021 → 2018
- Add explicit `use std::convert::TryFrom` (in prelude for 2021, not 2018)

## Step 13: Replace CARGO_TARGET_TMPDIR

`env!("CARGO_TARGET_TMPDIR")` → `format!("{}/target/tmp", manifest_dir)` (stabilized 1.54)

## Step 14: Support Rust 1.51

`.args([...])` → `.args(&[...])` (`IntoIterator` for arrays stabilized 1.53)

## Step 15: Support Rust 1.50

Replace `Reserved<N>` const generic type with specific `Reserved4`, `Reserved6`, etc. (const generics stabilized 1.51)

## Step 16: Support Rust 1.45

Manual `Debug`, `Copy`, `Clone`, `Eq`, `PartialEq`, `Ord`, `PartialOrd`, `Hash` impls for Reserved types. (Array trait impls for lengths > 32 extended in 1.47)

## Step 17: Support Rust 1.42

`u64::MAX` → `core::u64::MAX` (associated constants on primitives stabilized 1.43)

## Step 18: Support Rust 1.41

`matches!(expr, pattern)` → `match expr { pattern => true, _ => false }` (stabilized 1.42)

## Step 19: Support Rust 1.39

- `todo!` → `unimplemented!` (stabilized 1.40)
- `mem::take` → `mem::replace(&mut x, Default::default())` (stabilized 1.40)
- Remove `#[non_exhaustive]` (stabilized 1.40)
