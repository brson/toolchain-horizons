#!/usr/bin/env node

/**
 * Dependency toolchain compatibility experiment for Node.js.
 *
 * This experiment tests how adding a single dependency affects the range
 * of Node.js versions that can successfully use that dependency.
 *
 * Uses nvm for Node.js version management and npm for package installation.
 * Two-phase testing: --engine-strict for declared compatibility, then runtime tests.
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');
const os = require('os');

// Package list with known engines declarations.
const PACKAGES = [
  // Web frameworks.
  { name: 'express', hasEngines: true },
  { name: 'koa', hasEngines: true },

  // Utilities.
  { name: 'lodash', hasEngines: false },
  { name: 'date-fns', hasEngines: false },
  { name: 'uuid', hasEngines: false },

  // HTTP clients.
  { name: 'axios', hasEngines: false },
  { name: 'node-fetch', hasEngines: true },

  // Testing.
  { name: 'jest', hasEngines: true },
  { name: 'mocha', hasEngines: true },
  { name: 'vitest', hasEngines: true },

  // Async.
  { name: 'async', hasEngines: false },

  // CLI.
  { name: 'commander', hasEngines: true },
  { name: 'yargs', hasEngines: true },
  { name: 'chalk', hasEngines: true },

  // File/Path.
  { name: 'fs-extra', hasEngines: true },
  { name: 'glob', hasEngines: true },

  // Validation.
  { name: 'joi', hasEngines: true },
  { name: 'zod', hasEngines: false },

  // Database.
  { name: 'pg', hasEngines: true },

  // Logging.
  { name: 'winston', hasEngines: true },
  { name: 'pino', hasEngines: false },
];

// Node versions to test (LTS versions + current).
const NODE_VERSIONS = [
  'v14.21.3',  // LTS Fermium (EOL April 2023)
  'v16.20.2',  // LTS Gallium (EOL Sept 2023)
  'v18.20.8',  // LTS Hydrogen (Active until Oct 2025)
  'v20.19.5',  // LTS Iron (Current Active LTS)
  'v22.20.0',  // LTS Jod (Newest LTS)
  'v24.0.2',   // Current
];

const results = [];

console.log('Starting Node.js dependency toolchain compatibility experiment');
console.log(`Testing ${PACKAGES.length} packages across ${NODE_VERSIONS.length} Node versions\n`);

// Test control case first.
console.log('=== Testing control case (no dependencies) ===');
const controlResult = testControlCase();
console.log(`Control: oldest=${controlResult.oldestCompatible}, latest=${controlResult.latestCompatible}\n`);
results.push(controlResult);

// Test each package.
for (const pkg of PACKAGES) {
  console.log(`=== Testing ${pkg.name} ===`);
  const result = testPackage(pkg);
  console.log(`${pkg.name}: oldest=${result.oldestCompatible || 'NONE'}, latest=${result.latestCompatible || 'N/A'}`);
  if (result.engineFailure) {
    console.log(`  Engine restriction: ${result.engineFailure}`);
  }
  console.log();
  results.push(result);
}

// Write results.
fs.writeFileSync('results.json', JSON.stringify(results, null, 2));
console.log('=== Results written to results.json ===');

/**
 * Test the control case (no dependencies).
 */
function testControlCase() {
  const result = {
    packageName: 'CONTROL',
    hasEngines: false,
    oldestCompatible: null,
    latestCompatible: null,
  };

  const oldest = findOldestCompatible(null);
  result.oldestCompatible = oldest;
  result.latestCompatible = NODE_VERSIONS[NODE_VERSIONS.length - 1];

  return result;
}

/**
 * Test a single package.
 */
function testPackage(pkg) {
  const result = {
    packageName: pkg.name,
    hasEngines: pkg.hasEngines,
    oldestCompatible: null,
    latestCompatible: null,
    engineFailure: null,
  };

  // Find oldest compatible version.
  const oldest = findOldestCompatible(pkg);
  if (oldest) {
    result.oldestCompatible = oldest;
    result.latestCompatible = NODE_VERSIONS[NODE_VERSIONS.length - 1];
  }

  return result;
}

