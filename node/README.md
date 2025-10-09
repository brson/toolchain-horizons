# Node.js Dependency Toolchain Compatibility Experiment

This experiment mirrors the Rust, Python, Go, and Java versions but for Node.js packages.

## Methodology

- Take a list of foundational Node.js packages (npm packages)
- For each package, test compatibility across multiple Node.js versions
- Use a **two-phase approach**:
  1. **Engine Strict Phase**: Use `npm install --engine-strict` to check declared compatibility
  2. **Runtime Phase**: Actually import and use the package to verify real compatibility
- Find the oldest Node version that works with each package

## Tool: nvm

This experiment uses [nvm](https://github.com/nvm-sh/nvm) for Node.js version management:
- `nvm install <version>` - Install Node versions
- `nvm use <version>` - Switch to a specific version
- npm is used for package installation

This is analogous to SDKMAN for Java and rustup for Rust.

## Two-Phase Testing Approach

### Phase 1: Engine Strict (`--engine-strict`)

Many npm packages declare their Node.js compatibility in the `engines` field of package.json:
```json
{
  "engines": {
    "node": ">= 18"
  }
}
```

By default, npm **ignores** this field and installs anyway (just shows warnings). With `--engine-strict`, npm will **fail** if the current Node version doesn't match.

**What this tests:**
- What package maintainers **declare** as compatible
- Metadata-based compatibility (like Maven's approach)

**Limitations:**
- Not all packages declare `engines` (~50% don't)
- Some packages are overly conservative in declarations
- Doesn't test if code actually runs

### Phase 2: Runtime Testing

For packages that pass Phase 1 (or don't declare engines), we create actual test code:
```javascript
const packageName = require('package-name');
// Actually call functions and use APIs
```

Then run with `node test.js` to verify it works.

**What this tests:**
- Actual runtime compatibility
- If the JavaScript/APIs work on this Node version
- Real-world usability

**Why this matters:**
Learning from the Java experiment, we discovered that testing only dependency resolution (without actually using the code) is a weak test. This phase ensures we're testing real compatibility.

## The Package List

Foundational npm packages, selected to represent different categories:

### Web Frameworks
- express (Declared: `>= 18`)
- fastify (No engines declaration)
- koa (Declared: `>= 18`)

### Utilities
- lodash (No engines declaration)
- date-fns (No engines declaration)
- uuid (No engines declaration)

### HTTP Clients
- axios (No engines declaration)
- node-fetch (Declared: `^12.20.0 || ^14.13.1 || >=16.0.0`)

### Testing
- jest (Declared: `^18.14.0 || ^20.0.0 || ^22.0.0 || >=24.0.0`)
- mocha (Declared: `^18.18.0 || ^20.9.0 || >=21.1.0`)
- vitest (Declared: `^18.0.0 || ^20.0.0 || >=22.0.0`)
- chai (TBD)

### Async/Promises
- async (No engines declaration)
- p-queue (TBD)
- p-limit (TBD)

### CLI Tools
- commander (Declared: `>=20`)
- yargs (Declared: `^20.19.0 || ^22.12.0 || >=23`)
- chalk (Declared: `^12.17.0 || ^14.13 || >=16.0.0`)
- inquirer (TBD)

### File/Path
- fs-extra (Declared: `>=14.14`)
- glob (Declared: `20 || >=22`)
- rimraf (TBD)

### Validation
- joi (Declared: `>= 20`)
- zod (No engines declaration)
- ajv (TBD)

### Database
- pg (Declared: `>= 16.0.0`)
- mysql2 (TBD)
- mongodb (TBD)

### Logging
- winston (Declared: `>= 12.0.0`)
- pino (No engines declaration)

## Running

```bash
cd node
node experiment.js
```

Results will be written to `results.json`.

## Node Version Strategy

Testing Node.js LTS versions plus current, spanning ~8 years:
- Node 14.21.3 (LTS Fermium, EOL April 2023)
- Node 16.20.2 (LTS Gallium, EOL Sept 2023)
- Node 18.20.8 (LTS Hydrogen, Active until Oct 2025)
- Node 20.19.5 (LTS Iron, Current Active LTS)
- Node 22.20.0 (LTS Jod, newest LTS as of Oct 2024)
- Node 24.x (Current, not LTS yet)

## Expected Results

Unlike Java (where all packages worked with Java 8-23), we expect to see:
- **Significant restrictions** - Many packages require Node 18+
- **Testing frameworks very restrictive** - jest, mocha, vitest all require 18+
- **Mixed results** - Some packages with no engines declaration may work on older Node
- **Faster dropping of old versions** - Node ecosystem moves faster than Java

This will provide interesting contrast to Java's exceptional backward compatibility.
