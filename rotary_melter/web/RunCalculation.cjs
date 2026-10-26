/* Headless entry to the unchanged V11 browser calculation engine. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {performance} = require('node:perf_hooks');
const context = vm.createContext({console, performance});
const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, 'manifest.json'), 'utf8'));
for (const name of manifest.ENGINE) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, name), 'utf8'), context, {filename: name});
}
try {
  const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
  const configuration = context.RotaryModel.migrateInputs(payload.configuration);
  const result = context.RotaryModel.simulate(configuration, {noHistory: !!payload.noHistory});
  process.stdout.write(JSON.stringify(result));
} catch (error) {
  process.stderr.write(String(error.stack || error));
  process.exitCode = 1;
}
