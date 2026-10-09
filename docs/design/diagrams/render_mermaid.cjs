// Render the pinned Mermaid library using Playwright/Edge instead of Puppeteer.
// A temporary loopback server serves only the local Mermaid dist directory.
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(path.join(__dirname, '../../../node_modules/playwright'));

async function main() {
  const [manifestPath, vendorPath, configPath, edgePath] = process.argv.slice(2);
  const jobs = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const vendor = path.resolve(vendorPath);
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const server = http.createServer((req, res) => {
    const pathname = new URL(req.url, 'http://127.0.0.1').pathname;
    if (pathname === '/') {
      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      res.end('<!doctype html><html><meta charset="utf-8"><body><script type="module">import mermaid from "/vendor/mermaid.esm.min.mjs";window.mermaid=mermaid;</script></body></html>');
      return;
    }
    if (!pathname.startsWith('/vendor/')) { res.writeHead(404); res.end(); return; }
    const filename = path.resolve(vendor, decodeURIComponent(pathname.slice('/vendor/'.length)));
    if (!filename.startsWith(vendor + path.sep)) { res.writeHead(403); res.end(); return; }
    if (!fs.existsSync(filename) || !fs.statSync(filename).isFile()) { res.writeHead(404); res.end(); return; }
    res.setHeader('Content-Type', filename.endsWith('.css') ? 'text/css' : filename.endsWith('.json') ? 'application/json' : 'text/javascript');
    fs.createReadStream(filename).pipe(res);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ executablePath: edgePath, headless: true });
    const page = await browser.newPage({ viewport: { width: 1920, height: 1500 } });
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    await page.waitForFunction(() => Boolean(window.mermaid));
    await page.evaluate(c => window.mermaid.initialize({ ...c, startOnLoad: false }), config);
    for (let i = 0; i < jobs.length; i++) {
      const job = jobs[i];
      const svg = await page.evaluate(async ({ source, id }) => {
        await window.mermaid.parse(source);
        return (await window.mermaid.render(id, source)).svg;
      }, { source: job.source, id: 'diagram_' + i });
      fs.writeFileSync(job.output, svg, 'utf8');
      process.stdout.write('Rendered ' + job.name + '\n');
    }
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
}
main().catch(error => { process.stderr.write(String(error.stack || error) + '\n'); process.exitCode = 1; });
