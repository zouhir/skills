import { createContext, type ComponentChildren } from 'preact'
import { useContext, useState } from 'preact/hooks'

export class AppModel {
  // Add domain stores here as your app grows. Pass each store only the
  // dependencies it needs, rather than the whole AppModel:
  //
  // readonly user = new UserStore()
  // readonly cart = new CartStore(this.user)
}

const StoreContext = createContext<AppModel | null>(null)

export function StoreProvider({ children }: { children: ComponentChildren }) {
  // Lazy initializer: the store is created once, not on every re-render
  const [store] = useState(() => new AppModel())
  return <StoreContext.Provider value={store}>{children}</StoreContext.Provider>
}

export function useStore(): AppModel {
  const store = useContext(StoreContext)
  if (!store) {
    throw new Error('useStore() must be used inside <StoreProvider>')
  }
  return store
}
