import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { RiskBadge } from '../components/RiskBadge';

describe('RiskBadge', () => {
  it('renders low risk', () => {
    render(<RiskBadge level="low" />);
    expect(screen.getByText('低')).toBeInTheDocument();
  });

  it('renders critical risk', () => {
    render(<RiskBadge level="critical" />);
    expect(screen.getByText('严重')).toBeInTheDocument();
  });

  it('renders null for undefined level', () => {
    const { container } = render(<RiskBadge level={undefined} />);
    expect(container.firstChild).toBeNull();
  });
});

describe('RunStatusBadge', () => {
  it('renders completed status', async () => {
    const { RunStatusBadge } = await import('../components/RunStatusBadge');
    render(<RunStatusBadge status="completed" />);
    expect(screen.getByText('已完成')).toBeInTheDocument();
  });

  it('renders blocked status', async () => {
    const { RunStatusBadge } = await import('../components/RunStatusBadge');
    render(<RunStatusBadge status="blocked" />);
    expect(screen.getByText('已阻断')).toBeInTheDocument();
  });

  it('renders failed status', async () => {
    const { RunStatusBadge } = await import('../components/RunStatusBadge');
    render(<RunStatusBadge status="failed" />);
    expect(screen.getByText('失败')).toBeInTheDocument();
  });
});