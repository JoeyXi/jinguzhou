#!/usr/bin/env node

const { spawnSync } = require("node:child_process");

const candidates = process.platform === "win32"
  ? ["python", "py"]
  : ["python3", "python"];

let result = null;
for (const candidate of candidates) {
  result = spawnSync(candidate, ["-m", "jinguzhou.cli", ...process.argv.slice(2)], {
    stdio: "inherit"
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
