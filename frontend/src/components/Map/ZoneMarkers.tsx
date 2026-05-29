// @ts-nocheck
import { ScatterplotLayer, TextLayer } from 'deck.gl';
import type { ZoneResult } from '@/types';

function scoreToColor(score: number): [number, number, number, number] {
  if (score < 40) {
    return [239, 68, 68, 220];
  }
  if (score < 70) {
    return [245, 158, 11, 220];
  }
  return [16, 185, 129, 220];
}

export function buildZoneMarkerLayers(
  zones: ZoneResult[],
  onClick: (zone: ZoneResult) => void,
) {
  const scatterplotLayer = new ScatterplotLayer<ZoneResult>({
    id: 'geo-zone-markers',
    data: zones,
    getPosition: (zone: ZoneResult) => [zone.lon, zone.lat],
    getRadius: (zone: ZoneResult) => 40 + zone.score * 0.6,
    getFillColor: (zone: ZoneResult) => scoreToColor(zone.score),
    getLineColor: () => [255, 255, 255, 120],
    lineWidthMinPixels: 1,
    stroked: true,
    pickable: true,
    radiusUnits: 'pixels',
    onClick: (info: any) => {
      if (info.object) {
        onClick(info.object);
      }
    },
  });

  const textLayer = new TextLayer<ZoneResult>({
    id: 'geo-zone-labels',
    data: zones.filter((zone) => zone.score > 60),
    getPosition: (zone: ZoneResult) => [zone.lon, zone.lat],
    getText: (zone: ZoneResult) => zone.score.toFixed(0),
    getSize: 14,
    getColor: [255, 255, 255, 200],
    background: true,
    getBackgroundColor: [10, 10, 15, 180],
    getBackgroundPadding: [4, 2, 4, 2],
    fontWeight: 700,
    sizeUnits: 'pixels',
    billboard: true,
  });

  return [scatterplotLayer, textLayer];
}

export { scoreToColor };
