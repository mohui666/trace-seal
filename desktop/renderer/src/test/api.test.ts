import { describe, it, expect } from 'vitest';
import { getTraceSealApi } from '../api/getTraceSealApi';
import { mockTraceSealApi } from '../api/mockTraceSealApi';

describe('getTraceSealApi', () => {
  it('returns mock API when window.traceSeal is not set', () => {
    delete (window as any).traceSeal;
    const api = getTraceSealApi();
    expect(api).toBe(mockTraceSealApi);
  });

  it('returns Electron API when window.traceSeal is set', () => {
    const mockApi = { ...mockTraceSealApi };
    (window as any).traceSeal = mockApi;
    const api = getTraceSealApi();
    expect(api).toBe(mockApi);
    delete (window as any).traceSeal;
  });
});