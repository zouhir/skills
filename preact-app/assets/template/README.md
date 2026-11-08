# Preact + TypeScript Starter

A minimal Preact starter with TypeScript, Tailwind CSS, and preact-iso routing.

## Stack

- **Preact** - Fast 3kB React alternative
- **TypeScript** - Type safety
- **Vite** - Fast dev server and builds
- **Tailwind CSS** - Utility-first CSS
- **preact-iso** - Lightweight router
- **@preact/signals** - Reactive state management

## Getting Started

```bash
npm install
npm run dev
```

## Project Structure

```
src/
├── components/     # Reusable UI components (not created yet; add when needed)
├── routes/         # Page components
│   ├── Home/
│   └── NotFound/   # Lazy-loaded 404 route
├── store/          # State management (AppModel pattern)
├── app.tsx         # Router setup
├── main.tsx        # Entry point
└── index.css       # Tailwind import
```

## State Management

Uses a class-based AppModel with Preact Signals, passed via context:

```tsx
// src/store/index.tsx: add domain stores as fields
export class AppModel {
  readonly user = new UserStore()
  // Pass only the dependencies a store needs, not the whole AppModel
  readonly cart = new CartStore(this.user)
}

// Access store in components
import { useStore } from './store'

function MyComponent() {
  const store = useStore() // throws if used outside <StoreProvider>
  // store.user, store.cart, etc.
}
```

## Styling

Tailwind CSS utilities only. Avoid adding a second styling system.

## Scripts

- `npm run dev` - Start dev server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
