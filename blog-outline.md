# Blog Post Outline: Toolchain Horizons

## Narrative Arc

The presentation tells a personal story about discovering and addressing a hidden problem in the Rust ecosystem: how dependencies dramatically restrict your toolchain compatibility.

---

## Section 1: The Setup

**Hook**: I made a TigerBeetle Rust client and got mad about dependencies.

Introduce:
- Brian Anderson (Rust background, Mozilla years)
- TigerBeetle (database company, Zig core, strong philosophy)
- The TigerBeetle Rust client project

### The Rust Client

Key characteristics:
- Small — < 2 kloc
- `async` / `await`
- FFI — mostly unsafe
- Partially code-generated

```rust
pub fn lookup_transfers(
    &self,
    events: &[u128],
) -> impl Future<...> {
    let (packet, rx) = create_packet(
        TB_OPERATION_LOOKUP_TRANSFERS,
        events,
    );

    unsafe {
        tb_client_submit(
            self.client,
            Box::into_raw(packet),
        );
    }

    async {
        let msg = rx.await?;
        let responses = handle_message(&msg)?;
        Ok(Vec::from(responses))
    }
}
```

### Initial MSRV Discovery

Process of establishing MSRV:
1. "We support Rust version N"
2. `N = N-1`
3. `cargo +N test`
4. Fix build (or give up)

**Result**: Initial MSRV was Rust 1.81 (September 2024) — only 9 months old!

Blockers:
- `fs::exists` in build script (stabilized 1.81)
- Cargo.lock v4 format (May 2024)

---

## Section 2: The TigerStyle Mindset

Interlude on TigerBeetle's philosophy (tigerbeetle/docs/TIGER_STYLE.md):
- Safety, performance, developer UX
- **No dependencies**

### Initial Dependencies

```toml
[dependencies]
bitflags = "2.6.0"
futures = "0.3.31"
thiserror = "2.0.3"

[build-dependencies]
anyhow = "1.0.93"
ignore = "0.4.23"

[dev-dependencies]
anyhow = "1.0.93"
tempfile = "3.15.0"
```

---

## Section 3: The Futures Problem

### The Dependency Tree

```
futures v0.3.31
├── futures-channel v0.3.31
│   ├── futures-core v0.3.31
│   └── futures-sink v0.3.31
├── futures-core v0.3.31
├── futures-executor v0.3.31
│   ├── futures-core v0.3.31
│   ├── futures-task v0.3.31
│   └── futures-util v0.3.31
│       ├── futures-channel v0.3.31 (*)
│       ├── futures-core v0.3.31
│       ├── futures-io v0.3.31
│       ├── futures-macro v0.3.31 (proc-macro)
│       │   ├── proc-macro2 v1.0.90
│       │   │   └── unicode-ident v1.0.14
│       │   ├── quote v1.0.37
│       │   │   └── proc-macro2 v1.0.90 (*)
│       │   └── syn v2.0.88
│       │       ├── proc-macro2 v1.0.90 (*)
│       │       ├── quote v1.0.37 (*)
│       │       └── unicode-ident v1.0.14
│       ├── futures-sink v0.3.31
│       ├── futures-task v0.3.31
│       ├── memchr v2.7.4
│       ├── pin-project-lite v0.2.15
│       ├── pin-utils v0.1.0
│       └── slab v0.4.9
├── futures-io v0.3.31
├── futures-sink v0.3.31
├── futures-task v0.3.31
└── futures-util v0.3.31 (*)
```

Highlight: `syn` crate deep in the tree.

### The Moment of Madness

**Story beat**: syn published a point release bumping MSRV from 1.63 to 1.68, breaking the build of our 3-dependency crate.

This is when Brian got mad.

---

## Section 4: The Experiment

### Methodology

- Pick ~30 popular Rust crates
- Compile each against ~every Rust toolchain (1.31 to 1.90)
- Report the oldest compatible version

### Crates Tested

serde, anyhow, futures, syn, rayon, walkdir, rand, regex, chrono, crossbeam, log, thiserror, bitflags, itertools, libc, num_cpus, backtrace, etc.

### Results Visualization

[compatibility-timeline-rust.png]

---

## Section 5: The syn/proc-macro2 Epoch

**Key insight**: The minimum Rust version supported by most of the Rust ecosystem is limited by the `syn` and `proc-macro2` crates.

They are used by most procedural macros.

---

## Section 6: The Compatibility Quest

### Timeline of Progress

| MSRV | Date | Blocker |
|------|------|---------|
| 1.81 | Sep 2024 | Initial MSRV — `fs::exists` |
| 1.68 | Mar 2023 | **futures / syn / proc-macro2** |
| 1.56 | Oct 2021 | `bitflags`, edition 2018 |
| 1.51 | Mar 2021 | const generics |
| 1.47 | Oct 2020 | array traits > 32 |
| 1.42 | Mar 2020 | `matches!`, `u64::MAX` |
| 1.39 | Nov 2019 | **async/await minimum** |

### Removing the `futures` Dependency

#### Step 1: Break Out Sub-crates

```toml
# Before
[dependencies]
futures = "0.3.31"

# After
[dependencies]
futures-channel = "0.3.31"

[dev-dependencies]
futures-executor = "0.3.31"
futures-util = "0.3.31"
```

