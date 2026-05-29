import { useMemo, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, TriangleAlert } from 'lucide-react';
import { useGeoSmartStore } from '@/store/useGeoSmartStore';
import type { ZoneResult } from '@/types';
import { ZoneCard } from './ZoneCard';
import { ScoreGauge } from './ScoreGauge';

type AnalysisPanelProps = {
  onTrackEvent?: (name: string, data?: Record<string, unknown>) => void;
};

const sectionNames = ['financial', 'competitive', 'demographic'] as const;

export function AnalysisPanel({ onTrackEvent }: AnalysisPanelProps) {
  const analysisResult = useGeoSmartStore((state) => state.analysisResult);
  const activeZone = useGeoSmartStore((state) => state.activeZone);
  const uiFocus = useGeoSmartStore((state) => state.uiFocus);
  const setActiveZone = useGeoSmartStore((state) => state.setActiveZone);
  const setViewState = useGeoSmartStore((state) => state.setViewState);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const sectionEnterAt = useRef<Record<string, number>>({});

  const topZones = analysisResult?.top_zones ?? [];

  const focusedScale = useMemo(() => {
    if (uiFocus === 'financial') {
      return { score: 1.18, competitive: 1.0, demographic: 1.0 };
    }
    if (uiFocus === 'competitive') {
      return { score: 1.0, competitive: 1.18, demographic: 1.0 };
    }
    if (uiFocus === 'demographic') {
      return { score: 1.0, competitive: 1.0, demographic: 1.18 };
    }
    return { score: 1.0, competitive: 1.0, demographic: 1.0 };
  }, [uiFocus]);

  const selectZone = (zone: ZoneResult) => {
    setActiveZone(zone);
    setViewState({ longitude: zone.lon, latitude: zone.lat, zoom: 14, pitch: 45, bearing: 0 });
    onTrackEvent?.('zone_click', { zone_id: zone.zone_id, score: zone.score });
  };

  const beginSection = (section: string) => {
    sectionEnterAt.current[section] = window.performance.now();
  };

  const endSection = (section: string) => {
    const start = sectionEnterAt.current[section];
    if (typeof start === 'number') {
      const dwellTimeMs = window.performance.now() - start;
      onTrackEvent?.('section_dwell', { section, dwellTimeMs });
    }
  };

  return (
    <motion.aside
      initial={{ x: 400 }}
      animate={{ x: 0 }}
      transition={{ type: 'spring', stiffness: 120, damping: 20 }}
      className="geo-panel absolute right-0 top-0 z-20 flex h-full w-[min(380px,34vw)] flex-col"
    >
      <div
        ref={scrollRef}
        onScroll={(event) => onTrackEvent?.('panel_scroll', { scrollTop: event.currentTarget.scrollTop })}
        className="geo-scrollbar flex-1 overflow-y-auto px-5 py-6"
      >
        {!analysisResult ? (
          <div className="mt-10 space-y-4 text-sm text-text-secondary">
            <div className="text-xs uppercase tracking-[0.22em] text-text-secondary">Analysis</div>
            <div>Choose a location to run the spatial pipeline and generate viability intelligence.</div>
          </div>
        ) : (
          <div className="space-y-6">
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-xs uppercase tracking-[0.24em] text-text-secondary">Top zones</h2>
                <span className="text-[11px] uppercase tracking-[0.22em] text-text-secondary">
                  {analysisResult.top_zones.length} candidates
                </span>
              </div>
              <div className="space-y-2">
                {topZones.map((zone) => (
                  <ZoneCard key={zone.zone_id} zone={zone} active={activeZone?.zone_id === zone.zone_id} onClick={selectZone} />
                ))}
              </div>
            </section>

            <section
              onMouseEnter={() => beginSection('financial')}
              onMouseLeave={() => endSection('financial')}
              className="space-y-4 border border-border bg-white/[0.02] p-4"
              style={{ transform: `scale(${focusedScale.score})`, transformOrigin: 'top left' }}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs uppercase tracking-[0.24em] text-text-secondary">Active zone detail</div>
                {activeZone ? (
                  <span className={`border px-2 py-1 text-[11px] uppercase tracking-[0.18em] ${activeZone.viability_rating === 'Excellent' || activeZone.viability_rating === 'Good' ? 'border-success text-success' : activeZone.viability_rating === 'Moderate' ? 'border-warning text-warning' : 'border-danger text-danger'}`}>
                    {activeZone.viability_rating}
                  </span>
                ) : null}
              </div>
              {activeZone ? (
                <>
                  <ScoreGauge score={activeZone.score} />
                  <div className="text-lg font-semibold text-text-primary">{activeZone.headline}</div>
                  <div className="grid gap-3">
                    <div className="space-y-2">
                      <div className="text-[11px] uppercase tracking-[0.22em] text-text-secondary">Strengths</div>
                      <div className="space-y-1 text-sm text-text-primary">
                        {activeZone.top_strengths.map((item) => (
                          <div key={item} className="flex gap-2">
                            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                            <span>{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="text-[11px] uppercase tracking-[0.22em] text-text-secondary">Risks</div>
                      <div className="space-y-1 text-sm text-text-primary">
                        {activeZone.top_risks.map((item) => (
                          <div key={item} className="flex gap-2">
                            <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
                            <span>{item}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="border border-accent bg-accent/10 p-4 text-sm text-text-primary">
                    <div className="mb-2 text-[11px] uppercase tracking-[0.22em] text-accent">Recommendation</div>
                    {activeZone.recommendation}
                  </div>
                </>
              ) : (
                <div className="text-sm text-text-secondary">Select a zone to inspect the narrative report.</div>
              )}
            </section>

            <section
              onMouseEnter={() => beginSection('competitive')}
              onMouseLeave={() => endSection('competitive')}
              className="space-y-2 border border-border bg-white/[0.02] p-4"
              style={{ transform: `scale(${focusedScale.competitive})`, transformOrigin: 'top left' }}
            >
              <div className="text-[11px] uppercase tracking-[0.22em] text-text-secondary">Area summary</div>
              <div className="text-sm text-text-primary">{analysisResult.analysis_summary}</div>
              <div className="text-xs text-text-secondary">Processing time: {analysisResult.processing_time_ms.toFixed(0)} ms</div>
            </section>

            <section
              onMouseEnter={() => beginSection('demographic')}
              onMouseLeave={() => endSection('demographic')}
              className="space-y-2 border border-border bg-white/[0.02] p-4"
              style={{ transform: `scale(${focusedScale.demographic})`, transformOrigin: 'top left' }}
            >
              <div className="text-[11px] uppercase tracking-[0.22em] text-text-secondary">Data sources</div>
              <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-[0.18em] text-text-secondary">
                {topZones[0]?.data_sources?.map((source) => (
                  <span key={source} className="border border-border px-2 py-1">
                    {source}
                  </span>
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </motion.aside>
  );
}
