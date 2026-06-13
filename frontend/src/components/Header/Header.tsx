import { motion } from 'framer-motion';
import { useChat } from '../../context/ChatContext';
import styles from './Header.module.css';

function formatThreadId(threadId: string) {
  const compact = threadId.replace(/-/g, '').toUpperCase();
  return `LOG-${compact.slice(0, 4)} · ${compact.slice(4, 8)} · ${compact.slice(8, 12)}`;
}

function SkullLogo() {
  return (
    <svg className={styles.logoSkull} width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
      <path d="M11 2C7.13 2 4 5.13 4 9c0 2.4 1.16 4.52 2.95 5.85V17h8.1v-2.15C16.84 13.52 18 11.4 18 9c0-3.87-3.13-7-7-7Z" fill="#C9A84C" opacity="0.9" />
      <rect x="7" y="17" width="3" height="3" rx="0.5" fill="#C9A84C" opacity="0.6" />
      <rect x="12" y="17" width="3" height="3" rx="0.5" fill="#C9A84C" opacity="0.6" />
      <circle cx="8.5" cy="8.5" r="2" fill="#0A1520" />
      <circle cx="13.5" cy="8.5" r="2" fill="#0A1520" />
      <path d="M10 12h2" stroke="#0A1520" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

export function Header() {
  const { state, dispatch } = useChat();

  function startNewThread() {
    dispatch({ type: 'NEW_THREAD', payload: { threadId: crypto.randomUUID() } });
  }

  return (
    <header className={styles.header}>
      <div className={styles.logo} aria-label="OharaGPT">
        <SkullLogo />
        <span>OHARAGPT</span>
      </div>
      <div className={styles.headerRight}>
        <span className={styles.threadId}>{formatThreadId(state.threadId)}</span>
        <motion.button
          type="button"
          className={styles.newLogBtn}
          onClick={startNewThread}
          whileHover={{ boxShadow: '0 0 12px rgba(201,168,76,0.15)' }}
        >
          + NEW LOG
        </motion.button>
      </div>
    </header>
  );
}
