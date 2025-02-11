// src/components/ContextMenu.tsx

import React, { useEffect, useRef } from 'react';
import { useContextMenu } from '../contexts/ContextMenuContext';
import './ContextMenu.css';

const ContextMenu: React.FC = () => {
  const { menuState, hideMenu } = useContextMenu();
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        hideMenu();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [hideMenu]);

  if (!menuState.visible) return null;

  return (
    <div
      ref={menuRef}
      className="context-menu"
      style={{
        position: 'fixed',
        top: menuState.y,
        left: menuState.x,
      }}
    >
      {menuState.items.map((item, index) => (
        <div
          key={index}
          className="context-menu-item"
          onClick={() => {
            item.action();
            hideMenu();
          }}
        >
          {item.label}
        </div>
      ))}
    </div>
  );
};

export default ContextMenu;
