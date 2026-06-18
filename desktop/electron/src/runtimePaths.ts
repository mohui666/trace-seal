import fs from "node:fs";
import path from "node:path";

export interface RuntimePathOptions {
  isPackaged?: boolean;
  resourcesPath?: string;
  dirname?: string;
  cwd?: string;
  env?: NodeJS.ProcessEnv;
  platform?: NodeJS.Platform;
}

export function preloadPath(dirname: string): string {
  return path.join(dirname, "preload.js");
}

export function bundledCoreExecutablePath(options: RuntimePathOptions = {}): string {
  const resourcesPath = options.resourcesPath || process.resourcesPath || process.cwd();
  const platform = options.platform || process.platform;
  const exeName = platform === "win32" ? "traceseal-core.exe" : "traceseal-core";
  return path.join(resourcesPath, "traceseal-core", exeName);
}

export function rendererIndexPath(options: RuntimePathOptions = {}): string | null {
  const env = options.env || process.env;
  const cwd = options.cwd || process.cwd();
  const dirname = options.dirname || __dirname;

  if (env.TRACESEAL_RENDERER_DIST) {
    const explicit = path.resolve(env.TRACESEAL_RENDERER_DIST, "index.html");
    if (fs.existsSync(explicit)) return explicit;
  }

  const candidates: string[] = [];
  if (options.isPackaged && options.resourcesPath) {
    candidates.push(path.join(options.resourcesPath, "renderer", "index.html"));
  }

  candidates.push(
    // Compiled Electron runtime: desktop/electron/dist/src/main.js -> desktop/renderer/dist/index.html
    path.resolve(dirname, "../../../renderer/dist/index.html"),
    // Fallback when running from source tooling.
    path.resolve(dirname, "../../renderer/dist/index.html"),
    path.resolve(cwd, "../renderer/dist/index.html"),
    path.resolve(cwd, "desktop/renderer/dist/index.html"),
  );

  return candidates.find((candidate) => fs.existsSync(candidate)) || null;
}
