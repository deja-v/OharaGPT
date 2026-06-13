import { streamChat } from '../api';
import { useChat } from '../context/ChatContext';

function friendlyError(err: unknown) {
  if (err instanceof DOMException && err.name === 'AbortError') {
    return 'Connection lost.';
  }

  if (err instanceof TypeError) {
    return 'Could not connect. Is the backend running?';
  }

  if (err instanceof Error) {
    return err.message || 'Something went wrong. Please try again.';
  }

  return 'Something went wrong. Please try again.';
}

export function useSubmit() {
  const { state, dispatch } = useChat();

  async function submit(question: string) {
    if (state.isStreaming || !question.trim()) return;

    const userId = crypto.randomUUID();
    const asstId = crypto.randomUUID();
    const prompt = question.trim();

    dispatch({ type: 'ADD_USER_MESSAGE', payload: { id: userId, content: prompt } });
    dispatch({ type: 'ADD_ASSISTANT_PLACEHOLDER', payload: { id: asstId } });

    try {
      await streamChat(prompt, state.threadId, {
        onToken: (token) => dispatch({ type: 'APPEND_TOKEN', payload: { id: asstId, token } }),
        onDone: (data) => dispatch({ type: 'FINISH_STREAM', payload: { id: asstId, ...data } }),
        onError: (err) => dispatch({ type: 'SET_ERROR', payload: friendlyError(err) }),
      });
    } catch (err) {
      dispatch({ type: 'SET_ERROR', payload: friendlyError(err) });
    }
  }

  return { submit, isStreaming: state.isStreaming };
}
