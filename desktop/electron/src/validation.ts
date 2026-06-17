import path from "node:path";
import { TraceSealRuntimeError } from "./types";

const RUN_ID_RE = /^run_[A-Za-z0-9_.-]+$/;

export function validateRunId(runId: unknown): string {
  if (typeof runId !== "string") {
    throw new TraceSealRuntimeError("INVALID_RUN_ID", "runId must be a string");
  }
  const value = runId.trim();
  if (!value) {
    throw new TraceSealRuntimeError("INVALID_RUN_ID", "runId is empty");
  }
  if (path.isAbsolute(value) || value.includes("..") || value.includes("/") || value.includes("\\")) {
    throw new TraceSealRuntimeError("INVALID_RUN_ID", "runId must not be a path");
  }
  if (!RUN_ID_RE.test(value)) {
    throw new TraceSealRuntimeError("INVALID_RUN_ID", "runId must match run_<safe characters>");
  }
  return value;
}
