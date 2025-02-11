import React, { createContext, useContext, useState, ReactNode } from 'react';

interface ContextMenuItem {
  label: string;
  action: () => void;
}

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  items: ContextMenuItem[];
}

interface ContextMenuContextType {
  menuState: ContextMenuState;
  showMenu: (x: number, y: number, items: ContextMenuItem[]) => void;
  hideMenu: () => void;
}

const ContextMenuContext = createContext<ContextMenuContextType>({
  menuState: {
    visible: false,
    x: 0,
    y: 0,
    items: [],
  },
  showMenu: () => {},
  hideMenu: () => {},
});

interface ContextMenuProviderProps {
  children: ReactNode;
}

export function ContextMenuProvider({ children }: ContextMenuProviderProps) {
  const [menuState, setMenuState] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    items: [],
  });

  const showMenu = (x: number, y: number, items: ContextMenuItem[]) => {
    setMenuState({
      visible: true,
      x,
      y,
      items,
    });
  };

  const hideMenu = () => {
    setMenuState(prev => ({
      ...prev,
      visible: false,
    }));
  };

  return (
    <ContextMenuContext.Provider value={{ menuState, showMenu, hideMenu }}>
      {children}
    </ContextMenuContext.Provider>
  );
}

export const useContextMenu = () => useContext(ContextMenuContext); 