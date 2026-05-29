import { AnimatePresence, motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const messages = [
  'Querying infrastructure data...',
  'Analyzing competitor density...',
  'Running spatial simulation...',
  'Generating viability report...',
];

type LoadingOverlayProps = {
  visible: boolean;
};

export function LoadingOverlay({ visible }: LoadingOverlayProps) {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (!visible) {
      return;
    }
    const interval = window.setInterval(() => {
      setMessageIndex((current) => (current + 1) % messages.length);
    }, 1800);
    return () => window.clearInterval(interval);
  }, [visible]);

  return (
    <AnimatePresence>
      {visible ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="pointer-events-none absolute inset-0 z-40 flex items-center justify-center bg-black/35 backdrop-blur-[1px]"
        >
          <motion.div
            key={messages[messageIndex]}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="border border-border bg-surface px-6 py-4 text-sm text-text-primary shadow-panel"
          >
            {messages[messageIndex]}
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
