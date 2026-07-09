'use client';

import { motion } from 'framer-motion';
import { pageVariants } from '@/lib/motion';

/** Enveloppe chaque page pour lui donner la transition d'entrée standard. */
export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div variants={pageVariants} initial="initial" animate="animate" className="min-h-full">
      {children}
    </motion.div>
  );
}
