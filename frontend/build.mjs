import * as esbuild from 'esbuild';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const directory = path.dirname(fileURLToPath(import.meta.url));
const options = {
  entryPoints: [path.join(directory, 'src/main.jsx')], bundle: true, outdir: path.join(directory, '../static/react'),
  entryNames: 'app', minify: true, format: 'esm', target: ['es2020'],
  jsx: 'automatic', define: {'process.env.NODE_ENV': '"production"'},
  sourcemap: false, logLevel: 'info',
};
if (process.argv.includes('--watch')) {
  const context = await esbuild.context(options);
  await context.watch();
  console.log('React: surveillance active. Rechargez le navigateur après une modification.');
} else {
  await esbuild.build(options);
}
