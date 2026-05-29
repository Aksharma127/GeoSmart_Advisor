import { useEffect, useMemo, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { analyzeLocation } from '@/api/client';
import { useGeoSmartStore } from '@/store/useGeoSmartStore';

export function useAnalysis() {
  const selectedCoords = useGeoSmartStore((state) => state.selectedCoords);
  const businessCategory = useGeoSmartStore((state) => state.businessCategory);
  const setResult = useGeoSmartStore((state) => state.setResult);
  const setLoading = useGeoSmartStore((state) => state.setLoading);
  const setActiveZone = useGeoSmartStore((state) => state.setActiveZone);
  const currentRequest = useRef(0);

  const mutation = useMutation({
    mutationFn: async ({ lat, lon, category }: { lat: number; lon: number; category: string }) =>
      analyzeLocation(lat, lon, 500, category, 5),
    onMutate: () => setLoading(true),
    onSuccess: (result) => {
      setResult(result);
      setActiveZone(result.top_zones[0] ?? null);
      setLoading(false);
    },
    onError: () => setLoading(false),
  });

  useEffect(() => {
    if (!selectedCoords) {
      return;
    }

    const requestId = ++currentRequest.current;
    mutation
      .mutateAsync({
        lat: selectedCoords.lat,
        lon: selectedCoords.lon,
        category: businessCategory,
      })
      .catch(() => undefined)
      .finally(() => {
        if (requestId === currentRequest.current) {
          setLoading(false);
        }
      });
  }, [businessCategory, mutation, selectedCoords, setLoading]);

  return {
    analyzeLocation: mutation.mutateAsync,
    isLoading: mutation.isPending,
  };
}
