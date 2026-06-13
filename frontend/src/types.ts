export type Verdict = 'SUPPORTED' | 'CONTRADICTED' | 'INSUFFICIENT';
export type MessageMode = 'qa' | 'theory';

export interface SourceItem {
  source: string;
  heading: string;
  score: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources: SourceItem[];
  mode: MessageMode;
  verdict: Verdict | null;
  isStreaming: boolean;
  isError: boolean;
}

export interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  error: string | null;
  threadId: string;
}
