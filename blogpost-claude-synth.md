# How dependencies destroy your Rust MSRV

During a recent project to get the [Rust client](https://github.com/tigerbeetle/tigerbeetle/tree/main/src/clients/rust) for the [TigerBeetle database](https://tigerbeetle.com/)
ready for production,
I went through the familiar process of establishing the minimum supported version
of the Rust toolchain (MSRV) the crate could support.

It usually goes something like this:

1. Start with the oldest toolchain you can reasonably support
2. Try to build with progressively older toolchains
3. Hit compiler errors or dependency incompatibilities
4. Settle on whatever version actually builds
5. Watch your MSRV creep forward as dependencies update

What I found was, in hindsight, not surprising -
yet it felt surprisingly revelatory at the time,
even though I've gone through this process numerous times:

> If you use any Rust dependencies, even as dev-dependencies,
  you are committing to supporting only 2-3 years of Rust toolchains.

You will likely be chasing toolchain upgrades to stay in that 2-3 year window.

Whether this is good or bad I'm not sure.
I generally think healthy projects should keep their toolchains upgraded.
But _only_ being _able_ to support two years of toolchains feels kinda offensive to me.

I eventually settled on the minimum supported version
being Rust 1.63, from August 2022, about 2.5 years prior to publication.
This appears to be something like the median consensus of the crate ecosystem,
and pushing past that requires increasing effort.

I decided to measure exactly how much each dependency restricts your toolchain horizon.

## The experiment

I took 29 foundational Rust crates (stuff like `serde`, `rand`, `futures`, `log` - the kind of things everybody uses) and for each one I created a minimal project with that single dependency. Then I used binary search to find the oldest Rust toolchain that could compile it.

For comparison, I also tested a control project with zero dependencies.

The setup:
- Edition 2018
- Latest stable version specs (like `"1"` for serde, `"0.3"` for futures)
- Binary search over all stable Rust releases from 1.0.0 to 1.90.0
- Each toolchain can generate its own lockfile, but uses the same manifest

## The results

**Control (no dependencies):** Compiles on Rust 1.16.0 (March 2017) through 1.90.0

That's 74 versions, spanning 7.4 years of Rust history. Pretty good!

Now here's what happens when you add a single dependency:

![Rust Crate Toolchain Compatibility Timeline](rust/compatibility-timeline.png)

### The spectrum of pain

The least restrictive dependencies still hurt:

- `bitflags`, `serde`, `mime`: Require Rust 1.31.1 (Dec 2018)
  - That's **20% version loss**, 1.8 years newer than baseline

Most common crates hit what I'm calling "the 2022 wall":

- `futures`, `log`, `crossbeam`, `syn`, `thiserror`: Require Rust 1.61.0 (May 2022)
  - **61% version loss**, 5.2 years newer
- `rand`, `itertools`, `libc`, `num_cpus`: Require Rust 1.63.0 (Aug 2022)
  - **64% version loss**, 5.4 years newer

Then there are the really aggressive ones:

- `rayon`: Requires Rust 1.80.1 (Aug 2024)
  - **86% version loss** - only 4 months old when I ran this!
- `backtrace`: Requires Rust 1.82.0 (Oct 2024)
  - **89% version loss** - basically requires the latest toolchain

## What this actually means

If you're writing a library and you add `rand` or `itertools`, you just eliminated the entire 2017-2021 era. Five years of Rust history, gone. Your MSRV is now "August 2022 or newer."

And it's not like these are weird experimental crates - 16 out of the 29 I tested require Rust from 2022 or later.

The really striking thing is the **time compression**. Your compatibility window shrinks from 7.4 years to potentially just a few months. Not because you did anything wrong, but because your dependency adopted some new language feature.

## The 2022 wall

More than half the crates I tested cluster around Rust 1.61-1.63 (mid-2022). I don't know exactly why there's such a strong cutoff there, but my guess is it's related to some combination of:
- Generic associated types stabilizing in 1.65
- The 2021 edition pushing people to update their baseline
- General ecosystem momentum toward newer features

Whatever the reason, if you're picking dependencies today, there's a good chance they're going to require a 2022+ toolchain.

## Edition 2018 vs 2021

This experiment used edition 2018, which has a baseline of Rust 1.31.0. If I'd used edition 2021, the control case would jump to Rust 1.56.0 (Oct 2021), eliminating another ~40 versions right off the bat.

So the edition choice matters, but dependencies matter way more.

## Is this just Rust?

I was curious if this phenomenon was unique to Rust, so I ran the same experiment on Python, Java, and Node.js.

Short answer: **yes, this is mostly a Rust thing**.

- **Java**: All 26 packages I tested work on Java 8 through Java 23. Ten years of backward compatibility. Dependencies have essentially zero impact on your toolchain horizon.

- **Python**: 16 out of 19 packages work on Python 3.8-3.13 (the full range). Only numpy required a newer version (3.9+). Dependencies barely matter.

- **Node.js**: More like Rust - 33% of packages work on Node 14+, but 24% require Node 20+ (released 2023). The ecosystem moves fast and drops old versions.

The JVM's bytecode compatibility and the ecosystem's commitment to long-term support mean you can use cutting-edge libraries while supporting decade-old Java versions. Python's slower language evolution keeps compatibility broad. Node and Rust both move fast and break things.

(Full cross-language results in the coda below, for the curious.)

## Takeaways

If you're a library author who cares about MSRV:
- Every dependency is expensive
- Even "stable" foundational crates march forward
- Check the MSRV policies of your dependencies
- Consider if you really need that dep

If you're an application author:
- You probably don't care as much, but know that your MSRV is determined by your most aggressive dependency
- Want to support older systems? Audit your deps

I'm not saying "never use dependencies" - that would be silly. But the cost is real and it's higher than I expected. A single `rand` or `futures` dependency cuts out five years of Rust history.

This isn't necessarily bad. Rust is evolving fast, and that's part of what makes it exciting. But it's a tradeoff: innovation vs compatibility. Other ecosystems made different choices.

Anyway, full results and the experiment code are [on GitHub](https://github.com/brson/dep-tool-comp).

---

## Coda: Cross-language comparison

For the curious, here are the detailed results from testing Python, Java, and Node.js.

### Python: Surprisingly broad compatibility

**Control (no dependencies):** Python 3.8 (Oct 2019) → 3.13 (Oct 2024) - **6 years**

Python dependencies showed minimal restriction:

- **16/19 packages** work on Python 3.8-3.13 (same as control)
- **numpy**: Requires Python 3.9+ (lost only 1 version)
- **3 packages** had installation issues (likely binary compilation, not Python version issues)

Tested packages: certifi, charset-normalizer, click, idna, jinja2, markupsafe, packaging, platformdirs, pluggy, pytest, pytz, requests, setuptools, six, urllib3, numpy, pillow, pyyaml, python-dateutil

### Java: Exceptional backward compatibility

**Control (no dependencies):** Java 8 (2014) → Java 23 (2024) - **10+ years**

**ALL 26 packages tested work on Java 8 through Java 23.**

This includes cutting-edge versions like JUnit 6.0.0-RC3, OkHttp 5.0.0-alpha.17, and Jackson 2.20.0.

Tested packages: Apache Commons (lang3, io, collections4, text, math3, csv), SLF4J, Logback, Gson, Jackson, JUnit 5, Mockito, AssertJ, Guava, Apache HttpClient, OkHttp, Joda-Time, RxJava, H2, PostgreSQL driver, HikariCP, DOM4J, SnakeYAML, javax.inject, Guice, Jakarta Validation API

### Node.js: Active version churn

**Control (no dependencies):** Node 14 (2020) → Node 24 (2024) - **~4 years**

Node showed significant dependency restrictions:

- **33%** of packages work on Node 14+
- **29%** require Node 18+ (2022)
- **24%** require Node 20+ (2023)
- **10%** failed on all versions tested

Popular packages with strict requirements:
- **express, koa**: Require Node 18+
- **commander, yargs**: Require Node 20+
- **jest, mocha**: Require Node 18+

Tested packages: express, koa, lodash, date-fns, uuid, axios, node-fetch, jest, mocha, vitest, async, commander, yargs, chalk, fs-extra, glob, joi, zod, pg, winston, pino

### Why these differences exist

**Java's excellence** comes from:
- Strict bytecode compatibility guarantees
- Multi-release JAR support (ship multiple bytecode versions in one artifact)
- Strong cultural commitment to backward compatibility
- Long LTS support windows (8+ years)

**Python's stability** comes from:
- Slower language evolution (compared to Rust)
- `python_requires` metadata enforcement
- Cultural emphasis on compatibility
- Mature ecosystem with stable interfaces

**Rust's restrictions** come from:
- Rapid language evolution (new editions, features every 6 weeks)
- Libraries adopting new features quickly
- No enforcement of MSRV in manifests (until recently)
- Cultural acceptance of moving fast

**Node's churn** comes from:
- Rapid release cycle (major version every 6 months)
- Shorter LTS windows (3 years)
- ESM/CommonJS transition
- "Move fast" culture

---

## Methodology notes

**Rust experiment:**
- Version specs used major versions for >= 1.0 crates, major.minor for < 1.0
- All tests allowed different Cargo.lock files per toolchain
- One crate (derive_more) failed to compile and was excluded
- Tested on Linux, October 2024
- Toolchain versions are the latest point releases only (so 1.63.0, not 1.63.1)
- Binary search used: testing log₂(90) ≈ 7 versions per crate instead of all 90

**Other languages:**
- Python: Binary search using `uv` package manager with import validation
- Java: Binary search using Maven with compile validation
- Node: Binary search using nvm with runtime import validation
- All used major version specs to allow maximum dependency flexibility

Full experimental code and raw data available in the [GitHub repository](https://github.com/brson/dep-tool-comp).
