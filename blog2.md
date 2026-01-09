# How To: Remove every dependency from the TigerBeetle Rust client

Not all this work is in mainline TigerBeetle;
it is [on my own branch](https://github.com/brson/tigerbeetle/tree/rustclient-no-deps-do-not-delete).


| Step | Rust | Commit   | Action   | Features                                                          |
|------|------|----------|----------|-------------------------------------------------------------------|
| 1    | 1.63 | [`65d9`] | Remove   | `thiserror` (MSRV 1.61)                                           |
| 2    | 1.63 | [`4c85`] | Remove   | `ignore`                                                          |
| 3    | 1.63 | [`e67f`] | Remove   | `walkdir`                                                         |
| 4    | 1.63 | [`4bef`] | Remove   | `anyhow` (MSRV 1.39)                                              |
| 5    | 1.63 | [`f7cc`] | Split    | `futures` (MSRV 1.56) → `futures-channel`, `-executor`, `-util`   |
| 6    | 1.63 | [`abd5`] | Polyfill | `futures-executor` (MSRV 1.56)                                    |
| 7    | 1.63 | [`632b`] | Polyfill | `futures-utils` (MSRV 1.56)                                       |
| 8    | 1.63 | [`381d`] | Polyfill | `futures-channel` (MSRV 1.56)                                     |
| 9    | 1.63 | [`46bf`] | Polyfill | `bitflags` (MSRV 1.56)                                            |
| 10   | 1.56 | [`fcc1`] | Rework   | format string captures, `Path::try_exists`, `const Mutex::new`    |
| 11   | 1.56 | [`db93`] | Remove   | `rust-version` (manifest)                                         |
| 12   | 1.31 | [`71b5`] | Rework   | Edition 2021→2018, `use std::convert::TryFrom`                    |
| 13   | 1.53 | [`dad2`] | Replace  | `CARGO_TARGET_TMPDIR`                                             |
| 14   | 1.51 | [`c459`] | Rework   | `IntoIterator` for arrays (introduced 1.53)                       |
| 15   | 1.50 | [`ff9c`] | Rework   | `const` generics (introduced 1.51)                                |
| 16   | 1.45 | [`76d5`] | Rework   | `Array` impl for lengths > 32 (extended 1.47)                     |
| 17   | 1.42 | [`f0db`] | Replace  | associated constants (`u64::MAX`) (introduced 1.43)               |
| 19   | 1.41 | [`f3ac`] | Replace  | `matches!` (stabilized 1.42)                                      |
| 20   | 1.39 | [`02a8`] | Rework   | `todo!`, `mem::take`, `#[non_exhaustive]` (stabilized 1.40)       |

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
