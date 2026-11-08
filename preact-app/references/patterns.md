# Recipes for preact-starter apps

All paths are relative to the app root. Examples obey the starter's tsconfig (`strict`, `verbatimModuleSyntax`, `erasableSyntaxOnly`).

## Add a route

`src/routes/Settings/index.tsx`:

```tsx
export function Settings() {
  return (
    <div class="p-8">
      <h1 class="text-3xl font-bold mb-4">Settings</h1>
    </div>
  )
}
```

`src/app.tsx` — lazy-load it, register before the default route:

```tsx
const Settings = lazy(() => import('./routes/Settings').then((m) => m.Settings))
// ...
<Route path="/settings" component={Settings} />
<Route default component={NotFound} />
```

Route params:

```tsx
// <Route path="/projects/:id" component={Project} />
import { useRoute } from 'preact-iso'

export function Project() {
  const { params } = useRoute()
  return <h1>Project {params.id}</h1>
}
```

Navigation: `<a href="/settings">` for links; programmatic:

```tsx
import { useLocation } from 'preact-iso'
const { route, path } = useLocation()
route('/settings')
```

## Shared layout (nav, shell)

Put it in `src/components/Layout/index.tsx` and wrap the `<Router>` in `src/app.tsx` (inside `LocationProvider` so links and `useLocation` work):

```tsx
import type { ComponentChildren } from 'preact'
import { useLocation } from 'preact-iso'

export function Layout({ children }: { children: ComponentChildren }) {
  const { path } = useLocation()
  const link = (href: string, label: string) => (
    <a href={href} class={path === href ? 'font-semibold text-gray-900' : 'text-gray-500 hover:text-gray-900'}>
      {label}
    </a>
  )
  return (
    <div class="min-h-screen">
      <nav class="flex gap-6 border-b px-8 py-4">{link('/', 'Home')}{link('/settings', 'Settings')}</nav>
      <main>{children}</main>
    </div>
  )
}
```

## Add a domain store

`src/store/todos.ts` — explicit fields (no constructor parameter properties under `erasableSyntaxOnly`):

```ts
import { signal, computed } from '@preact/signals'
import type { UserStore } from './user'

export interface Todo {
  id: string
  text: string
  done: boolean
  owner: string | null
}

export class TodoStore {
  readonly items = signal<Todo[]>([])
  readonly remaining = computed(() => this.items.value.filter((t) => !t.done).length)
  // Only the dependency this store needs. A private field that is never read
  // fails the build (noUnusedLocals), so don't inject stores "just in case".
  private readonly user: UserStore

  constructor(user: UserStore) {
    this.user = user
  }

  add(text: string) {
    const owner = this.user.currentUser.value?.name ?? null
    this.items.value = [...this.items.value, { id: crypto.randomUUID(), text, done: false, owner }]
  }

  toggle(id: string) {
    this.items.value = this.items.value.map((t) => (t.id === id ? { ...t, done: !t.done } : t))
  }

  clearDone() {
    this.items.value = this.items.value.filter((t) => !t.done)
  }
}
```

Rules: replace arrays/objects immutably (assign a new value) so subscribers update; expose actions as methods; wrap several signal writes in `batch(() => { ... })` so subscribers update once; keep `fetch` calls inside store methods and track `isLoading` / `error` signals there.

Register in `src/store/index.tsx`:

```tsx
import { UserStore } from './user'
import { TodoStore } from './todos'

export class AppModel {
  readonly user = new UserStore()
  readonly todos = new TodoStore(this.user) // only what it needs
}
```

Field initializers run in order, so declare dependencies first.

## Async loading in a store

```ts
export class UserStore {
  readonly currentUser = signal<User | null>(null)
  readonly isLoading = signal(false)
  readonly error = signal<string | null>(null)

  async load() {
    this.isLoading.value = true
    this.error.value = null
    try {
      const res = await fetch('/api/me')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      this.currentUser.value = await res.json()
    } catch (e) {
      this.error.value = e instanceof Error ? e.message : String(e)
    } finally {
      this.isLoading.value = false
    }
  }
}
```

Trigger from a component with `useEffect(() => { store.user.load() }, [])`, or from the store's own constructor if it should always load at startup.

## Components

`src/components/TodoItem/index.tsx`:

```tsx
import type { Todo } from '../../store/todos'
import { useStore } from '../../store'

export function TodoItem({ todo }: { todo: Todo }) {
  const store = useStore()
  return (
    <label class="flex items-center gap-2">
      <input type="checkbox" checked={todo.done} onChange={() => store.todos.toggle(todo.id)} />
      <span class={todo.done ? 'line-through text-gray-400' : ''}>{todo.text}</span>
    </label>
  )
}
```

Local UI state with a signal:

```tsx
import { useSignal } from '@preact/signals'

export function NewTodo() {
  const store = useStore()
  const draft = useSignal('')
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        if (draft.value.trim()) store.todos.add(draft.value.trim())
        draft.value = ''
      }}
    >
      <input class="border rounded px-2 py-1" value={draft} onInput={(e) => (draft.value = e.currentTarget.value)} />
    </form>
  )
}
```

Passing a signal itself (`value={draft}`) binds it directly to the DOM without re-rendering the component; use `.value` when you need the component to re-render.

## Theme tokens

Add to `src/index.css` (Tailwind v4, no `tailwind.config.js`):

```css
@import "tailwindcss";

@theme {
  --color-brand-500: oklch(0.62 0.19 260);
  --font-display: "Inter", sans-serif;
}
```

Then use `bg-brand-500`, `font-display`.

## API proxy during development

In `vite.config.ts`:

```ts
export default defineConfig({
  plugins: [preact(), tailwindcss()],
  server: { proxy: { '/api': 'http://localhost:8787' } },
})
```
