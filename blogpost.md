# Measuring the effect of Rust dependencies on your toolchain horizen

During a recent project to get the [Rust client] for the [TigerBeetle database]
ready for production,
I went through a typical process of establishing the minimum supported version
of the Rust toolchain the crate could support.

It usually goes something like this:

1. todo
2. todo

What I found was in hindsight not surprising,
but at the time was surprisingly revelatory,
even though I have gone through the process numerous times:

> If you use any Rust dependencies, even as dev-dependencies,
  you are committing to supporting only 2 years of Rust toolchains.

You will likely be chasing toolchain upgrades to stay in that 2 year window.

Whether this is good or bad I'm not sure:
I generally think healthy projects should keep their toolchains upgraded;
but _only_ being _able_ to support two years of toolchains feels kinda offensive to me.

I eventually settled on the minimum supported version
being [Rust 1.63], from (date todo), N months prior to date of publication.
This appears to be something like the median consensus of the crate ecosystem,
and pushing past that requires increasing effort.

todo
