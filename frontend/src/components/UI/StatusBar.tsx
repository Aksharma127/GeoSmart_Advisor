import { useQuery } from '@tanstack/react-query';
import { useGeoSmartStore } from '@/store/useGeoSmartStore';
import { checkHealth } from '@/api/client';

function HealthDot({ live }: { live: boolean }) {
  return <span className={`inline-block h-2.5 w-2.5 rounded-none ${live ? 'bg-success' : 'bg-danger'}`} />;
}

export function StatusBar() {
  const coords = useGeoSmartStore((state) => state.selectedCoords);
  const viewState = useGeoSmartStore((state) => state.mapViewState);
  const analysisResult = useGeoSmartStore((state) => state.analysisResult);

  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    refetchInterval: 30000,
    retry: 1,
  });

  const data = healthQuery.data;
  const lastAnalysis = analysisResult?.timestamp ? new Date(analysisResult.timestamp).toLocaleString() : 'No analysis yet';

  return (
    <div className="absolute bottom-0 left-0 right-0 z-30 flex h-10 items-center justify-between border-t border-border bg-bg/95 px-4 text-[11px] uppercase tracking-[0.18em] text-text-secondary backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5"><HealthDot live={!!data?.services.julia} /> Julia</span>
        <span className="flex items-center gap-1.5"><HealthDot live={!!data?.services.pipeline} /> Pipeline</span>
        <span className="flex items-center gap-1.5"><HealthDot live={!!data?.services.slm} /> SLM</span>
        <span className="ml-3 text-text-secondary">Last analysis: {lastAnalysis}</span>
      </div>
      <div className="flex items-center gap-4">
        <span>{coords ? `${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}` : 'No coordinates selected'}</span>
        <span>Zoom {viewState.zoom.toFixed(1)}</span>
      </div>
    </div>
  );
}
