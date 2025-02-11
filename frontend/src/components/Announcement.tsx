// src/components/Announcement.tsx

import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/atom-one-dark.css';
import TableOfContents from './TableOfContents';
import './Announcement.css';

interface AnnouncementProps {
    onClose?: () => void;
    isModal?: boolean;
}

const Announcement: React.FC<AnnouncementProps> = ({ onClose, isModal = false }) => {
    const [content, setContent] = useState<string>('');
    const [showModal, setShowModal] = useState(false);
    const contentRef = useRef<HTMLDivElement>(null);
    const trailsRef = useRef<HTMLDivElement[]>([]);
    const requestRef = useRef<number>();
    const previousTimeRef = useRef<number>();

    useEffect(() => {
        const fetchAnnouncement = async () => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL;
                const response = await fetch(`${apiUrl}/announcement`);
                if (!response.ok) {
                    throw new Error('公告获取失败');
                }
                const data = await response.json();
                setContent(data.content);
            } catch (error) {
                console.error('获取公告失败：', error);
            }
        };

        fetchAnnouncement();
    }, []);

    useEffect(() => {
        const content = contentRef.current;
        if (!content) return;

        let trails: HTMLDivElement[] = [];
        const maxTrails = 35;
        let lastCreated = 0;
        let lastPosition = { x: 0, y: 0 };

        const colors = [
            '#ff6b6b', '#da77f2', '#4dabf7', '#51cf66', '#ffd43b',
            '#ff922b', '#748ffc', '#20c997', '#f06595', '#fab005'
        ];

        const createStar = (x: number, y: number) => {
            const star = document.createElement('div');
            star.className = 'trail-star';
            const color = colors[Math.floor(Math.random() * colors.length)];
            star.style.setProperty('--star-color', color);
            
            // 随机大小 (1-3px)
            const size = 1 + Math.random() * 2;
            star.style.width = `${size}px`;
            star.style.height = `${size}px`;
            
            // 延长动画持续时间 (2-3秒)
            const duration = 2 + Math.random();
            star.style.setProperty('--twinkle-duration', `${duration}s`);
            
            // 随机初始缩放
            const initialScale = 0.8 + Math.random() * 0.4;
            star.style.setProperty('--initial-scale', initialScale.toString());
            
            const spread = 15;
            const randomX = x + (Math.random() - 0.5) * spread;
            const randomY = y + (Math.random() - 0.5) * spread;
            
            star.style.left = `${randomX}px`;
            star.style.top = `${randomY}px`;
            star.style.animationDelay = `${Math.random() * 0.3}s`;  
            document.body.appendChild(star);

            setTimeout(() => star.remove(), duration * 1000);
        };

        const createTrail = (x: number, y: number) => {
            const now = Date.now();
            if (now - lastCreated < 35) return;
            lastCreated = now;

            // 在移动轨迹上生成星星
            if (lastPosition.x !== 0 && lastPosition.y !== 0) {
                const distance = Math.sqrt(
                    Math.pow(x - lastPosition.x, 2) + 
                    Math.pow(y - lastPosition.y, 2)
                );
                if (distance > 20) { // 移动距离足够时生成星星
                    const starCount = 1 + Math.floor(Math.random() * 2);
                    for (let i = 0; i < starCount; i++) {
                        // 在起点和终点之间随机位置生成星星
                        const ratio = Math.random();
                        const starX = lastPosition.x + (x - lastPosition.x) * ratio;
                        const starY = lastPosition.y + (y - lastPosition.y) * ratio;
                        createStar(starX, starY);
                    }
                }
            }
            lastPosition = { x, y };

            const trail = document.createElement('div');
            trail.className = 'mouse-trail';
            const duration = 2 + Math.random() * 1;
            const direction = Math.random() > 0.5 ? 1 : -1;
            const offset = Math.random() * 60;
            trail.style.animation = `trail-fade ${duration}s ease-out forwards`;
            trail.style.left = `${x}px`;
            trail.style.top = `${y}px`;
            trail.style.setProperty('--x-offset', `${direction * offset}px`);
            document.body.appendChild(trail);
            trails.push(trail);

            if (trails.length > maxTrails) {
                const oldTrail = trails.shift();
                oldTrail?.remove();
            }

            setTimeout(() => {
                trail.remove();
                trails = trails.filter(t => t !== trail);
            }, duration * 1000);
        };

        const handleMouseMove = (e: MouseEvent) => {
            createTrail(e.pageX, e.pageY);
        };

        content.addEventListener('mousemove', handleMouseMove);

        return () => {
            content.removeEventListener('mousemove', handleMouseMove);
            trails.forEach(trail => trail.remove());
            if (requestRef.current) {
                cancelAnimationFrame(requestRef.current);
            }
        };
    }, []);

    const addIdsToHeadings = (markdown: string) => {
        return markdown.replace(
            /^(#{1,6})\s+(.+)$/gm,
            (match, hashes, title) => {
                const id = title.toLowerCase().replace(/\s+/g, '-');
                return `${hashes} ${title} {#${id}}`;
            }
        );
    };

    const AnnouncementContent = () => (
        <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeHighlight]}
            components={{
                table: ({node, ...props}) => (
                    <div className="table-container">
                        <table {...props} className="markdown-table" />
                    </div>
                ),
                a: ({node, children, ...props}) => (
                    <a {...props} target="_blank" rel="noopener noreferrer">{children}</a>
                )
            }}
        >
            {addIdsToHeadings(content)}
        </ReactMarkdown>
    );

    if (!isModal) {
        return (
            <div className="announcement-page">
                <TableOfContents content={content} />
                <div className="announcement-container">
                    <div className="announcement-header">
                        <h1>公告</h1>
                    </div>
                    <div ref={contentRef} className="announcement-content">
                        <AnnouncementContent />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <span className="close-button" onClick={onClose}>&times;</span>
                <h2>公告</h2>
                <div ref={contentRef} className="announcement-content">
                    <AnnouncementContent />
                </div>
            </div>
        </div>
    );
}

export default Announcement;
