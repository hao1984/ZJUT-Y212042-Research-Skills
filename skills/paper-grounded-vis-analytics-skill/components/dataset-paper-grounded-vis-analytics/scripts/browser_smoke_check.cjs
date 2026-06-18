#!/usr/bin/env node
/* Browser smoke check for dataset-paper-grounded VIS apps. */

const fs = require("fs");
const path = require("path");

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (item.startsWith("--")) {
      const next = argv[i + 1];
      args[item.slice(2)] = next && !next.startsWith("--") ? next : true;
      if (next && !next.startsWith("--")) i += 1;
    }
  }
  return args;
}

function fileUrl(filePath) {
  return `file:///${path.resolve(filePath).replace(/\\/g, "/").replace(/^([A-Za-z]):/, "$1:")}`;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log("usage: node browser_smoke_check.cjs --file <run_dir>/app/index.html --run-dir <run_dir> [--executable-path <chrome.exe>]");
    return;
  }
  const targetFile = args.file ? path.resolve(args.file) : null;
  const url = args.url || (targetFile ? fileUrl(targetFile) : null);
  if (!url) throw new Error("Pass --file app/index.html or --url http://...");
  const runDir = path.resolve(args["run-dir"] || (targetFile ? path.dirname(path.dirname(targetFile)) : process.cwd()));
  const outPath = path.resolve(args.out || path.join(runDir, "artifacts", "browser_smoke.json"));

  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch (error) {
    throw new Error(`Playwright is not available: ${error.message}`);
  }

  const launchOptions = { headless: true };
  if (args["executable-path"]) launchOptions.executablePath = path.resolve(args["executable-path"]);
  const browser = await chromium.launch(launchOptions);
  const viewports = [
    { width: 1920, height: 1080, label: "1920x1080" },
    { width: 1440, height: 810, label: "1440x810" }
  ];
  const results = [];
  for (const viewport of viewports) {
    const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
    const consoleErrors = [];
    page.on("console", msg => { if (msg.type() === "error") consoleErrors.push(msg.text()); });
    page.on("pageerror", error => consoleErrors.push(error.message));
    await page.goto(url, { waitUntil: "load", timeout: 30000 });
    await page.waitForFunction(() => window.__DATASET_VIS_DEMO_READY__ === true, null, { timeout: 10000 });
    const metrics = await page.evaluate(() => {
      const required = [".primaryPanel", ".referencePanel", ".contextPanel", ".evidencePanel", ".provenance"];
      const visibleRequired = required.every(selector => {
        const el = document.querySelector(selector);
        if (!el) return false;
        const rect = el.getBoundingClientRect();
        return rect.width > 40 && rect.height > 20;
      });
      return {
        viewportWidth: window.innerWidth,
        viewportHeight: window.innerHeight,
        bodyScrollHeight: document.body.scrollHeight,
        htmlScrollHeight: document.documentElement.scrollHeight,
        bodyScrollWidth: document.body.scrollWidth,
        htmlScrollWidth: document.documentElement.scrollWidth,
        svgCount: document.querySelectorAll("svg").length,
        dataMarks: document.querySelectorAll("[data-mark='true']").length,
        groundingItems: document.querySelectorAll(".groundItem, .groundCard, [data-grounding='true']").length,
        chips: document.querySelectorAll(".chip").length,
        visibleRequired
      };
    });
    const verticalOverflow = Math.max(metrics.bodyScrollHeight, metrics.htmlScrollHeight) - viewport.height;
    const horizontalOverflow = Math.max(metrics.bodyScrollWidth, metrics.htmlScrollWidth) - viewport.width;
    const screenshotPath = path.join(runDir, "artifacts", `smoke_${viewport.label}.png`);
    await page.screenshot({ path: screenshotPath });
    results.push({
      viewport: viewport.label,
      consoleErrors,
      metrics,
      verticalOverflow,
      horizontalOverflow,
      viewportFit: verticalOverflow <= 2 && horizontalOverflow <= 2,
      nonblank: metrics.svgCount >= 1 && metrics.dataMarks >= 5,
      coordinatedWorkspaceVisible: metrics.visibleRequired && metrics.groundingItems >= 1,
      screenshot: screenshotPath
    });
    await page.close();
  }
  await browser.close();
  const report = {
    checked_at: new Date().toISOString(),
    url,
    pass: results.every(item => item.consoleErrors.length === 0 && item.viewportFit && item.nonblank && item.coordinatedWorkspaceVisible),
    results
  };
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(report, null, 2));
  if (!report.pass) process.exitCode = 1;
}

main().catch(error => {
  console.error(error.message);
  process.exit(1);
});
