# How dependencies destroy your Rust MSRV

I recently discovered something that kinda blew my mind: adding just one dependency to a Rust project can make it way harder to support older toolchains. Like, dramatically harder.

I should have known this already - I've been through the MSRV dance enough times. But seeing the actual numbers was still pretty shocking.

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

Anyway, full results and the experiment code are [on GitHub](https://github.com/brson/dep-tool-comp).

---

## Methodology notes

- Version specs used major versions for >= 1.0 crates, major.minor for < 1.0
- All tests allowed different Cargo.lock files per toolchain
- One crate (derive_more) failed to compile and was excluded
- Tested on Linux, October 2024
- Toolchain versions are the latest point releases only (so 1.63.0, not 1.63.1)

The experiment uses binary search to find the oldest compatible version, which means I'm testing log₂(90) ≈ 7 versions per crate instead of all 90. Makes it actually feasible to run.
