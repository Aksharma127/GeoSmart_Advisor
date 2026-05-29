// @ts-nocheck
import { useMemo, useRef } from 'react';
import { DeckGL } from 'deck.gl';
import Map from 'react-map-gl/maplibre';
import type { ViewStateChangeParameters } from 'react-map-gl/maplibre';
import { buildHeatmapLayer } from './HeatmapLayer';
import { buildZoneMarkerLayers } from './ZoneMarkers';
import { useGeoSmartStore } from '@/store/useGeoSmartStore';
import type { AnalyzeResponse, ZoneResult } from '@/types';

type GeoSmartMapProps = {
  onTrackEvent?: (name: string, data?: Record<string, unknown>) => void;
};

export function GeoSmartMap({ onTrackEvent }: GeoSmartMapProps) {
  const analysisResult = useGeoSmartStore((state) => state.analysisResult);
  const mapViewState = useGeoSmartStore((state) => state.mapViewState);
  const setViewState = useGeoSmartStore((state) => state.setViewState);
  const setCoords = useGeoSmartStore((state) => state.setCoords);
  const setActiveZone = useGeoSmartStore((state) => state.setActiveZone);
  const setFocus = useGeoSmartStore((state) => state.setFocus);
  const previousZoom = useRef(mapViewState.zoom);

  const layers = useMemo(() => {
    const layerList = [];
    if (analysisResult?.heatmap_data?.length) {
      layerList.push(buildHeatmapLayer(analysisResult.heatmap_data));
    }
    if (analysisResult?.top_zones?.length) {
      layerList.push(
        ...buildZoneMarkerLayers(analysisResult.top_zones, (zone: ZoneResult) => {
          setActiveZone(zone);
          setFocus('competitive');
          onTrackEvent?.('zone_click', { zone_id: zone.zone_id, score: zone.score });
        }),
      );
    }
    return layerList;
  }, [analysisResult, onTrackEvent, setActiveZone, setFocus]);

  const handleViewStateChange = (params: ViewStateChangeParameters) => {
    const nextViewState = params.viewState;
    onTrackEvent?.('map_interaction', { zoomDelta: nextViewState.zoom - previousZoom.current });
    previousZoom.current = nextViewState.zoom;
    setViewState({
      longitude: nextViewState.longitude,
      latitude: nextViewState.latitude,
      zoom: nextViewState.zoom,
      pitch: nextViewState.pitch,
      bearing: nextViewState.bearing,
    });
  };

  return (
    <DeckGL
      layers={layers}
      viewState={mapViewState}
      controller={{ dragRotate: true, touchRotate: true }}
      onViewStateChange={handleViewStateChange}
      onClick={(info) => {
        if (!info.object && info.coordinate) {
          const [lon, lat] = info.coordinate as [number, number];
          setCoords({ lat, lon });
          setFocus('map');
          setViewState({ longitude: lon, latitude: lat, zoom: 14, pitch: 45, bearing: 0 });
          onTrackEvent?.('map_interaction', { clicked: true });
        }
      }}
      getCursor={({ isHovering }) => (isHovering ? 'crosshair' : 'default')}
      style={{ position: 'absolute', inset: 0 }}
    >
      <Map
        reuseMaps
        mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        attributionControl={false}
      />
    </DeckGL>
  );
}
