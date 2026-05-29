export interface HeatmapPoint {
  lat: number;
  lon: number;
  weight: number;
}

export interface ZoneResult {
  lat: number;
  lon: number;
  score: number;
  zone_id: string;
  viability_rating: string;
  headline: string;
  top_strengths: string[];
  top_risks: string[];
  recommendation: string;
  breakdown: Record<string, unknown>;
  data_sources: string[];
  is_mock?: boolean;
}

export interface AnalyzeResponse {
  request_id: string;
  top_zones: ZoneResult[];
  heatmap_data: HeatmapPoint[];
  analysis_summary: string;
  processing_time_ms: number;
  timestamp: string;
}

export interface AnalyzeRequest {
  lat: number;
  lon: number;
  radius_m?: number;
  business_category?: string;
  top_n?: number;
}

export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'down';
  services: {
    julia: boolean;
    pipeline: boolean;
    slm: boolean;
  };
  uptime_seconds: number;
}
