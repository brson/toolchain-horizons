# Toolchain Horizons: Exploring Dependency-Toolchain Compatibility

Last year I created the Rust client for [TigerBeetle],
the double-entry financial accounting database.

While landing the code and establishing the minimum
supported Rust version I had multiple
surprises about how few Rust versions common crates supported:
e.g. the pervasive and official `futures` crate
currently only supports back to Rust TODO, date TODO.

So I did an experiment to learn more about toolchain
support in the Rust dependency landscape.



## Background: TigerBeetle clients


## Background: MSRV discovery



Initial MSRV: Rust 1.81, September 5, 2024.




## TigerStyle and dependencies




## TigerBeetle Rust client dependencies




## The Rust `futures` dependency problem




## The experiment and its results



## Conclusion




## Appendix: other languages' toolchain horizons
