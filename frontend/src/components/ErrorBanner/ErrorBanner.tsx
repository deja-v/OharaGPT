import { AnimatePresence, motion } from 'framer-motion';
import { useChat } from '../../context/ChatContext';
import styles from './ErrorBanner.module.css';

function messageFor(error: string) {
  if (error.startsWith('HTTP 429')) return 'Rate limit reached. Wait a moment and try again.';
  if (error.startsWith('HTTP 500') && error.toLowerCase().includes('index')) {
    return 'Wiki index not built. Run `python -m rag.index` from backend/.';
  }
  if (error.startsWith('HTTP ')) return 'Something went wrong. Please try again.';
  return error;
}

export function ErrorBannerPortal() {
  const { state, dispatch } = useChat();

  return (
    <AnimatePresence>
      {state.error && (
        <motion.div
          initial={{ y: -48, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -48, opacity: 0 }}
          className={styles.banner}
        >
          <span>{messageFor(state.error)}</span>
          <button type="button" onClick={() => dispatch({ type: 'DISMISS_ERROR' })} aria-label="Dismiss error">
            ✕
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
