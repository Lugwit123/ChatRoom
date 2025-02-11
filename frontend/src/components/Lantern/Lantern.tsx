import React from 'react';
import './lantern.css';

const Lantern: React.FC = () => {
  const characters = ['新', '年', '快', '乐'];  // 只使用两个字

  return (
    <div className="lantern-container">
      {characters.map((char, index) => (
        <div key={index} className="lantern" style={{ animationDelay: `${index * 0.5}s` }}>
          <div className="lantern-string"></div>
          <div className="lantern-body">
            <div className="lantern-glow"></div>
          </div>
          <div className="lantern-top"></div>
          <div className="lantern-bottom">
            <div className="lantern-bottom-ring"></div>
            <div className="lantern-bottom-sticks">
              <div className="lantern-bottom-stick"></div>
              <div className="lantern-bottom-stick"></div>
              <div className="lantern-bottom-stick"></div>
            </div>
          </div>
          <div className="lantern-text">{char}</div>
          <div className="lantern-tassel">
            <div className="lantern-tassel-line"></div>
            <div className="lantern-tassel-line"></div>
            <div className="lantern-tassel-line"></div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default Lantern;
