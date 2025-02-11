// frontend/src/components/UserInfo.js

import React from 'react';
import '../styles.css';

function UserInfo({ user, onSelect }) {
  return (
    <div className="user-info" onClick={() => onSelect(user)}>
      <p>{user.name}</p>
    </div>
  );
}

export default UserInfo;
