import { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { useGeoSmartStore, type UIFocus } from '@/store/useGeoSmartStore';

type TelemetryEvent = {
  name: 'zone_click' | 'panel_scroll' | 'map_interaction' | 'section_dwell' | string;
  data: Record<string, unknown>;
  timestamp: string;
};

const baiBase = import.meta.env.VITE_BAI_URL ?? 'http://localhost:8000';

export function useTelemetry() {
  const events = useRef<TelemetryEvent[]>([]);
  const dwellTotals = useRef<Record<string, number>>({});
  const [uiFocus, setUiFocus] = useState<UIFocus>('map');
  const setStoreFocus = useGeoSmartStore((state) => state.setFocus);
  const sessionId = useMemo(() => crypto.randomUUID(), []);

  useEffect(() => {
    const interval = window.setInterval(async () => {
      if (events.current.length === 0) {
        return;
      }

      const batch = events.current.splice(0, events.current.length);
      try {
        await axios.post(`${baiBase.replace(/\/$/, '')}/telemetry`, {
          session_id: sessionId,
          events: batch,
          timestamp: new Date().toISOString(),
        });
      } catch {
        // Telemetry is best-effort.
      }
    }, 5000);

    return () => window.clearInterval(interval);
  }, [sessionId]);

  const recomputeFocus = (section?: string) => {
    if (!section) {
      return;
    }

    const mapped: UIFocus =
      section === 'financial'
        ? 'financial'
        : section === 'competitive'
          ? 'competitive'
          : section === 'demographic'
            ? 'demographic'
            : 'map';

    setUiFocus(mapped);
    setStoreFocus(mapped);
  };

  const trackEvent = (name: TelemetryEvent['name'], data: Record<string, unknown> = {}) => {
    events.current.push({
      name,
      data,
      timestamp: new Date().toISOString(),
    });

    if (name === 'section_dwell' && typeof data.section === 'string' && typeof data.dwellTimeMs === 'number') {
      const section = data.section;
      dwellTotals.current[section] = (dwellTotals.current[section] ?? 0) + data.dwellTimeMs;
      const dominantSection = Object.entries(dwellTotals.current).sort((left, right) => right[1] - left[1])[0]?.[0];
      recomputeFocus(dominantSection);
    }
  };

  return { trackEvent, uiFocus };
}
