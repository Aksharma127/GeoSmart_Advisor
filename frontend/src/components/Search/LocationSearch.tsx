import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Loader2, Search } from 'lucide-react';
import { useDebounce } from '@/hooks/useDebounce';
import { useGeoSmartStore } from '@/store/useGeoSmartStore';

const foursquareCategoryIds: Record<string, string> = {
  retail: '4d4b7105d754a06378d81259',
  restaurant: '4d4b7105d754a06374d81259',
  cafe: '4bf58dd8d48988d1e0931735',
  pharmacy: '4bf58dd8d48988d10f951735',
  clinic: '4bf58dd8d48988d104941735',
  gym: '4bf58dd8d48988d175941735',
  salon: '4bf58dd8d48988d110951735',
};

const categories = [
  { label: 'Retail', value: 'retail' },
  { label: 'Restaurant', value: 'restaurant' },
  { label: 'Cafe', value: 'cafe' },
  { label: 'Pharmacy', value: 'pharmacy' },
  { label: 'Clinic', value: 'clinic' },
  { label: 'Gym', value: 'gym' },
  { label: 'Salon', value: 'salon' },
];

type LocationSearchProps = {
  onTrackEvent?: (name: string, data?: Record<string, unknown>) => void;
};

export function LocationSearch({ onTrackEvent }: LocationSearchProps) {
  const [query, setQuery] = useState('Connaught Place, New Delhi');
  const [isSearching, setIsSearching] = useState(false);
  const selectedCategory = useGeoSmartStore((state) => state.businessCategory);
  const setCoords = useGeoSmartStore((state) => state.setCoords);
  const setViewState = useGeoSmartStore((state) => state.setViewState);
  const setBusinessCategory = useGeoSmartStore((state) => state.setBusinessCategory);
  const setFocus = useGeoSmartStore((state) => state.setFocus);
  const debouncedQuery = useDebounce(query, 400);

  const categoryId = useMemo(() => foursquareCategoryIds[selectedCategory] ?? foursquareCategoryIds.retail, [selectedCategory]);

  const geocode = async (searchText: string) => {
    const value = searchText.trim();
    if (!value) {
      return;
    }
    setIsSearching(true);
    try {
      const response = await axios.get('https://nominatim.openstreetmap.org/search', {
        params: {
          q: value,
          format: 'json',
          limit: 1,
        },
        headers: {
          'Accept': 'application/json',
        },
      });
      const result = response.data?.[0];
      if (result) {
        const lat = Number(result.lat);
        const lon = Number(result.lon);
        setCoords({ lat, lon });
        setViewState({ longitude: lon, latitude: lat, zoom: 14, pitch: 45, bearing: 0 });
        setFocus('map');
        onTrackEvent?.('map_interaction', { search: true, query: value });
      }
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    if (debouncedQuery.trim().length > 2) {
      geocode(debouncedQuery).catch(() => undefined);
    }
  }, [debouncedQuery]);

  return (
    <div className="absolute left-4 top-4 z-30 w-[min(460px,calc(100vw-24px))] border border-border bg-surface/95 p-3 shadow-panel backdrop-blur-md">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          geocode(query).catch(() => undefined);
        }}
        className="space-y-3"
      >
        <div className="flex items-center gap-2 border border-border bg-bg px-3 py-2">
          <Search className="h-4 w-4 text-text-secondary" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search a city, neighborhood, or landmark"
            className="w-full bg-transparent text-sm text-text-primary outline-none placeholder:text-text-secondary"
          />
          {isSearching ? <Loader2 className="h-4 w-4 animate-spin text-accent" /> : null}
        </div>

        <div className="flex items-center gap-3">
          <label className="text-[11px] uppercase tracking-[0.22em] text-text-secondary">Category</label>
          <select
            value={selectedCategory}
            onChange={(event) => {
              setBusinessCategory(event.target.value);
              onTrackEvent?.('section_dwell', { section: 'category', dwellTimeMs: 0, categoryId: foursquareCategoryIds[event.target.value] });
            }}
            className="border border-border bg-bg px-3 py-2 text-sm text-text-primary outline-none"
          >
            {categories.map((category) => (
              <option key={category.value} value={category.value}>
                {category.label}
              </option>
            ))}
          </select>
          <span className="text-[11px] uppercase tracking-[0.22em] text-text-secondary">FSQ {categoryId}</span>
          <button
            type="submit"
            className="ml-auto border border-accent bg-accent px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-white"
          >
            Locate
          </button>
        </div>
      </form>
    </div>
  );
}
