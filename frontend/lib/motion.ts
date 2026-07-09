import type { Variants } from 'framer-motion';

/** Transition de page : fade + léger slide (150 ms). */
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.15, ease: 'easeOut' } },
  exit: { opacity: 0, y: -8, transition: { duration: 0.1, ease: 'easeIn' } },
};

/** Conteneur d'une liste en stagger — les enfants apparaissent en cascade. */
export const staggerContainer: Variants = {
  animate: { transition: { staggerChildren: 0.05, delayChildren: 0.02 } },
};

/** Élément d'une liste en stagger. */
export const staggerItem: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.25, ease: 'easeOut' } },
};
