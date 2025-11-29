# How dependencies shrink your toolchain compatibility window

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

This got me thinking: how much does each dependency actually restrict your toolchain horizon?
And is this phenomenon unique to Rust, or universal across programming ecosystems?

I decided to measure it.

## The experiment

I tested 4 popular programming languages to see how dependencies affect toolchain compatibility:

- **Rust**: 30 foundational crates
- **Python**: 19 common packages
- **Java**: 26 popular libraries
- **Node.js**: 21 essential packages

(I also attempted Go, but the experiment infrastructure had issues.
Go's module system and rapid language evolution since 1.18 suggested
it would fall somewhere between Rust and Node in terms of restrictions.)

For each language, I created a control project with no dependencies,
then tested individual dependencies to find the oldest and newest toolchain version
that could successfully build/run the project.

The methodology was consistent across languages:
- Use major version specs to allow maximum dependency flexibility
- Binary search to efficiently find compatibility boundaries
- Validate with actual compilation/execution, not just metadata

## The results

### Rust: Dependencies cut compatibility dramatically

**Control (no dependencies):** Rust 1.16.0 (Mar 2017) → 1.90.0 (Jun 2024) - **74 versions, 7.4 years**

The no-dependency baseline is remarkable.
A simple Rust 2018 edition crate can compile on toolchains spanning 7.4 years of Rust history.

But add a single dependency and that window shrinks fast:

![Rust Crate Toolchain Compatibility Timeline](rust/compatibility-timeline.png)

- **bitflags 1.x**: Rust 1.31+ only (lost 20% of versions)
- **futures 0.3**: Rust 1.61+ only (lost 61% of versions)
- **num_cpus 1.x**: Rust 1.63+ only (lost 64% of versions)
- **rayon 1.x**: Rust 1.80+ only (lost 86% of versions)
- **backtrace 0.3**: Rust 1.82+ only (lost 89% of versions)

Most crates cluster around Rust 1.60-1.63 (May-August 2022),
giving you a compatibility window of just 2-3 years instead of 7+.

**Key finding**: A single Rust dependency typically eliminates 50-60% of your potential toolchain compatibility.
The ecosystem has collectively settled on supporting roughly 2 years of Rust history.

### Python: Surprisingly broad compatibility

**Control (no dependencies):** Python 3.8 (Oct 2019) → 3.13 (Oct 2024) - **6 years**

Python dependencies showed minimal restriction:

- **16/19 packages** work on Python 3.8-3.13 (same as control)
- **numpy**: Requires Python 3.9+ (lost only 1 version)
- **3 packages** had installation issues (likely binary compilation, not Python version issues)

**Key finding**: Python dependencies barely affect your compatibility window.
The ecosystem maintains broad version support, likely due to slower language evolution
and strong backward compatibility culture.

### Java: Exceptional backward compatibility

**Control (no dependencies):** Java 8 (2014) → Java 23 (2024) - **10+ years**

Java showed the most remarkable result:

**ALL 26 packages tested work on Java 8 through Java 23.**

This includes cutting-edge versions like:
- JUnit 6.0.0-RC3
- OkHttp 5.0.0-alpha.17
- Jackson 2.20.0

**Key finding**: Java dependencies have virtually zero impact on toolchain compatibility.
The JVM's bytecode compatibility and the ecosystem's commitment to long-term support
mean you can use modern libraries while supporting decade-old JVMs.

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

**Key finding**: Node dependencies significantly restrict your toolchain horizon.
The ecosystem moves fast and actively drops support for older versions,
reflecting a "move fast, break compatibility" philosophy.

## Cross-language comparison

| Language | Control Range | Typical with Deps | % Lost |
|----------|---------------|-------------------|--------|
| **Rust** | 74 versions (7.4 years) | ~30 versions (2-3 years) | **60%** |
| **Python** | 6 versions (6 years) | 5-6 versions (5-6 years) | **0-17%** |
| **Java** | 10+ years | 10+ years | **0%** |
| **Node** | 4 years | 2-3 years | **25-50%** |

The spectrum from Java's perfect compatibility to Rust's dramatic restrictions
reveals fundamentally different ecosystem philosophies.

## What this means for your projects

### If you're writing Rust

- Expect your MSRV to be 2-3 years behind the latest stable
- Each dependency pulls you toward Rust 1.60-1.63 as a minimum
- Going older requires either no dependencies or significant dependency curation
- MSRV will require regular maintenance as dependencies update

### If you're writing Python

- Most dependencies won't restrict your Python version support
- You can reasonably support Python 3.8+ without much effort
- Watch out for packages with native extensions (numpy, pillow)

### If you're writing Java

