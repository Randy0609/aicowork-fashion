import type {
  Artifact,
  Category,
  ProductInput,
  RunWorkflowResponse,
  WorkbenchStatus,
  WorkflowManifest,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let message = `请求失败（HTTP ${response.status}）`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') message = body.detail;
    } catch {
      // Keep the HTTP fallback message.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function loadStatus(): Promise<WorkbenchStatus> {
  return request('/status');
}

export async function loadCategories(): Promise<Category[]> {
  const response = await request<{ items: Category[] }>('/categories');
  return response.items;
}

export async function loadWorkflows(): Promise<WorkflowManifest[]> {
  const response = await request<{ items: WorkflowManifest[] }>('/workflows');
  return response.items;
}

export async function loadArtifacts(): Promise<Artifact[]> {
  const response = await request<{ items: Artifact[] }>('/artifacts');
  return response.items;
}

export function runProductContent(
  inputs: ProductInput,
  provider: 'demo' | 'configured',
): Promise<RunWorkflowResponse> {
  return request('/workflows/product-content/run', {
    method: 'POST',
    body: JSON.stringify({ inputs, provider }),
  });
}
