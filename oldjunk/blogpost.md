# Measuring the effect of Rust dependencies on MSRV

During a recent modestly-sized project to get the [Rust client] for the [TigerBeetle database]
ready for production I went again through the process of establishing the minimum supported version
of the Rust toolchain (MSRV) the crate could support.

What I found was a bit shocking:

> Taking a dependency on a single Rust crate is likely
> to commit you to supporting only 2 years of Rust toolchains.


## The TigerBeetle Rust client and MSRV

Establishing the MSRV usually goes something like this:

1. Do a binary search through recent rust versions to find the newest
   one that doesn't build and test successfully,
   using rustup and commands like `cargo +1.63 test` to specify the toolchain.
2. Fix the build, which usually involves downgrading or removing dependencies.
3. Test on the stable compiler again.
4. Update your CI toolchain range.
4. Repeat.

Besids simple API incompatibility I sometimes run into situations:

- The lockfile format changed and the old revision must be used to generate lockfiles,
  because it can't read newer revisions.
  Quite a compatibility headache to deal with if you need to commit lockfiles.
- `cargo` can't resolve the dependency dependency graph on its own, but it is technically
  possible to resolve the graph; so we can claim compatibility, but it's not ideal.
- Older toolchains can technically work, but their resolved dependencies
  can't pass `cargo audit`; so we can claim compatibility, but it's not ideal.

For TigerBeetle we initially settled on the minimum supported version
being [Rust 1.63], which was released 2.5 years prior to publication.
This appears to be something like the median consensus of the crate ecosystem,
and pushing past that requires increasing effort.

That revision had 3 dependencies: [`anyhow`], [`futures`], and [`walkdir`].
Fundamental Rust crates.

**As I was working on this blog post, the `syn` crate published
a point release (2.0.107) that bumped their MSVR from 1.63 to 1.68,
breaking the build of our crate that had only 3 Rust dependencies.**

Eventually we just decided to go for it and remove all dependencies
(even `futures`, which I'll explain how we replaced in [an appendix]).

Now the TigerBeetl Rust client is compatible with Rust toolchains
back to version XXX, from XXX &mdash; even more compatible than the
ecosystem-fundamental `futures` crate!

This experience just gnawed at me for weeks:
Rust's stability guarantees are well-known;
so why does the ecosystem impose such a narrow compatibility window?

So I did an experiment to satisfy my curiousity.


## The experiment

To measure the MSRV cost of dependencies, I selected 29 foundational Rust crates
that commonly appear in production projects: `serde`, `rand`, `futures`, `log`,
and similar widely-used libraries.

For each crate, I created a minimal project with that single dependency and used
binary search to determine the oldest Rust toolchain that could compile it. This
provides an isolated measurement of each dependency's minimum toolchain
requirement.

**Experimental parameters:**

- Baseline is Rust 1.31, which introduced Rust 2018 edition in December 2018.
  Our test crates are declared with no edition (meaning 2015 edition).
- Latest stable version specifications (e.g. `"1"` for serde, `"0.3"` for futures).
  Cargo is free to resolve using the minor version number.
- Binary search space: all stable Rust releases from 1.31.0 to 1.90.0 (TODO versions).
- Each toolchain generates its own Cargo.lock, but all use the same Cargo.toml

A control project with zero dependencies compiles successfully with 1.31.

We are just testing cargo's ability to automatically resolve the dependency graph &mdash;
there are no manual interventions, which might be successful in a real project.



## The results

The control case compiles with Rust 1.16.0 (March 2017),
released prior to the 2018 edition.
I didn't check what the blocker is on going back further.
So language stability when it is just resolving dependencies is good.

Here's what happens when you add a single dependency.

![Rust Crate Toolchain Compatibility Timeline](rust/compatibility-timeline.png)

fixme these numbers are using the wrong baseline

Some very common crates heavily restrict your Rust toolchain:

- `bitflags`, `serde`, `mime`: Require Rust 1.31.1 (Dec 2018)
  - **20% version loss**, 1.8 years newer than baseline
- `futures`, `log`, `crossbeam`, `syn`, `thiserror`: Require Rust 1.61.0 (May 2022)
  - **61% version loss**, 5.2 years newer
- `rand`, `itertools`, `libc`, `num_cpus`: Require Rust 1.63.0 (Aug 2022)
  - **64% version loss**, 5.4 years newer
- `rayon`: Requires Rust 1.80.1 (Aug 2024)
  - **86% version loss** - only 4 months old when I ran this!
- `backtrace`: Requires Rust 1.82.0 (Oct 2024)
  - **89% version loss** - basically requires the latest toolchain
  