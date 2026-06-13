import { motion } from 'framer-motion';
import type { Message } from '../../types';
import { Bubble } from '../Bubble/Bubble';
import { SourceChips } from '../SourceChips/SourceChips';
import styles from './MessageRow.module.css';

function UserAvatar() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 1C5.24 1 3 3.24 3 6c0 1.7.82 3.2 2.08 4.13V12h5.84v-1.87C12.18 9.2 13 7.7 13 6c0-2.76-2.24-5-5-5Z" fill="#C9A84C" />
      <rect x="5" y="12" width="2" height="2" rx="0.3" fill="#C9A84C" opacity="0.6" />
      <rect x="9" y="12" width="2" height="2" rx="0.3" fill="#C9A84C" opacity="0.6" />
      <circle cx="6" cy="5.5" r="1.3" fill="#0A1520" />
      <circle cx="10" cy="5.5" r="1.3" fill="#0A1520" />
    </svg>
  );
}

function AssistantAvatar() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="1" y="3" width="5.5" height="10" rx="0.6" fill="none" stroke="#4DA3D8" strokeWidth="1" />
      <rect x="9.5" y="3" width="5.5" height="10" rx="0.6" fill="none" stroke="#4DA3D8" strokeWidth="1" />
      <line x1="6.5" y1="3" x2="6.5" y2="13" stroke="#4DA3D8" strokeWidth="0.7" />
      <line x1="9.5" y1="3" x2="9.5" y2="13" stroke="#4DA3D8" strokeWidth="0.7" />
      <line x1="2.5" y1="6" x2="5" y2="6" stroke="#4DA3D8" strokeWidth="0.6" opacity="0.5" />
      <line x1="2.5" y1="8" x2="5" y2="8" stroke="#4DA3D8" strokeWidth="0.6" opacity="0.5" />
      <line x1="2.5" y1="10" x2="5" y2="10" stroke="#4DA3D8" strokeWidth="0.6" opacity="0.5" />
      <line x1="11" y1="6" x2="13.5" y2="6" stroke="#4DA3D8" strokeWidth="0.6" opacity="0.5" />
      <line x1="11" y1="8" x2="13.5" y2="8" stroke="#4DA3D8" strokeWidth="0.6" opacity="0.5" />
      <line x1="11" y1="10" x2="13.5" y2="10" stroke="#4DA3D8" strokeWidth="0.6" opacity="0.5" />
    </svg>
  );
}

function Avatar({ role }: { role: Message['role'] }) {
  return (
    <div className={`${styles.avatar} ${role === 'user' ? styles.userAvatar : styles.asstAvatar}`}>
      {role === 'user' ? <UserAvatar /> : <AssistantAvatar />}
    </div>
  );
}

export function MessageRow({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={isUser ? styles.userRow : styles.asstRow}
    >
      <Avatar role={msg.role} />
      <div className={styles.bubbleWrap}>
        <Bubble message={msg} />
        {!msg.isStreaming && msg.sources.length > 0 && <SourceChips sources={msg.sources} />}
      </div>
    </motion.div>
  );
}
