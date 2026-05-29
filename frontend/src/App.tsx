import { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { LightDashboard } from '@/LightDashboard';

const FullAppShell = lazy(() => import('@/FullAppShell').then((module) => ({ default: module.FullAppShell })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const lightMode = import.meta.env.VITE_LIGHT_MODE === '1';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      {lightMode ? (
        <LightDashboard />
      ) : (
        <Suspense fallback={<div className="grid h-screen place-items-center bg-bg text-text-secondary">Loading map...</div>}>
          <FullAppShell />
        </Suspense>
      )}
    </QueryClientProvider>
  );
}