- Dependencies are essentially "free" from a compatibility perspective
- You can support Java 8 while using cutting-edge libraries
- Backward compatibility is a solved problem in the JVM ecosystem

### If you're writing Node.js

- Expect to support only recent Node versions (18+)
- Dependencies will push you toward newer Node versions quickly
- Plan for frequent toolchain upgrades
- Carefully evaluate dependency MSRV if supporting older Node is important

## Why these differences exist

**Java's excellence** comes from:
- Strict bytecode compatibility guarantees
- Multi-release JAR support (ship multiple bytecode versions)
- Strong cultural commitment to backward compatibility
- Long LTS support windows (8+ years)

**Python's stability** comes from:
- Slower language evolution (compared to Rust)
- `python_requires` metadata enforcement
- Cultural emphasis on compatibility
- Mature ecosystem with stable interfaces

**Rust's restrictions** come from:
- Rapid language evolution (new editions, features)
- Libraries adopting new features quickly
- No enforcement of MSRV in manifests (until recently)
- Cultural acceptance of moving fast

**Node's churn** comes from:
- Rapid release cycle (major version every 6 months)
- Shorter LTS windows (3 years)
- ESM/CommonJS transition
- "Move fast" culture

## Conclusion

If you write Rust and wonder why you can't support older toolchains,
it's not just you.
It's the entire ecosystem.
Dependencies compress your compatibility window from 7+ years to 2-3 years.

But this isn't universal.
Java proves that dependency compatibility doesn't have to be a constraint.
Python shows that even interpreted languages can maintain broad support.
Node demonstrates that rapid evolution trades compatibility for features.

The tradeoffs are real.
Rust's innovation requires breaking changes.
Java's stability sometimes feels stagnant.
Python's maturity limits experimentation.
Node's speed leaves older versions behind.

Choose your ecosystem knowing what you're trading.

---

## Appendix: Detailed results

### Rust detailed results

Tested 30 foundational crates. Control baseline: Rust 1.16.0 → 1.90.0 (74 versions).

Minimal restriction (15-20% loss):
- bitflags 1.3.2: Rust 1.31.1+
- serde 1.x: Rust 1.31.1+
- mime 0.3: Rust 1.31.1+
- cfg-if 1.0.3: Rust 1.32.0+

Moderate restriction (35-47% loss):
- regex 1.x: Rust 1.51.0+
- semver 1.x: Rust 1.51.0+

High restriction (44-62% loss):
- byteorder 1.5.0: Rust 1.60.0+
- futures 0.3.31: Rust 1.61.0+
- log 0.4.28: Rust 1.61.0+
- syn 2.x: Rust 1.61.0+
- thiserror 1.x: Rust 1.61.0+
- chrono 0.4: Rust 1.62.1+
- itertools 0.13: Rust 1.63.0+
- num_cpus 1.17.0: Rust 1.63.0+
- rand 0.8: Rust 1.63.0+

Severe restriction (66-86% loss):
- tempfile 3.x: Rust 1.65.0+
- env_logger 0.11: Rust 1.71.1+
- rayon 1.x: Rust 1.80.1+

Extreme restriction (89% loss):
- backtrace 0.3: Rust 1.82.0+

### Python detailed results

Tested 19 common packages. Control baseline: Python 3.8 → 3.13 (6 versions).

No restriction (16 packages):
- certifi, charset-normalizer, click, idna, jinja2, markupsafe, packaging,
  platformdirs, pluggy, pytest, pytz, requests, setuptools, six, urllib3

Minor restriction:
- numpy 2.x: Python 3.9+ (lost 1 version)

Failed (installation issues, not Python version):
- pillow, pyyaml, python-dateutil

### Java detailed results

Tested 26 popular libraries. Result: **ALL work on Java 8 → 23**.

Includes Apache Commons, SLF4J, Logback, Gson, Jackson, JUnit 5, Mockito,
Guava, OkHttp, Joda-Time, RxJava, H2, PostgreSQL driver, HikariCP, and more.

### Node.js detailed results

Tested 21 essential packages. Control baseline: Node 14 → 24.

Works on Node 14+ (7 packages):
- lodash, date-fns, axios, async, fs-extra, zod

Requires Node 16+:
- pg

Requires Node 18+ (6 packages):
- express, koa, jest, mocha, winston, pino

Requires Node 20+ (5 packages):
- uuid, node-fetch, commander, yargs, glob, joi

Failed on all versions:
- vitest, chalk

---

**Methodology notes:**
- Rust: Binary search across 90 stable releases using `cargo check`
- Python: Binary search using `uv` package manager with import validation
- Java: Binary search using Maven with compile validation
- Node: Binary search using nvm with runtime import validation

Full experimental code and raw data available in the [GitHub repository](https://github.com/brson/dep-tool-comp).
