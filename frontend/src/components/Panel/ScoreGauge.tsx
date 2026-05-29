import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';

type ScoreGaugeProps = {
  score: number;
};

function describeArc(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const polarToCartesian = (centerX: number, centerY: number, radiusValue: number, angleInDegrees: number) => {
    const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
    return {
      x: centerX + radiusValue * Math.cos(angleInRadians),
      y: centerY + radiusValue * Math.sin(angleInRadians),
    };
  };

  const start = polarToCartesian(cx, cy, radius, startAngle);
  const end = polarToCartesian(cx, cy, radius, endAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';

  return [
    'M',
    start.x,
    start.y,
    'A',
    radius,
    radius,
    0,
    largeArcFlag,
    0,
    end.x,
    end.y,
  ].join(' ');
}

function interpolateColor(score: number) {
  if (score <= 50) {
    const t = score / 50;
    return {
      r: Math.round(239 + (245 - 239) * t),
      g: Math.round(68 + (158 - 68) * t),
      b: Math.round(68 + (11 - 68) * t),
    };
  }

  const t = (score - 50) / 50;
  return {
    r: Math.round(245 + (16 - 245) * t),
    g: Math.round(158 + (185 - 158) * t),
    b: Math.round(11 + (129 - 11) * t),
  };
}

export function ScoreGauge({ score }: ScoreGaugeProps) {
  const [displayScore, setDisplayScore] = useState(0);
  const animatedScore = Math.round(Math.max(0, Math.min(100, score)));
  const path = useMemo(() => describeArc(60, 60, 44, 225, -45), []);
  const pathLength = 2 * Math.PI * 44 * 0.75;
  const progress = pathLength * (1 - animatedScore / 100);
  const color = interpolateColor(animatedScore);

  useEffect(() => {
    const duration = 1200;
    const start = window.performance.now();
    let frame = 0;

    const tick = (now: number) => {
      const progressRatio = Math.min(1, (now - start) / duration);
      setDisplayScore(Math.round(animatedScore * progressRatio));
      if (progressRatio < 1) {
        frame = window.requestAnimationFrame(tick);
      }
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [animatedScore]);

  return (
    <div className="flex items-center gap-4">
      <svg width="120" height="120" viewBox="0 0 120 120" aria-label="score gauge">
        <path d={path} fill="none" stroke="#1E1E2E" strokeWidth="8" strokeLinecap="round" />
        <path
          d={path}
          fill="none"
          stroke={`rgb(${color.r}, ${color.g}, ${color.b})`}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={pathLength}
          strokeDashoffset={progress}
          style={{ transition: 'stroke-dashoffset 1.2s ease' }}
        />
        <text x="60" y="66" textAnchor="middle" fill="#F1F5F9" fontSize="22" fontWeight="800">
          {displayScore}
        </text>
      </svg>
      <div>
        <div className="text-xs uppercase tracking-[0.24em] text-text-secondary">Viability score</div>
        <motion.div
          className="text-sm text-text-primary"
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
        >
          {animatedScore}/100
        </motion.div>
      </div>
    </div>
  );
}
