import { TraceSealApi } from "./types";

declare global {
  interface Window {
    traceSeal: TraceSealApi;
  }
}

export {};
