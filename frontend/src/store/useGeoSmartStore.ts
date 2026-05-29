import { create } from 'zustand';
import type { AnalyzeResponse, ZoneResult } from '@/types';

export type UIFocus = 'map' | 'financial' | 'competitive' | 'demographic';

export interface ViewState {
  longitude: number;
  latitude: number;
  zoom: number;
  pitch: number;
  bearing: number;
}

interface GeoSmartState {
  selectedCoords: { lat: number; lon: number } | null;
  analysisResult: AnalyzeResponse | null;
  isLoading: boolean;
  activeZone: ZoneResult | null;
  mapViewState: ViewState;
  uiFocus: UIFocus;
  businessCategory: string;
  setCoords: (coords: { lat: number; lon: number } | null) => void;
  setResult: (result: AnalyzeResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setActiveZone: (zone: ZoneResult | null) => void;
  setViewState: (viewState: ViewState) => void;
  setFocus: (focus: UIFocus) => void;
  setBusinessCategory: (category: string) => void;
}

export const useGeoSmartStore = create<GeoSmartState>((set) => ({
  selectedCoords: null,
  analysisResult: null,
  isLoading: false,
  activeZone: null,
  mapViewState: {
    longitude: 77.209,
    latitude: 28.6139,
    zoom: 11,
    pitch: 0,
    bearing: 0,
  },
  uiFocus: 'map',
  businessCategory: 'retail',
  setCoords: (coords) => set({ selectedCoords: coords }),
  setResult: (result) => set({ analysisResult: result }),
  setLoading: (loading) => set({ isLoading: loading }),
  setActiveZone: (zone) => set({ activeZone: zone }),
  setViewState: (viewState) => set({ mapViewState: viewState }),
  setFocus: (focus) => set({ uiFocus: focus }),
  setBusinessCategory: (businessCategory) => set({ businessCategory }),
}));
