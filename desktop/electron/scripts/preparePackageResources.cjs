const fs = require("node:fs");
const path = require("node:path");

const repoRoot = path.resolve(__dirname, "../../..");
const rendererSource = path.join(repoRoot, "desktop", "renderer", "dist");
const packagingDist = path.join(repoRoot, "packaging", "dist");
const rendererTarget = path.join(packagingDist, "renderer");
const coreDir = path.join(packagingDist, "traceseal-core");
const coreExe = path.join(coreDir, process.platform === "win32" ? "traceseal-core.exe" : "traceseal-core");

function fail(message) {
  console.error(`[traceseal-package] ${message}`);
  process.exit(1);
}

function requireFile(filePath, message) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    fail(`${message}: ${filePath}`);
  }
}

requireFile(path.join(rendererSource, "index.html"), "Renderer dist is missing. Run npm run build in desktop/renderer first");
requireFile(coreExe, "Bundled Python Core is missing. Run scripts/build-windows.ps1 or build PyInstaller first");

fs.rmSync(rendererTarget, { recursive: true, force: true });
fs.mkdirSync(packagingDist, { recursive: true });
fs.cpSync(rendererSource, rendererTarget, { recursive: true });

console.log(`[traceseal-package] renderer: ${rendererTarget}`);
console.log(`[traceseal-package] core: ${coreDir}`);
