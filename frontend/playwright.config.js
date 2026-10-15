import {defineConfig} from '@playwright/test';
import {existsSync} from 'node:fs';
const localPython = '../.runtime/python/python.exe';
export default defineConfig({
  testDir: './tests', testMatch: '**/*.spec.js', workers: 1,
  use: {baseURL: 'http://127.0.0.1:8765', channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome', headless: true, screenshot: 'only-on-failure'},
  webServer: {
    command: `"${process.env.AUDIT_PYTHON || (existsSync(localPython) ? localPython : 'python')}" tests/server.py`,
    url: 'http://127.0.0.1:8765/api/session/', timeout: 60000, reuseExistingServer: false,
  },
});
