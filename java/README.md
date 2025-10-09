# Java Dependency Toolchain Compatibility Experiment

This experiment mirrors the Rust version but for Java packages.

## Methodology

- Take a list of foundational Java packages (Maven coordinates).
- Make a project that depends on a recent major version using version ranges
  like `[1.0,2.0)` to allow flexibility in resolution.
- Find the oldest Java toolchain we can use while still being able to use
  the latest Java toolchain. They can use different resolved versions
  (like different lockfiles), but must use the same dependency specification.

## Tool: SDKMAN

This experiment uses [SDKMAN](https://sdkman.io/) for Java version management:
- `sdk install java <version>` - Install Java versions
- `sdk use java <version>` - Switch to a specific version
- Maven is used for dependency resolution and compilation

This is analogous to the Rust experiment using `rustup` and `cargo`.

## The package list

Core Apache Commons libraries:
- commons-lang:commons-lang (Apache Commons Lang 2.x)
- org.apache.commons:commons-lang3 (Apache Commons Lang 3.x)
- commons-io:commons-io (Apache Commons IO)
- org.apache.commons:commons-collections4 (Apache Commons Collections)
- org.apache.commons:commons-text (Apache Commons Text)

Logging:
- org.slf4j:slf4j-api (SLF4J API)
- ch.qos.logback:logback-classic (Logback)
- org.apache.logging.log4j:log4j-core (Log4j 2)

JSON Processing:
- com.google.code.gson:gson (Gson)
- com.fasterxml.jackson.core:jackson-databind (Jackson)
- org.json:json (JSON-java)

Testing:
- junit:junit (JUnit 4)
- org.junit.jupiter:junit-jupiter (JUnit 5)
- org.mockito:mockito-core (Mockito)

Utilities:
- com.google.guava:guava (Google Guava)
- joda-time:joda-time (Joda-Time)
- org.apache.httpcomponents:httpclient (Apache HttpClient)

## Running

```bash
cd java
java Experiment.java
```

Results will be written to `results.json`.

## Compilation Checking

Java's `javac` compiler performs full type checking and compilation,
making it comparable to Rust's `cargo check`. This validates:
- Type correctness
- API compatibility
- Compile-time checks

## Java Version Strategy

Testing Java versions from 8 onwards, as Java 8 is the oldest LTS version
still widely used in production. We'll test:
- Java 8 (LTS, 2014)
- Java 11 (LTS, 2018)
- Java 17 (LTS, 2021)
- Java 21 (LTS, 2023)
- Java 23 (latest as of 2024)
