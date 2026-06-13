import { motion } from 'framer-motion';
import { useSubmit } from '../../hooks/useSubmit';
import styles from './EmptyState.module.css';

const questions = [
  {
    tag: 'INQUIRY ⚓',
    question: 'What is the true identity of Im-sama?',
  },
  {
    tag: 'THEORY ⚡',
    question: 'Theory: The Void Century was erased to conceal the Ancient Kingdom',
  },
  {
    tag: 'INQUIRY ⚓',
    question: 'Where are the three Ancient Weapons currently located?',
  },
];

function CompassRose() {
  return (
    <svg width="200" height="200" viewBox="0 0 200 200" fill="none" aria-hidden="true">
      <circle cx="100" cy="100" r="90" stroke="#C9A84C" strokeWidth="0.8" opacity="0.7" />
      <circle cx="100" cy="100" r="78" stroke="#C9A84C" strokeWidth="0.4" opacity="0.4" />
      <circle cx="100" cy="100" r="52" stroke="#C9A84C" strokeWidth="0.3" strokeDasharray="3 6" opacity="0.3" />
      <polygon points="100,8 107,92 100,100 93,92" fill="#C9A84C" opacity="0.9" />
      <polygon points="100,192 107,108 100,100 93,108" fill="#C9A84C" opacity="0.5" />
      <polygon points="192,100 108,93 100,100 108,107" fill="#C9A84C" opacity="0.9" />
      <polygon points="8,100 92,93 100,100 92,107" fill="#C9A84C" opacity="0.5" />
      <polygon points="100,8 107,92 100,100 93,92" fill="#C9A84C" opacity="0.35" transform="rotate(45 100 100)" />
      <polygon points="100,192 107,108 100,100 93,108" fill="#C9A84C" opacity="0.2" transform="rotate(45 100 100)" />
      <polygon points="192,100 108,93 100,100 108,107" fill="#C9A84C" opacity="0.35" transform="rotate(45 100 100)" />
      <polygon points="8,100 92,93 100,100 92,107" fill="#C9A84C" opacity="0.2" transform="rotate(45 100 100)" />
      <g stroke="#C9A84C" strokeWidth="0.5" opacity="0.3">
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(30 100 100)" />
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(60 100 100)" />
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(120 100 100)" />
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(150 100 100)" />
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(210 100 100)" />
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(240 100 100)" />
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(300 100 100)" />
        <line x1="100" y1="10" x2="100" y2="20" transform="rotate(330 100 100)" />
      </g>
      <circle cx="100" cy="100" r="8" fill="none" stroke="#C9A84C" strokeWidth="1.2" opacity="0.8" />
      <circle cx="100" cy="100" r="3" fill="#C9A84C" opacity="0.8" />
      <text x="100" y="5" textAnchor="middle" fontFamily="'Bebas Neue',sans-serif" fontSize="9" fill="#C9A84C" opacity="0.9">N</text>
      <text x="100" y="200" textAnchor="middle" fontFamily="'Bebas Neue',sans-serif" fontSize="9" fill="#C9A84C" opacity="0.5">S</text>
      <text x="3" y="104" textAnchor="middle" fontFamily="'Bebas Neue',sans-serif" fontSize="9" fill="#C9A84C" opacity="0.5">W</text>
      <text x="198" y="104" textAnchor="middle" fontFamily="'Bebas Neue',sans-serif" fontSize="9" fill="#C9A84C" opacity="0.9">E</text>
    </svg>
  );
}

export function EmptyState() {
  const { submit, isStreaming } = useSubmit();

  return (
    <motion.section
      className={styles.emptyState}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.97, transition: { duration: 0.15 } }}
    >
      <div className={styles.roseWrap}>
        <CompassRose />
      </div>
      <h1 className={styles.emptyHeading}>The Grand Archive Awaits</h1>
      <p className={styles.emptySub}>Ask anything about the world. Inquire into its oldest mysteries.</p>
      <div className={styles.wantedRow}>
        {questions.map((item) => (
          <motion.button
            key={item.question}
            type="button"
            className={styles.wantedCard}
            onClick={() => submit(item.question)}
            disabled={isStreaming}
            whileHover={{ y: -3, boxShadow: '0 8px 28px rgba(0,0,0,0.4)' }}
          >
            <span className={styles.wantedTag}>{item.tag}</span>
            <span className={styles.wantedQuestion}>{item.question}</span>
          </motion.button>
        ))}
      </div>
    </motion.section>
  );
}
