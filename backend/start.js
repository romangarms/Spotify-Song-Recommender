#!/usr/bin/env node
/**
 * Cross-platform Python venv launcher
 * Works on Windows, macOS, and Linux
 */

const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

// Determine the correct Python path based on platform
const isWindows = os.platform() === 'win32';
const pythonPath = isWindows
  ? path.join(__dirname, 'venv', 'Scripts', 'python.exe')
  : path.join(__dirname, 'venv', 'bin', 'python');

// Spawn Python process
const python = spawn(pythonPath, ['app.py'], {
  cwd: __dirname,
  stdio: 'inherit',
  shell: false
});

python.on('error', (error) => {
  console.error('Failed to start Python:', error.message);
  console.error('\nMake sure you have created the virtual environment:');
  console.error('  cd backend && python -m venv venv');
  console.error('  cd backend && venv\\Scripts\\pip install -r requirements.txt  (Windows)');
  console.error('  cd backend && venv/bin/pip install -r requirements.txt      (Mac/Linux)');
  process.exit(1);
});

python.on('exit', (code) => {
  process.exit(code);
});
