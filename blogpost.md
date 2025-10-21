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







---
