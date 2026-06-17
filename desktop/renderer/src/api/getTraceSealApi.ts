import type { TraceSealApi } from './contracts';
import { mockTraceSealApi } from './mockTraceSealApi';

export function getTraceSealApi(): TraceSealApi {
  if (window.traceSeal) {
    return window.traceSeal;
  }
  return mockTraceSealApi;
}