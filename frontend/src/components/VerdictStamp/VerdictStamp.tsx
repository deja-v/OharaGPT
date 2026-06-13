import { motion } from 'framer-motion';
import type { Verdict } from '../../types';
import styles from './VerdictStamp.module.css';

const verdictIcon: Record<Verdict, string> = {
  SUPPORTED: '✓',
  CONTRADICTED: '✗',
  INSUFFICIENT: '?',
};

const verdictLabel: Record<Verdict, string> = {
  SUPPORTED: 'SUP-\nPORTED',
  CONTRADICTED: 'CONTRA-\nDICTED',
  INSUFFICIENT: 'INSUF-\nFICIENT',
};

export function VerdictStamp({ verdict }: { verdict: Verdict }) {
  return (
    <motion.div
      className={`${styles.stamp} ${styles[verdict.toLowerCase()]}`}
      initial={{ opacity: 0, scale: 0.7, rotate: 8 }}
      animate={{ opacity: 1, scale: 1, rotate: 8 }}
      transition={{ type: 'spring', stiffness: 200, damping: 12, delay: 0.5 }}
    >
      <span className={styles.icon}>{verdictIcon[verdict]}</span>
      <span className={styles.label}>{verdictLabel[verdict]}</span>
    </motion.div>
  );
}
