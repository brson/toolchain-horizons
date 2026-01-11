# How To: Remove every dependency from the TigerBeetle Rust client

Not all this work is in mainline TigerBeetle;
it is [on my own branch](https://github.com/brson/tigerbeetle/tree/rustclient-no-deps-do-not-delete).


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

## Step 2: Remove walkdir

## Step 3: Remove anyhow

## Step 4: Remove thiserror

## Step 5: Split futures

## Step 6: Polyfill futures-executor

## Step 7: Polyfill futures-utils

## Step 8: Polyfill futures-channel

## Step 9: Polyfill bitflags

## Step 10: Support Rust 1.56

## Step 11: Remove rust-version

## Step 12: Edition 2018

## Step 13: Replace CARGO_TARGET_TMPDIR

## Step 14: Support Rust 1.51

## Step 15: Support Rust 1.50

## Step 16: Support Rust 1.45

## Step 17: Support Rust 1.42

## Step 18: Support Rust 1.41

## Step 19: Support Rust 1.39
