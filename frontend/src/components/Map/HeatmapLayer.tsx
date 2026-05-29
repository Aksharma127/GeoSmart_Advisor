// @ts-nocheck
import { HeatmapLayer } from 'deck.gl';
import type { HeatmapPoint } from '@/types';

export function buildHeatmapLayer(data: HeatmapPoint[]) {
  return new HeatmapLayer<HeatmapPoint>({
    id: 'geo-heatmap-layer',
    data,
    getPosition: (point) => [point.lon, point.lat],
    getWeight: (point) => point.weight,
    radiusPixels: 80,
    intensity: 2,
    threshold: 0.03,
    colorRange: [
      [0, 0, 80, 0],
      [0, 50, 150, 100],
      [0, 150, 100, 180],
      [100, 200, 50, 220],
      [255, 200, 0, 240],
      [255, 50, 0, 255],
    ],
  });
}