#### Step 2: Polyfill `block_on`

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

88 lines total including:
- Parker struct with Mutex<bool> + Condvar
- RawWakerVTable with 4 unsafe functions
- Manual Arc reference counting

#### Step 3: Polyfill Stream Utilities

```rust
// Reimplemented from futures-util:
pub trait Stream { ... }           // 8 lines
pub trait StreamExt { ... }        // 12 lines
pub struct Next<'a, S> { ... }     // 15 lines
pub fn unfold<T, F, Fut, Item>     // 45 lines
pub struct Unfold<T, F, Fut>       // 35 lines
macro_rules! pin_mut! { ... }      // 10 lines
```

120 lines total.

#### Step 4: Polyfill Oneshot Channel

```rust
struct OneshotFuture<T> { shared: Arc<OneshotShared<T>> }
struct OneshotShared<T> { waker: Mutex<Option<Waker>>,
                          value: Mutex<Option<T>> }
struct OneshotSender<T> { shared: Arc<OneshotShared<T>> }

impl<T> Future for OneshotFuture<T> { /* 12 lines */ }
impl<T> OneshotSender<T> { fn send(self, value: T) { /* 10 lines */ } }
```

60 lines — **final runtime dependency removed!**

### Total Polyfill Cost

```
futures crate removed: -1 dependency
polyfill code added:   +270 lines
  - block_on:      88 lines
  - Stream utils: 120 lines
  - oneshot:       60 lines
```

---

## Section 7: Was It Worth It?

Open question for the reader.

Considerations:
- Can't use tokio in examples/docs anyway (not zero-dep)
- 270 lines of polyfill code to maintain
- 5 years of backwards compatibility gained

---

## Appendix A: Full Rust Experiment Results

| Crate | Version | Oldest Rust |
|-------|---------|-------------|
| CONTROL | - | 1.16.0 |
| mime | 0.3.17 | 1.31.1 |
| serde | 1.0.228 | 1.31.1 |
| walkdir | 2.5.0 | 1.31.1 |
| cfg-if | 1.0.4 | 1.32.0 |
| hex | 0.4.3 | 1.36.0 |
| anyhow | 1.0.100 | 1.38.0 |
| regex | 1.12.2 | 1.51.0 |
| semver | 1.0.27 | 1.51.0 |
| bitflags | 2.10.0 | 1.56.1 |
| unicode-segmentation | 1.12.0 | 1.56.1 |
| byteorder | 1.5.0 | 1.60.0 |
| crossbeam | 0.8.4 | 1.61.0 |
| log | 0.4.28 | 1.61.0 |
| chrono | 0.4.42 | 1.62.1 |
| itertools | 0.14.0 | 1.63.0 |
| libc | 0.2.177 | 1.63.0 |
| num_cpus | 1.17.0 | 1.63.0 |
| rand | 0.9.2 | 1.63.0 |
| tempfile | 3.23.0 | 1.65.0 |
| extension-trait | 1.0.2 | 1.68.2 |
| **futures** | 0.3.31 | **1.68.2** |
| **syn** | 2.0.110 | **1.68.2** |
| **thiserror** | 1.0.69 | **1.68.2** |
| socket2 | 0.6.1 | 1.70.0 |
| env_logger | 0.11.8 | 1.71.1 |
| toml | 0.9.8 | 1.76.0 |
| **rayon** | 1.11.0 | **1.80.1** |
| backtrace | 0.3.76 | 1.82.0 |
| url | 2.5.7 | 1.83.0 |

Key observations:
- **1.68** is the "syn epoch" — many proc-macro-using crates cluster here
- Some foundational crates (serde, walkdir, mime) maintain excellent compatibility
- rayon and backtrace require very recent toolchains

---

## Appendix B: TigerBeetle Rust Client Dependency Removal History

### Full Commit Sequence

| Commit | Dependency Removed | Lines Changed |
|--------|-------------------|---------------|
| 65d9b96fa | thiserror | +209/-139 |
| 4c85201a2 | ignore | +31/-727 |
| e67f1867f | walkdir | +15/-20 |
| 4befa9de6 | anyhow | +53/-53 |
| f7cc94b53 | futures (split) | +9/-8 |
| abd5b9774 | futures-executor | +99/-8 |
| 632b5ed6d | futures-util | +130/-17 |
| 381de6c81 | futures-channel | +77/-17 |
| 46bf3a169 | bitflags | +421/-3 |

---

## Appendix C: Other Languages

### Java

Java doesn't seem to have this problem. (needs investigation)

### Go

- Modules introduced Go 1.13 (September 2019)
- ~60% of tested crates compatible with 1.13
- Modern web frameworks (gin, echo, grpc) require Go 1.21+
- Google libraries tend to require recent Go versions

[compatibility-timeline-go.png]

---

## Links

- GitHub: https://github.com/brson/toolchain-horizons
- TigerBeetle: https://tigerbeetle.com
- TigerStyle: tigerbeetle/docs/TIGER_STYLE.md
- Original PR: https://github.com/tigerbeetle/tigerbeetle/pull/3254
