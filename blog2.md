# How To: Remove every dependency from the TigerBeetle Rust client

| Step | Rust Version | Action   | Features                                                              |
|------|--------------|----------|-----------------------------------------------------------------------|
| 1    |              | Remove   | `thiserror`                                                           |
| 2    |              | Remove   | `ignore`                                                              |
| 3    |              | Remove   | `walkdir`                                                             |
| 4    |              | Remove   | `anyhow`                                                              |
| 5    |              | Split    | `futures` → `futures-channel`, `futures-executor`, `futures-util`     |
| 6    |              | Polyfill | `futures-executor`                                                    |
| 7    |              | Polyfill | `futures-utils`                                                       |
| 8    |              | Polyfill | `futures-channel`                                                     |
| 9    |              | Polyfill | `bitflags`                                                            |
| 10   | 1.56         | Rework   | format string captures, `Path::try_exists`, `const Mutex::new`        |
| 11   | ?            | Remove   | `rust-version` (manifest)                                             |
| 12   | ?            | Rework   | Edition 2024→2018, `use std::convert::TryFrom`                        |
| 13   | 1.53         | Replace  | `CARGO_TARGET_TMPDIR`                                                 |
| 14   | 1.51         | Rework   | `IntoIterator` for arrays (introduced 1.53)                           |
| 15   | 1.50         | Rework   | `const` generics (introduced 1.51)                                    |
| 16   | 1.45         | Rework   | `Array` impl for lengths > 32 (extended 1.47)                         |
| 17   | 1.42         | Replace  | associated constants on primitives (`u64::MAX`) (introduced 1.43)     |
| 19   | 1.41         | Replace  | `matches!` (stabilized 1.42)                                          |
| 20   | 1.39         | Rework   | `todo!`, `mem::take`, `#[non_exhaustive]` (stabilized 1.40)           |
