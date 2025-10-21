# Measuring the effect of Rust dependencies on MSRV

During a recent project to get the [Rust client] for the [TigerBeetle database]
ready for production
I went through a typical process of establishing the minimum supported version
of the Rust toolchain (MSRV) the crate could support.

It usually goes something like this:

1. Do a binary search through rust versions to find the newest
   one that doesn't build and test successfully,
   using rustup and commands like `cargo +1.60 test` to specify the toolchain.
2. Fix the build, which usually involves downgrading or removing dependencies.
3. Test on the stable compiler again.
4. Repeat.

Besids simple API incompatibility I sometimes run into situations:

- The lockfile format changed and the old revision must be used to generate lockfiles,
  because it can't read newer revisions.
  Quite a compatibility headache to deal with if you need to commit lockfiles.
- `cargo` can't resolve the dependency dependency graph on its own, but it is technically
  possible to resolve the graph; so we can claim compatibility, but it's not ideal.
- Older toolchains can technically work, but their resolved dependencies
  can't pass `cargo audit`; so we can claim compatibility, but it's not ideal.

I'm sure there are others I've forgotten.

This time, what I found was in hindsight not surprising,
but at the time was surprisingly revelatory,
even though I have gone through the process numerous times:

> Taking a dependency on a single Rust crate is likely
> to commit you to supporting only 2 years of Rust toolchains.

You will likely be chasing toolchain upgrades to stay in that 2 year window.

Whether this is good or bad I'm not sure:
I generally think healthy projects should keep their toolchains upgraded;
but _only_ being _able_ to support two years of toolchains smells stinky to me!

I eventually settled on the minimum supported version
being [Rust 1.63], from (date todo), N months prior to date of publication.
This appears to be something like the median consensus of the crate ecosystem,
and pushing past that requires increasing effort.

This experience just gnawed at me for weeks.
So I did an experiment to satisfy my curiousity.








---
