/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useReducer, type ReactNode } from 'react';
import type { ChatState, MessageMode, SourceItem, Verdict } from '../types';

type ChatAction =
  | { type: 'ADD_USER_MESSAGE'; payload: { id: string; content: string } }
  | { type: 'ADD_ASSISTANT_PLACEHOLDER'; payload: { id: string } }
  | { type: 'APPEND_TOKEN'; payload: { id: string; token: string } }
  | { type: 'FINISH_STREAM'; payload: { id: string; sources: SourceItem[]; mode: MessageMode; verdict: Verdict | null } }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'DISMISS_ERROR' }
  | { type: 'NEW_THREAD'; payload: { threadId: string } };

interface ChatContextValue {
  state: ChatState;
  dispatch: React.Dispatch<ChatAction>;
}

function makeInitialState(): ChatState {
  const threadId = sessionStorage.getItem('thread_id') ?? crypto.randomUUID();
  sessionStorage.setItem('thread_id', threadId);

  return {
    messages: [],
    isStreaming: false,
    error: null,
    threadId,
  };
}

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_USER_MESSAGE': {
      const mode = action.payload.content.trim().toLowerCase().startsWith('theory:') ? 'theory' : 'qa';

      return {
        ...state,
        error: null,
        messages: [
          ...state.messages,
          {
            id: action.payload.id,
            role: 'user',
            content: action.payload.content,
            sources: [],
            mode,
            verdict: null,
            isStreaming: false,
            isError: false,
          },
        ],
      };
    }
    case 'ADD_ASSISTANT_PLACEHOLDER':
      return {
        ...state,
        isStreaming: true,
        error: null,
        messages: [
          ...state.messages,
          {
            id: action.payload.id,
            role: 'assistant',
            content: '',
            sources: [],
            mode: 'qa',
            verdict: null,
            isStreaming: true,
            isError: false,
          },
        ],
      };
    case 'APPEND_TOKEN':
      return {
        ...state,
        messages: state.messages.map((message) =>
          message.id === action.payload.id
            ? { ...message, content: message.content + action.payload.token }
            : message,
        ),
      };
    case 'FINISH_STREAM':
      return {
        ...state,
        isStreaming: false,
        messages: state.messages.map((message) =>
          message.id === action.payload.id
            ? {
                ...message,
                sources: action.payload.sources,
                mode: action.payload.mode,
                verdict: action.payload.verdict,
                isStreaming: false,
              }
            : message,
        ),
      };
    case 'SET_ERROR':
      return {
        ...state,
        isStreaming: false,
        error: action.payload,
        messages: state.messages.map((message) =>
          message.isStreaming ? { ...message, isStreaming: false, isError: true } : message,
        ),
      };
    case 'DISMISS_ERROR':
      return { ...state, error: null };
    case 'NEW_THREAD':
      sessionStorage.setItem('thread_id', action.payload.threadId);
      return {
        messages: [],
        isStreaming: false,
        error: null,
        threadId: action.payload.threadId,
      };
    default:
      return state;
  }
}

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, undefined, makeInitialState);

  return (
    <ChatContext.Provider value={{ state, dispatch }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const value = useContext(ChatContext);

  if (!value) {
    throw new Error('useChat must be used within ChatProvider');
  }

  return value;
}
