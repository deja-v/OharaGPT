import { motion } from 'framer-motion';
import { useRef, useState, type FormEvent, type KeyboardEvent } from 'react';
import { useSubmit } from '../../hooks/useSubmit';
import styles from './MessageInput.module.css';

function DenDenMushiIcon() {
  return (
    <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
      <motion.g
        whileHover={{ x: [-2, 2, -1, 0], rotate: [-5, 4, -2, 0] }}
        transition={{ duration: 0.4, ease: 'easeInOut' }}
        style={{ originX: '50%', originY: '50%' }}
      >
        <circle cx="16" cy="14" r="7.5" fill="none" stroke="#C9A84C" strokeWidth="1.3" />
        <path d="M16 14 m0-4.5 a4.5 4.5 0 0 1 4.5 4.5 a4.5 4.5 0 0 1-4.5 4.5" stroke="#C9A84C" strokeWidth="0.7" fill="none" opacity="0.4" />
        <circle cx="16" cy="14" r="1.5" fill="#C9A84C" opacity="0.5" />
        <path d="M8.5 17 Q6.5 19 8.5 20.5 Q11.5 22 16 21" stroke="#C9A84C" strokeWidth="1.3" fill="none" strokeLinecap="round" />
        <ellipse cx="9" cy="15.5" rx="3" ry="2.2" fill="none" stroke="#C9A84C" strokeWidth="1.1" />
        <line x1="7.5" y1="13.5" x2="5.5" y2="10" stroke="#C9A84C" strokeWidth="0.9" strokeLinecap="round" />
        <line x1="10" y1="13" x2="9" y2="9.5" stroke="#C9A84C" strokeWidth="0.9" strokeLinecap="round" />
        <circle cx="5.5" cy="10" r="1.3" fill="#C9A84C" />
        <circle cx="9" cy="9.5" r="1.3" fill="#C9A84C" />
      </motion.g>
    </svg>
  );
}

export function MessageInput() {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const { submit, isStreaming } = useSubmit();

  function resizeTextarea() {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 130)}px`;
  }

  async function handleSubmit(event?: FormEvent) {
    event?.preventDefault();
    const prompt = value.trim();
    if (!prompt || isStreaming) return;

    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = '';
    await submit(prompt);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  }

  return (
    <form className={`${styles.inputZone} ${isStreaming ? styles.disabled : ''}`} onSubmit={handleSubmit}>
      <div className={styles.terminalLabel}>✦ TRANSPONDER SNAIL TERMINAL ✦</div>
      <div className={styles.terminal}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          rows={1}
          value={value}
          placeholder="Ask about a theory or a fact — the archive is open..."
          disabled={isStreaming}
          onChange={(event) => setValue(event.target.value)}
          onInput={resizeTextarea}
          onKeyDown={handleKeyDown}
        />
        <button className={styles.sendBtn} type="submit" aria-label="Send message" disabled={isStreaming || !value.trim()}>
          <DenDenMushiIcon />
        </button>
      </div>
    </form>
  );
}