/**
 * Find the oldest compatible Node version using binary search.
 */
function findOldestCompatible(pkg) {
  let left = 0;
  let right = NODE_VERSIONS.length;
  let oldest = null;

  while (left < right) {
    const mid = Math.floor(left + (right - left) / 2);
    const version = NODE_VERSIONS[mid];

    console.log(`  Testing Node ${version}`);

    const testResult = testNodeVersion(version, pkg);

    if (testResult.success) {
      oldest = version;
      right = mid;
    } else {
      if (testResult.engineFailure && !results.find(r => r.packageName === pkg?.name)?.engineFailure) {
        // Record first engine failure we encounter.
        const pkgResult = results.find(r => r.packageName === pkg?.name);
        if (pkgResult) {
          pkgResult.engineFailure = testResult.engineFailure;
        }
      }
      left = mid + 1;
    }
  }

  return oldest;
}

/**
 * Test if a package works with a specific Node version.
 * Two-phase approach: engine-strict check, then runtime test.
 */
function testNodeVersion(nodeVersion, pkg) {
  // Ensure Node version is installed.
  if (!ensureNodeInstalled(nodeVersion)) {
    return { success: false, reason: 'Node install failed' };
  }

  // Control case - just test Node itself.
  if (!pkg) {
    return testNodeOnly(nodeVersion);
  }

  // Phase 1: Try npm install with --engine-strict.
  const engineResult = testWithEngineStrict(nodeVersion, pkg);
  if (!engineResult.success) {
    return { success: false, engineFailure: engineResult.reason };
  }

  // Phase 2: Runtime test - actually use the package.
  const runtimeResult = testRuntime(nodeVersion, pkg);
  return runtimeResult;
}

/**
 * Test that Node itself works (control case).
 */
function testNodeOnly(nodeVersion) {
  try {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'node-exp-'));

    try {
      // Create simple test.
      const testCode = 'console.log("ok");';
      fs.writeFileSync(path.join(tmpDir, 'test.js'), testCode);

      // Run with this Node version.
      const result = spawnSync('bash', ['-c', `source ~/.config/nvm/nvm.sh && nvm use ${nodeVersion} && node test.js`], {
        cwd: tmpDir,
        timeout: 30000,
        encoding: 'utf-8',
      });

      return {
        success: result.status === 0 && result.stdout?.includes('ok'),
      };
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  } catch (err) {
    return { success: false, reason: err.message };
  }
}

/**
 * Phase 1: Test with npm install --engine-strict.
 */
function testWithEngineStrict(nodeVersion, pkg) {
  try {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'node-exp-'));

    try {
      // Create package.json.
      fs.writeFileSync(path.join(tmpDir, 'package.json'), JSON.stringify({
        name: 'test',
        version: '1.0.0',
        dependencies: {
          [pkg.name]: 'latest',
        },
      }, null, 2));

      // Create .npmrc with engine-strict=true.
      fs.writeFileSync(path.join(tmpDir, '.npmrc'), 'engine-strict=true\n');

      // Try npm install.
      const result = spawnSync('bash', ['-c',
        `source ~/.config/nvm/nvm.sh && nvm use ${nodeVersion} && npm install 2>&1`
      ], {
        cwd: tmpDir,
        timeout: 120000,
        encoding: 'utf-8',
      });

      if (result.status !== 0) {
        // Check if it's an engine error.
        const output = result.stdout + result.stderr;
        if (output.includes('EBADENGINE') || output.includes('Unsupported engine')) {
          // Extract the engine requirement if possible.
          const match = output.match(/wanted: \{[^}]+node[^}]+\}/);
          return {
            success: false,
            reason: match ? match[0] : 'Engine version mismatch',
          };
        }
        return { success: false, reason: 'Install failed (non-engine)' };
      }

      return { success: true };
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  } catch (err) {
    return { success: false, reason: err.message };
  }
}

/**
 * Phase 2: Runtime test - actually require and use the package.
 */
