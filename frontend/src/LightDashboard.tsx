import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { CheckCircle2, ExternalLink, MapPin, Server, ShieldAlert, TrendingUp } from 'lucide-react';
import type { AnalyzeResponse, ZoneResult } from '@/types';

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

async function fetchDemo(): Promise<AnalyzeResponse> {
  const response = await axios.get<AnalyzeResponse>(`${baseURL}/api/v1/demo`, { timeout: 8000 });
  return response.data;
}

function scoreColor(score: number) {
  if (score >= 75) return 'text-success';
  if (score >= 55) return 'text-warning';
  return 'text-danger';
}

function ZoneRow({ zone }: { zone: ZoneResult }) {
  return (
    <article className="border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-text-secondary">{zone.zone_id}</p>
          <h2 className="mt-2 text-lg font-semibold text-text-primary">{zone.headline}</h2>
        </div>
        <div className={`text-4xl font-extrabold tabular-nums ${scoreColor(zone.score)}`}>{zone.score.toFixed(0)}</div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div>
          <p className="mb-2 text-xs uppercase tracking-[0.18em] text-success">Strengths</p>
          <ul className="space-y-2 text-sm text-text-secondary">
            {zone.top_strengths.map((item) => (
              <li key={item} className="flex gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-2 text-xs uppercase tracking-[0.18em] text-danger">Risks</p>
          <ul className="space-y-2 text-sm text-text-secondary">
            {zone.top_risks.map((item) => (
              <li key={item} className="flex gap-2">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="mt-4 border border-primary/50 bg-primary/10 p-3 text-sm text-text-primary">{zone.recommendation}</div>
    </article>
  );
}

export function LightDashboard() {
  const demoQuery = useQuery({
    queryKey: ['light-demo'],
    queryFn: fetchDemo,
    retry: 1,
    staleTime: 300_000,
  });

  const result = demoQuery.data;
  const zone = result?.top_zones[0];

  return (
    <main className="min-h-screen overflow-auto bg-bg text-text-primary">
      <section className="border-b border-border bg-surface px-5 py-4">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight">GeoSmart Advisor</h1>
            <p className="mt-1 text-sm text-text-secondary">Light mode dashboard for low-power machines</p>
          </div>
          <a
            href={`${baseURL}/api/v1/demo`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 border border-border px-3 py-2 text-sm text-text-secondary hover:text-text-primary"
          >
            Demo JSON <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-5 py-6 md:grid-cols-3">
        <div className="border border-border bg-surface p-4">
          <MapPin className="h-5 w-5 text-primary" />
          <p className="mt-3 text-xs uppercase tracking-[0.18em] text-text-secondary">Location</p>
          <p className="mt-1 text-lg font-semibold">Connaught Place</p>
          <p className="text-sm text-text-secondary">New Delhi demo zone</p>
        </div>
        <div className="border border-border bg-surface p-4">
          <TrendingUp className="h-5 w-5 text-success" />
          <p className="mt-3 text-xs uppercase tracking-[0.18em] text-text-secondary">Viability</p>
          <p className="mt-1 text-lg font-semibold">{zone ? `${zone.score.toFixed(1)}/100` : 'Loading'}</p>
          <p className="text-sm text-text-secondary">{zone?.viability_rating ?? 'Demo report'}</p>
        </div>
        <div className="border border-border bg-surface p-4">
          <Server className="h-5 w-5 text-warning" />
          <p className="mt-3 text-xs uppercase tracking-[0.18em] text-text-secondary">Runtime</p>
          <p className="mt-1 text-lg font-semibold">Demo light</p>
          <p className="text-sm text-text-secondary">API + static UI only</p>
        </div>
      </section>

      <section className="mx-auto max-w-5xl space-y-4 px-5 pb-8">
        {demoQuery.isLoading ? (
          <div className="border border-border bg-surface p-6 text-text-secondary">Loading demo analysis...</div>
        ) : demoQuery.isError ? (
          <div className="border border-danger bg-danger/10 p-6 text-danger">API is not reachable on {baseURL}.</div>
        ) : (
          <>
            <p className="border border-border bg-surface p-4 text-sm text-text-secondary">{result?.analysis_summary}</p>
            {result?.top_zones.map((item) => <ZoneRow key={item.zone_id} zone={item} />)}
          </>
        )}
      </section>
    </main>
  );
}
