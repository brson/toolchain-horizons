# Toolchain Horizons: Exploring Dependency-Toolchain Compatibility

Last year I created the Rust client for [TigerBeetle](https://github.com/tigerbeetle/tigerbeetle),
the double-entry financial accounting database.
While landing the code and establishing the minimum
supported Rust version I encountered multiple
surprises about how common Rust crates manage their toolchain dependencies.
So I did an experiment to learn more about toolchain
support in the Rust dependency landscape.
In the course of this experiment I learned
that common Rust crates support
only 1-2 years of prior Rust toolchains;
I removed every dependency from the TigerBeetle Rust client,
and replaced modern Rust language features
until it was compatible with Rust 1.39, from 2019.
For the sake of curiosity.




## Background: TigerBeetle clients

TigerBeetle has a client-server architecture,
and provides client libraries for most popular languages:
Python, Java, Go, Node, .NET, and now Rust.
Each of these is a bindings/FFI project that binds
to the single `tb_client` library,
written in Zig,
exposing a C ABI,
wrapped in the idioms of the embedding language.


![TigerBeetle client architecture: language clients (Python, Java, Go, Node, .NET, Rust) all connect to the central tb_client library written in Zig](tb-client-arch.svg)


The Rust client is less than two thousand lines of production Rust code,
some of it generated, some of it written by hand.
It provides a simple asynchronous,
futures-oriented API for use with `async` / `await`;
and it is runtime-agnostic,
requiring no dependencies on specific Rust async runtimes.

In use it looks like this:

```rust
use tigerbeetle as tb;

// Connect to TigerBeetle
let client = tb::Client::new(0, "127.0.0.1:3000")?;

// Create two accounts on the same ledger
let accounts = [
    tb::Account {
        id: tb::id(),
        ledger: 1,
        code: 1,
        ..Default::default()
    },
    tb::Account {
        id: tb::id(),
        ledger: 1,
        code: 1,
        ..Default::default()
    },
];
client.create_accounts(&accounts).await?;

// Transfer 100 units from the first account to the second
let transfers = [tb::Transfer {
    id: tb::id(),
    debit_account_id: accounts[0].id,
    credit_account_id: accounts[1].id,
    amount: 100,
    ledger: 1,
    code: 1,
    ..Default::default()
}];
client.create_transfers(&transfers).await?;
```




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
I save that work for just before publication,
a process like:

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
the client's initial MSRV was Rust 1.81,
published September 5, 2024.

About 9 months of supported toolchains.
Not satisfactory, but not surprising.




## TigerStyle and dependencies

TigerBeetle has a set of strict and opinionated
coding guidelines,
[TigerStyle](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md).
They are focused on three pillars:
safety, performance, and developer UX.

TigerStyle emphasizes fully understanding and owning your code
and radically reducing dependencies.

It has this to say about dependencies:

> TigerBeetle has a “zero dependencies” policy,
  apart from the Zig toolchain.
  Dependencies, in general, inevitably lead to supply chain attacks,
  safety and performance risk, and slow install times.
  For foundational infrastructure in particular,
  the cost of any dependency is further amplified throughout the rest of the stack.




## TigerBeetle Rust client dependencies





## The Rust `futures` dependency problem




## The experiment and its results



## Why support older Rust version?



## And does it matter that we can't?

Probably not.


So what about TigerBeetle's zero-dependency policy?
