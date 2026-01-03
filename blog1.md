# Toolchain Horizons: Exploring Dependency-Toolchain Compatibility

Last year I created the Rust client for [TigerBeetle],
the double-entry financial accounting database.

While landing the code and establishing the minimum
supported Rust version I had multiple
surprises about how few Rust versions were supported by common crates (libraries).

So I did an experiment to learn more about toolchain
support in the Rust dependency landscape.




## Background: TigerBeetle clients

TigerBeetle has a client-server architecture,
and provides client libraries for most popular languages:
Python, Java, Go, Node, .NET, and now Rust.

Each of these is a bindings/FFI project that binds
to the single `tb_client` library, written in Zig,
exposing a C ABI,
wrapped in the idioms of the appropriate language.


<!-- todo tb_client diagram -->



## Background: MSRV discovery

The Rust ecosystem has a concept of
the "Minimum Supported Rust Version" (MSRV) for its crates.
This means exactly what it sounds like.
It is a versioning scheme that relates crates
to the Rust compiler version,
and it is separate from SemVer,
Rust's primary versioning scheme.

Some crates encode this information in
their `Cargo.toml` manifest's optional
[`rust-version`](https://doc.rust-lang.org/cargo/reference/rust-version.html)
field.

It is a best practice for crate maintainers
to know and document their minimum supported Rust version
and test against that version in their CI.

When I do the initial development of a new Rust crate,
I don't worry about the minimum Rust version;
I save that work for just before publication.

The process typically proceeds thusly:

1. Start with the oldest version I know I support.
2. Test against the previous version.
3. Fix the build.
   This usually involves removing or replacing dependencies,
   and replacing newer language features with older ones
   or dependencies that fill that role.
   Open-coded polyfills are often involved.
4. Update CI to verify that as the minimum supported Rust version.
4. Do it again.

When I posted the [initial pull request] for
the Rust TigerBeetle client in June 2025,
I had not done this yet,
and expected our minimum supported Rust version to be a recent one.
Without any effort to support older releases,
the client's
initial MSRV was Rust 1.81, published September 5, 2024.

About 9 months of supported toolchains.
Not satisfactory, but expected.




## TigerStyle and dependencies

TigerBeetle somewhat notoriously has a set of strict and opinionated
coding guidelines, branded [TigerStyle].

The guidelines are focused on three pillars:
safety, performance, and developer UX.




## TigerBeetle Rust client dependencies




## The Rust `futures` dependency problem




## The experiment and its results



## Conclusion




## Appendix: other languages' toolchain horizons
