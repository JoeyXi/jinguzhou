#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "../../..");
const localSrc = path.join(repoRoot, "src");
const hasLocalCheckout = fs.existsSync(path.join(localSrc, "jinguzhou", "__init__.py"));

function buildEnv() {
  const env = { ...process.env };
  if (!hasLocalCheckout) {
    return env;
  }

  const existing = env.PYTHONPATH;
  env.PYTHONPATH = existing ? `${localSrc}${path.delimiter}${existing}` : localSrc;
  return env;
}

const candidates = process.platform === "win32"
  ? ["python", "py"]
  : ["python3", "python"];

let result = null;
for (const candidate of candidates) {
  result = spawnSync(candidate, ["-m", "jinguzhou.cli", ...process.argv.slice(2)], {
    stdio: "inherit",
    env: buildEnv(),
  });
  if (result.error && result.error.code === "ENOENT") {
    continue;
  }
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  process.exit(result.status === null ? 1 : result.status);
}

console.error("Python was not found. Install Python and the Jinguzhou package first:");
console.error('  python3 -m pip install "jinguzhou"');
process.exit(1);
