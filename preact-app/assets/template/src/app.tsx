import { LocationProvider, ErrorBoundary, Router, Route, lazy } from 'preact-iso'
import { Home } from './routes/Home'

// Routes loaded on demand get their own chunk. Keep the landing route eager
// so the first paint doesn't wait on an extra request.
const NotFound = lazy(() => import('./routes/NotFound').then((m) => m.NotFound))

export function App() {
  return (
    <LocationProvider>
      <ErrorBoundary>
        <Router>
          <Route path="/" component={Home} />
          <Route default component={NotFound} />
        </Router>
      </ErrorBoundary>
    </LocationProvider>
  )
}
