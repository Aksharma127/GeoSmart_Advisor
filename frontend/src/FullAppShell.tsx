import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { GeoSmartMap } from '@/components/Map/GeoSmartMap';
import { AnalysisPanel } from '@/components/Panel/AnalysisPanel';
import { LocationSearch } from '@/components/Search/LocationSearch';
import { StatusBar } from '@/components/UI/StatusBar';
import { LoadingOverlay } from '@/components/UI/LoadingOverlay';
import { checkHealth } from '@/api/client';
import { useAnalysis } from '@/hooks/useAnalysis';
import { useTelemetry } from '@/hooks/useTelemetry';
import { useGeoSmartStore } from '@/store/useGeoSmartStore';

export function FullAppShell() {
  const { trackEvent, uiFocus } = useTelemetry();
  const isLoading = useGeoSmartStore((state) => state.isLoading);
  const selectedCoords = useGeoSmartStore((state) => state.selectedCoords);
  const [demoBanner, setDemoBanner] = useState<string | null>(null);
  useAnalysis();

  const healthQuery = useQuery({
    queryKey: ['initial-health'],
    queryFn: checkHealth,
    refetchOnWindowFocus: false,
    retry: 1,
    staleTime: 60_000,
  });

  useEffect(() => {
    if (healthQuery.data && healthQuery.data.status !== 'healthy') {
      setDemoBanner('Running in demo mode');
    }
  }, [healthQuery.data]);

  useEffect(() => {
    if (uiFocus) {
      document.documentElement.dataset.focus = uiFocus;
    }
  }, [uiFocus]);

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-bg text-text-primary">
      <GeoSmartMap onTrackEvent={trackEvent} />
      <LocationSearch onTrackEvent={trackEvent} />
      <AnalysisPanel onTrackEvent={trackEvent} />
      <StatusBar />
      <LoadingOverlay visible={isLoading} />
      <AnimatePresence>
        {demoBanner ? (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="absolute left-1/2 top-4 z-50 -translate-x-1/2 border border-warning bg-warning/10 px-4 py-2 text-xs uppercase tracking-[0.22em] text-warning"
          >
            {demoBanner}
          </motion.div>
        ) : null}
      </AnimatePresence>
      {!selectedCoords ? (
        <div className="pointer-events-none absolute inset-x-0 top-1/2 z-10 -translate-y-1/2 text-center text-xs uppercase tracking-[0.26em] text-text-secondary">
          Search a location or click the map to begin
        </div>
      ) : null}
    </div>
  );
}
