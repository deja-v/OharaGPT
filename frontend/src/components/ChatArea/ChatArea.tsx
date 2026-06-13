import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { useChat } from '../../context/ChatContext';
import { EmptyState } from '../EmptyState/EmptyState';
import { MessageRow } from '../MessageRow/MessageRow';
import styles from './ChatArea.module.css';

export function ChatArea() {
  const { state } = useChat();
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages.length]);

  return (
    <main className={styles.chatArea}>
      <AnimatePresence mode="wait">
        {state.messages.length === 0 ? (
          <EmptyState key="empty" />
        ) : (
          <motion.div
            key="messages"
            className={styles.messages}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            {state.messages.map((message) => (
              <MessageRow key={message.id} msg={message} />
            ))}
            <div ref={bottomRef} />
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
