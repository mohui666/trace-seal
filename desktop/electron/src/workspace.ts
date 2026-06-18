import fs from "node:fs";
import path from "node:path";
import { TraceSealRuntimeError, WorkspaceInfo } from "./types";

interface WorkspaceSettings {
  workspaceRoot?: unknown;
}

export interface WorkspaceRunner {
  setRepositoryRoot(repositoryRoot: string): void;
}

export type DirectorySelector = () => Promise<string | null>;

export const EMPTY_WORKSPACE: WorkspaceInfo = Object.freeze({
  path: null,
  valid: false,
  hasRuns: false,
  hasPolicy: false,
});

function isDirectory(directoryPath: string): boolean {
  try {
    return fs.statSync(directoryPath).isDirectory();
  } catch {
    return false;
  }
}

export function inspectWorkspace(workspacePath: string | null | undefined): WorkspaceInfo {
  if (!workspacePath || typeof workspacePath !== "string") {
    return { ...EMPTY_WORKSPACE };
  }
  const normalized = path.resolve(workspacePath);
  let valid = false;
  try {
    valid = fs.statSync(normalized).isDirectory();
    if (valid) fs.accessSync(normalized, fs.constants.R_OK);
  } catch {
    valid = false;
  }
  return {
    path: normalized,
    valid,
    hasRuns: valid && isDirectory(path.join(normalized, "runs")),
    hasPolicy: valid && isDirectory(path.join(normalized, "policy")),
  };
}

export class WorkspaceStore {
  constructor(private readonly settingsPath: string) {}

  getSettingsPath(): string {
    return this.settingsPath;
  }

  getWorkspace(): WorkspaceInfo {
    if (!fs.existsSync(this.settingsPath)) return { ...EMPTY_WORKSPACE };
    try {
      const parsed = JSON.parse(fs.readFileSync(this.settingsPath, "utf8")) as WorkspaceSettings;
      if (typeof parsed.workspaceRoot !== "string" || !parsed.workspaceRoot.trim()) {
        return { ...EMPTY_WORKSPACE };
      }
      return inspectWorkspace(parsed.workspaceRoot);
    } catch {
      return { ...EMPTY_WORKSPACE };
    }
  }

  saveWorkspace(workspacePath: string): WorkspaceInfo {
    const info = inspectWorkspace(workspacePath);
    if (!info.valid || !info.path) {
      throw new TraceSealRuntimeError("INVALID_WORKSPACE", "Selected workspace is not an accessible directory", {
        workspacePath,
      });
    }
    try {
      fs.mkdirSync(path.dirname(this.settingsPath), { recursive: true });
      const temporaryPath = `${this.settingsPath}.tmp`;
      fs.writeFileSync(temporaryPath, JSON.stringify({ workspaceRoot: info.path }, null, 2), "utf8");
      fs.renameSync(temporaryPath, this.settingsPath);
      return info;
    } catch (error) {
      throw new TraceSealRuntimeError("INTERNAL_ERROR", "Failed to save workspace settings", error);
    }
  }

  clearWorkspace(): void {
    try {
      fs.rmSync(this.settingsPath, { force: true });
    } catch (error) {
      throw new TraceSealRuntimeError("INTERNAL_ERROR", "Failed to clear workspace settings", error);
    }
  }
}

export class WorkspaceController {
  constructor(
    private readonly store: WorkspaceStore,
    private readonly runner: WorkspaceRunner,
    private readonly selectDirectory: DirectorySelector,
    private readonly fallbackRoot: string,
  ) {
    const current = this.store.getWorkspace();
    if (current.valid && current.path) this.runner.setRepositoryRoot(current.path);
  }

  async selectWorkspace(): Promise<WorkspaceInfo> {
    const selectedPath = await this.selectDirectory();
    if (!selectedPath) return this.getWorkspace();
    const info = this.store.saveWorkspace(selectedPath);
    this.runner.setRepositoryRoot(info.path!);
    return info;
  }

  getWorkspace(): WorkspaceInfo {
    const info = this.store.getWorkspace();
    if (info.valid && info.path) this.runner.setRepositoryRoot(info.path);
    return info;
  }

  clearWorkspace(): void {
    this.store.clearWorkspace();
    this.runner.setRepositoryRoot(this.fallbackRoot);
  }
}
