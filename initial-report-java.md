# Java Toolchain Compatibility Experiment Results

The experiment completed successfully in **6 minutes 39 seconds**, testing 12 popular Java packages across 5 Java versions (8, 11, 17, 21, 23).

## Key Finding: Java Has Excellent Backward Compatibility

**All 12 packages tested are compatible with Java 8 through Java 23** - a 10+ year span!

## Tested Packages & Resolved Versions

| Package | Version Range | Resolved | Compatible Range |
|---------|---------------|----------|------------------|
| **Control** (no deps) | - | - | Java 8 → 23 |
| commons-lang3 | [3.12,4.0) | 3.19.0 | Java 8 → 23 |
| commons-io | [2.11,3.0) | 2.20.0 | Java 8 → 23 |
| commons-collections4 | [4.4,5.0) | 4.5.0 | Java 8 → 23 |
| commons-text | [1.10,2.0) | 1.14.0 | Java 8 → 23 |
| slf4j-api | [2.0,3.0) | 2.1.0-alpha1 | Java 8 → 23 |
| logback-classic | [1.4,2.0) | 1.5.19 | Java 8 → 23 |
| gson | [2.10,3.0) | 2.13.2 | Java 8 → 23 |
| jackson-databind | [2.15,3.0) | 2.20.0 | Java 8 → 23 |
| junit-jupiter | [5.10,6.0) | 6.0.0-RC3 | Java 8 → 23 |
| mockito-core | [5.0,6.0) | 5.20.0 | Java 8 → 23 |
| guava | [32.0,33.0) | 32.1.3-jre | Java 8 → 23 |
| httpclient | [4.5,5.0) | 4.5.14 | Java 8 → 23 |

## Cross-Language Comparison

### Rust (most restrictive)
- **Control**: Rust 1.16.0 → 1.90.0 (74 versions, ~7 years)
- **With deps**: Some restrict to Rust 1.60.0+, losing 44 versions

### Python (moderately restrictive)
- **Control**: Python 3.8 → 3.13 (6 versions, ~6 years)
- **With deps**:
  - **numpy** restricts to 3.9+ (loses 1 version)
  - **pillow, python-dateutil, pyyaml** don't work with any tested version

### Java (least restrictive)
- **Control**: Java 8 → 23 (5 LTS + latest, 10+ years)
- **With deps**: **ALL packages work with Java 8 → 23** ✅

## Why Java Differs

1. **Strong backward compatibility commitment** - The JVM maintains strict bytecode compatibility
2. **Multi-release JAR support** - Libraries can ship code for multiple Java versions in one artifact
3. **Mature ecosystem** - Most libraries maintain broad Java version support
4. **LTS-focused** - Community focuses on long-term support versions (8, 11, 17, 21)

## Experiment Design

- **Tool chain**: SDKMAN for Java version management
- **Build tool**: Maven for dependency resolution
- **Validation**: `mvn compile` performs full type checking (comparable to `cargo check`)
- **Binary search**: Efficiently finds oldest compatible version
- **Versions tested**: 8.0.432-tem, 11.0.25-tem, 17.0.13-tem, 21.0.5-tem, 23.0.1-tem

## Conclusion

Unlike Rust and Python where dependencies can significantly restrict your toolchain horizon, **Java dependencies have virtually no impact on toolchain compatibility**. This reflects Java's strong emphasis on backward compatibility and the ecosystem's commitment to supporting long-term support versions.
