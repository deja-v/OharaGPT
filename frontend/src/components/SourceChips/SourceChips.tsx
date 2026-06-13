import { motion } from 'framer-motion';
import type { SourceItem } from '../../types';
import styles from './SourceChips.module.css';

export function SourceChips({ sources }: { sources: SourceItem[] }) {
  return (
    <div className={styles.chips}>
      {sources.map((source, index) => (
        <motion.div
          key={`${source.source}-${source.heading}-${index}`}
          className={styles.chip}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.06 }}
          whileHover={{ y: -1 }}
        >
          ⚓ {source.source} — {source.heading}
        </motion.div>
      ))}
    </div>
  );
}
