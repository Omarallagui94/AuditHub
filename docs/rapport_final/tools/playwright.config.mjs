import playwright from '../../../frontend/node_modules/@playwright/test/index.js';
const {defineConfig} = playwright;

export default defineConfig({
  testDir: '.',
  testMatch: 'screenshots.spec.mjs',
  workers: 1,
  timeout: 90000,
  use: {
    baseURL: 'http://127.0.0.1:8766',
    channel: process.env.PLAYWRIGHT_CHANNEL || 'chrome',
    headless: true,
    viewport: {width: 1600, height: 1000},
    deviceScaleFactor: 1,
  },
  webServer: {
    command: '".runtime/python/python.exe" docs/rapport_final/tools/screenshot_server.py',
    url: 'http://127.0.0.1:8766/api/session/',
    cwd: '../../..',
    timeout: 60000,
    reuseExistingServer: false,
  },
});
