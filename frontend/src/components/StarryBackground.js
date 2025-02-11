// frontend/src/components/StarryBackground.js

import React, { useEffect } from 'react';
import './StarryBackground.css';

function StarryBackground() {
    useEffect(() => {
        const starContainer = document.querySelector('.star-container');
        const numStars = 100;

        for (let i = 0; i < numStars; i++) {
            const star = document.createElement('div');
            star.classList.add('star');
            star.style.top = `${Math.random() * 100}%`;
            star.style.left = `${Math.random() * 100}%`;
            star.style.width = `${Math.random() * 2 + 1}px`;
            star.style.height = `${Math.random() * 2 + 1}px`;
            star.style.background = `hsl(${Math.random() * 360}, 100%, 75%)`;
            starContainer.appendChild(star);
        }
    }, []);

    return <div className="star-container"></div>;
}

export default StarryBackground;
