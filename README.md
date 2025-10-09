# How dependencies affect your Toolchain version horizon

I recently observed in Rust that having just one dependency
made it much harder to make my crate compatible with older toolchains.

I want to do an experiment to validate this and then blog about it.


## Methodology

- Take a list of foundational Rust crates.
- Make a project that depends on the latest stable version,
  without point release, i.e. "1.0", "0.1", not "1.0.1" or "0.1.1".
- Find the oldest rust toolchain we can compile with,
  while still being able to compile with the latest rust toolchain.
  They can use different lockfiles, but must use the same manifest.


## The crate list

anyhow
backtrace
bitflags
byteorder
cfg-if
chrono
crossbeam
env_logger
extension-trait
futures
hex
itertools
libc
log
mime
num_cpus
rand
rayon
regex
serde
semver
socket2
syn
thiserror
toml
unicode-segmentation
url
walkdir


## Other languages


### Go - long toolchain horizon not practical

-Go 1.18 (March 2022):                                                                                           
  - Generics - Major language change that many modern packages use                                                
  - Many packages published after this require generics features                                                  
                                                                                                                  
- Go 1.16 (Feb 2021):                                                                                             
  - Module mode became default - Before this, GOPATH was still common                                             
  - go install behavior changed significantly                                                                     
                                                                                                                  
- Go 1.13 (Sept 2019):                                                                                            
  - Go modules became production-ready                                                                            
  - Earlier versions have buggy/incomplete module support
