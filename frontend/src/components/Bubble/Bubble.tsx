import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../../types';
import { TheoryTag } from '../TheoryTag/TheoryTag';
import { VerdictStamp } from '../VerdictStamp/VerdictStamp';
import styles from './Bubble.module.css';

export function Bubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const showTheory = message.mode === 'theory';
  const bubbleClass = [
    styles.bubble,
    isUser ? styles.userBubble : styles.asstBubble,
    showTheory ? styles.theoryBubble : '',
    message.isError ? styles.errorBubble : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={bubbleClass}>
      {showTheory && <TheoryTag />}
      {!isUser && message.verdict !== null && <VerdictStamp verdict={message.verdict} />}
      {isUser ? (
        <p>{message.content}</p>
      ) : (
        <ReactMarkdown>{message.content}</ReactMarkdown>
      )}
      {message.isStreaming && (
        <motion.span
          className={styles.streamDot}
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        />
      )}
    </div>
  );
}
