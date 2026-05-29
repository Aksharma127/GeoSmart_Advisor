import { motion } from 'framer-motion';
import type { ZoneResult } from '@/types';

type ZoneCardProps = {
  zone: ZoneResult;
  active?: boolean;
  onClick: (zone: ZoneResult) => void;
};

function ratingTone(rating: string) {
  switch (rating) {
    case 'Excellent':
    case 'Good':
      return 'text-success';
    case 'Moderate':
      return 'text-warning';
    case 'Poor':
    default:
      return 'text-danger';
  }
}

export function ZoneCard({ zone, active = false, onClick }: ZoneCardProps) {
  return (
    <motion.button
      type="button"
      onClick={() => onClick(zone)}
      className={`w-full border px-4 py-3 text-left transition-colors ${active ? 'border-accent bg-white/5' : 'border-border bg-transparent hover:bg-white/5'}`}
      whileTap={{ scale: 0.995 }}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-text-primary">{zone.headline}</div>
          <div className={`mt-1 text-xs uppercase tracking-[0.18em] ${ratingTone(zone.viability_rating)}`}>{zone.viability_rating}</div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-extrabold text-text-primary">{zone.score.toFixed(0)}</div>
          <div className="text-[11px] uppercase tracking-[0.18em] text-text-secondary">score</div>
        </div>
      </div>
    </motion.button>
  );
}
