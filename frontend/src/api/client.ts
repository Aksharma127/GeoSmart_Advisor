import axios from 'axios';
import type { AnalyzeRequest, AnalyzeResponse, ServiceHealth } from '@/types';

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const client = axios.create({
  baseURL,
  timeout: 30000,
});

export async function analyzeLocation(
  lat: number,
  lon: number,
  radiusM: number = 500,
  category: string = 'retail',
  topN: number = 5,
): Promise<AnalyzeResponse> {
  const payload: AnalyzeRequest = {
    lat,
    lon,
    radius_m: radiusM,
    business_category: category,
    top_n: topN,
  };
  const response = await client.post<AnalyzeResponse>('/api/v1/analyze', payload);
  return response.data;
}

export async function checkHealth(): Promise<ServiceHealth> {
  const response = await client.get<ServiceHealth>('/api/v1/health');
  return response.data;
}