function testRuntime(nodeVersion, pkg) {
  try {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'node-exp-'));

    try {
      // Create package.json (without engine-strict this time).
      fs.writeFileSync(path.join(tmpDir, 'package.json'), JSON.stringify({
        name: 'test',
        version: '1.0.0',
        dependencies: {
          [pkg.name]: 'latest',
        },
      }, null, 2));

      // Install package.
      const installResult = spawnSync('bash', ['-c',
        `source ~/.config/nvm/nvm.sh && nvm use ${nodeVersion} && npm install --silent 2>&1`
      ], {
        cwd: tmpDir,
        timeout: 120000,
        encoding: 'utf-8',
      });

      if (installResult.status !== 0) {
        return { success: false, reason: 'Runtime install failed' };
      }

      // Create test code that actually uses the package.
      const testCode = generateTestCode(pkg.name);
      fs.writeFileSync(path.join(tmpDir, 'test.js'), testCode);

      // Run the test.
      const testResult = spawnSync('bash', ['-c',
        `source ~/.config/nvm/nvm.sh && nvm use ${nodeVersion} && node test.js`
      ], {
        cwd: tmpDir,
        timeout: 30000,
        encoding: 'utf-8',
      });

      return {
        success: testResult.status === 0 && testResult.stdout?.includes('TEST_OK'),
      };
    } finally {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
  } catch (err) {
    return { success: false, reason: err.message };
  }
}

/**
 * Generate test code that actually uses a package.
 * This avoids the Java experiment's mistake of testing with an empty file.
 */
function generateTestCode(packageName) {
  const tests = {
    'express': `
      const express = require('express');
      const app = express();
      app.get('/', (req, res) => res.send('ok'));
      console.log('TEST_OK');
    `,
    'koa': `
      const Koa = require('koa');
      const app = new Koa();
      console.log('TEST_OK');
    `,
    'lodash': `
      const _ = require('lodash');
      const result = _.chunk(['a', 'b', 'c', 'd'], 2);
      if (result.length === 2) console.log('TEST_OK');
    `,
    'axios': `
      const axios = require('axios');
      console.log(typeof axios.get === 'function' ? 'TEST_OK' : 'FAIL');
    `,
    'uuid': `
      const { v4 } = require('uuid');
      const id = v4();
      console.log(id.length === 36 ? 'TEST_OK' : 'FAIL');
    `,
    'chalk': `
      const chalk = require('chalk');
      console.log(chalk.blue ? 'TEST_OK' : 'FAIL');
    `,
    'commander': `
      const { Command } = require('commander');
      const program = new Command();
      console.log('TEST_OK');
    `,
    'winston': `
      const winston = require('winston');
      const logger = winston.createLogger({transports: [new winston.transports.Console({silent: true})]});
      console.log('TEST_OK');
    `,
    'glob': `
      const { glob } = require('glob');
      console.log(typeof glob === 'function' ? 'TEST_OK' : 'FAIL');
    `,
    'fs-extra': `
      const fs = require('fs-extra');
      console.log(typeof fs.ensureDir === 'function' ? 'TEST_OK' : 'FAIL');
    `,
  };

  // Return specific test if available, otherwise generic require test.
  return tests[packageName] || `
    const pkg = require('${packageName}');
    console.log(pkg ? 'TEST_OK' : 'FAIL');
  `;
}

/**
 * Ensure a Node version is installed via nvm.
 */
function ensureNodeInstalled(version) {
  try {
    // Check if already installed.
    const listResult = spawnSync('bash', ['-c', `source ~/.config/nvm/nvm.sh && nvm list`], {
      encoding: 'utf-8',
      timeout: 10000,
    });

    if (listResult.stdout?.includes(version)) {
      return true;
    }

    // Install the version.
    console.log(`    Installing Node ${version}...`);
    const installResult = spawnSync('bash', ['-c',
      `source ~/.config/nvm/nvm.sh && nvm install ${version}`
    ], {
      timeout: 300000,
      encoding: 'utf-8',
    });

    return installResult.status === 0;
  } catch (err) {
    console.log(`    Failed to install ${version}: ${err.message}`);
    return false;
  }
}
