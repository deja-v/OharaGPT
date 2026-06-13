import type { MessageMode, SourceItem, Verdict } from './types';

const BASE = import.meta.env.VITE_API_URL;

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onDone: (data: { sources: SourceItem[]; mode: MessageMode; verdict: Verdict | null }) => void;
  onError: (err: Error) => void;
}

async function mapHttpError(resp: Response): Promise<Error> {
  if (resp.status === 429) {
    return new Error('Rate limit reached. Wait a moment and try again.');
  }

  const body = await resp.text();

  if (resp.status === 500 && body.toLowerCase().includes('index')) {
    return new Error('Wiki index not built. Run `python -m rag.index` from backend/.');
  }

  return new Error(`HTTP ${resp.status}`);
}

export async function streamChat(
  question: string,
  threadId: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({ question, thread_id: threadId }),
    signal,
  });

  if (!resp.ok) {
    callbacks.onError(await mapHttpError(resp));
    return;
  }

  if (!resp.body) {
    callbacks.onError(new Error('Could not connect. Is the backend running?'));
    return;
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let eventType = 'message';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim();
        continue;
      }

      if (!line.startsWith('data: ')) continue;

      try {
        const data = JSON.parse(line.slice(6).trim());

        if (eventType === 'token') callbacks.onToken(data.content);
        else if (eventType === 'done') callbacks.onDone(data);
        else if (eventType === 'error') callbacks.onError(new Error(data.error));
      } catch {
        // Skip malformed SSE payloads without interrupting a valid stream.
      }

      eventType = 'message';
    }
  }
}
