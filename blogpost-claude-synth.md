# How dependencies destroy your Rust MSRV

I was working on the [Rust client](https://github.com/tigerbeetle/tigerbeetle/tree/main/src/clients/rust) for the [TigerBeetle database](https://tigerbeetle.com/),
getting it ready for production,
when I hit the familiar wall of MSRV determination.

You know the drill:
start optimistically with an ancient toolchain,
binary search your way up through compiler errors and dependency failures,
settle on whatever actually builds,
then watch your MSRV creep forward anyway as your dependencies update under you.

I had this moment of clarity -
one of those things that's obvious in retrospect but hits you sideways anyway,
even after doing it a dozen times:

> If you use any Rust dependencies, even as dev-dependencies,
  you are committing to supporting only 2-3 years of Rust toolchains.

And you will spend time chasing toolchain upgrades to stay in that window.

Is this good or bad? I don't know.
I believe healthy projects should keep their toolchains upgraded.
But _only_ being able to support two years of toolchains feels kinda offensive to me,
especially for a language that prides itself on stability guarantees.

I settled on Rust 1.63, from August 2022, about 2.5 years before publication.
This appears to be the median consensus of the ecosystem right now.
Pushing past it requires increasing effort, and at some point you just give up.

But I wanted to know: exactly how much does each dependency cost?

## The experiment

I took 29 foundational Rust crates -
the usual suspects like `serde`, `rand`, `futures`, `log`,
the kind of things that show up in every `Cargo.toml` -
and for each one created a minimal project with that single dependency.
Then I binary searched through Rust's release history to find the oldest toolchain that could compile it.

For comparison, I tested a control project with zero dependencies.

The setup:
- Edition 2018
- Latest stable version specs (`"1"` for serde, `"0.3"` for futures)
- Binary search over all stable Rust releases from 1.0.0 to 1.90.0
- Each toolchain can generate its own lockfile, but uses the same manifest

I wrote some quick automation to do the binary search,
and honestly I should have done this years ago.
It's satisfying to just let the computer tell you the answer instead of guessing.

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

I got curious whether this was unique to Rust,
or if I'd just been living in my Rust bubble for too long.
So I ran the same experiment on Python, Java, and Node.js.

Short answer: **yes, this is mostly a Rust thing**.

- **Java**: All 26 packages I tested work on Java 8 through Java 23. Ten years of backward compatibility. Dependencies have essentially zero impact on your toolchain horizon.

- **Python**: 16 out of 19 packages work on Python 3.8-3.13 (the full range). Only numpy required a newer version (3.9+). Dependencies barely matter.

- **Node.js**: More like Rust - 33% of packages work on Node 14+, but 24% require Node 20+ (released 2023). The ecosystem moves fast and drops old versions.

The JVM's bytecode compatibility and cultural commitment to long-term support mean you can use cutting-edge libraries while supporting decade-old Java versions.
Python's slower language evolution keeps compatibility broad.
Node and Rust both move fast and break things.

I spent years working on Rust at Mozilla,
watching us obsess over stability guarantees and backwards compatibility.
The irony is that while _rustc_ rarely breaks your code,
the ecosystem doesn't share that discipline.
Every crate author makes their own tradeoffs,
and collectively we've ended up with a 2-3 year compatibility window.

(Full cross-language results in the coda below if you want the details.)

## Takeaways

If you're a library author who cares about MSRV:
- Every dependency is expensive
- Even "stable" foundational crates march forward
- Check the MSRV policies of your dependencies
- Consider if you really need that dep

If you're an application author:
- You probably don't care as much, but your MSRV is determined by your most aggressive dependency
- Want to support older systems? Audit your deps first

I'm not saying "never use dependencies."
That would be silly, and I've written enough from-scratch code in my life to know it's usually a mistake.
But the cost is real and higher than I expected.
A single `rand` or `futures` dependency cuts out five years of Rust history.

This isn't necessarily bad.
Rust is evolving fast, and that's part of what makes it exciting.
But it's a tradeoff: innovation vs compatibility.
Other ecosystems made different choices.

The Rust I helped build at Mozilla obsessed over backwards compatibility,
and I'm proud of that work.
But the Rust ecosystem is its own thing now,
with its own values and priorities.
Watching it evolve from the sidelines is fascinating,
even when it goes directions I wouldn't have chosen.

Anyway, full results and the experiment code are [on GitHub](https://github.com/brson/dep-tool-comp).

---

## Postscript: On writing this with Claude Code

I wrote most of this post by hand,
but I used Claude Code to help me run the experiments and organize the data.
This was exactly the kind of tedious-but-straightforward automation work that AI is good at:
binary searching through toolchain versions,
running builds in Docker containers,
collecting and formatting results.

The funny thing is,
I still had to know what I was doing.
Claude helped me avoid a bunch of stupid mistakes with iterator adapters and error handling,
but it also confidently suggested things that were wrong,
and I had to know enough to catch them.

It's a useful tool.
Not a replacement for understanding,
but a way to move faster when you do understand.
Kind of like a really helpful but occasionally overconfident intern.

I'm not sure what to make of it yet.

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

A note on the code:
I had Claude Code help me write the binary search logic,
and we went through a few iterations to get the iterator adapters right.
It suggested a verbose but clear implementation first,
then we refined it to something more concise and idiomatic.
The back-and-forth reminded me that even for straightforward algorithms,
there's often a tension between "obviously correct" and "elegantly concise."
I tend to err on the side of concise these days,
but I can see the argument for verbose when the code is meant to be copied.

Full experimental code and raw data available in the [GitHub repository](https://github.com/brson/dep-tool-comp).
