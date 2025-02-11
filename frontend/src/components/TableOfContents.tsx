import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './TableOfContents.css';

interface TOCItem {
    id: string;
    text: string;
    level: number;
    index: number;
}

interface TableOfContentsProps {
    content: string;
}

const TableOfContents: React.FC<TableOfContentsProps> = ({ content }) => {
    const [toc, setToc] = useState<TOCItem[]>([]);
    const [activeId, setActiveId] = useState<string>('');
    const [width, setWidth] = useState(280);
    const [isDragging, setIsDragging] = useState(false);
    const tocRef = useRef<HTMLElement>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const usedIds = new Set<string>();
        const contentDiv = document.querySelector('.announcement-content');
        if (!contentDiv) return;

        const codeBlocks = contentDiv.querySelectorAll('pre');
        codeBlocks.forEach(block => {
            if (!block.querySelector('.copy-button')) {
                const button = document.createElement('button');
                button.className = 'copy-button';
                button.innerHTML = '复制';
                button.onclick = async (e) => {
                    e.preventDefault();
                    const code = block.textContent || '';
                    try {
                        await navigator.clipboard.writeText(code);
                        button.innerHTML = '已复制!';
                        setTimeout(() => {
                            button.innerHTML = '复制';
                        }, 2000);
                    } catch (err) {
                        console.error('复制失败:', err);
                        button.innerHTML = '复制失败';
                        setTimeout(() => {
                            button.innerHTML = '复制';
                        }, 2000);
                    }
                };
                block.style.position = 'relative';
                block.appendChild(button);
            }
        });

        const actualHeaders = Array.from(contentDiv.querySelectorAll('h1, h2, h3, h4, h5, h6'));
        const headings = actualHeaders.map((header, index) => {
            const text = header.textContent || '';
            const level = parseInt(header.tagName[1]);
            
            let baseId = text.toLowerCase()
                .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
                .replace(/^-+|-+$/g, '')
                .replace(/-+/g, '-');
            
            let id = baseId;
            let counter = 1;
            while (usedIds.has(id)) {
                id = `${baseId}-${counter}`;
                counter++;
            }
            usedIds.add(id);
            
            return { id, text, level, index };
        });

        setToc(headings);

        const addIdsToHeadings = () => {
            contentDiv.querySelectorAll('[id^="anchor-"]').forEach(el => el.remove());
            actualHeaders.forEach((header, index) => {
                if (index < headings.length) {
                    const { id } = headings[index];
                    header.id = id;
                    
                    const anchor = document.createElement('div');
                    anchor.id = `anchor-${id}`;
                    anchor.style.position = 'relative';
                    anchor.style.top = '-20px';
                    anchor.style.visibility = 'hidden';
                    anchor.style.pointerEvents = 'none';
                    header.parentNode?.insertBefore(anchor, header);
                }
            });
        };

        addIdsToHeadings();

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const id = entry.target.id.replace('anchor-', '');
                        setActiveId(id);
                    }
                });
            },
            { rootMargin: '0px 0px -80% 0px' }
        );

        document.querySelectorAll('[id^="anchor-"]').forEach((el) => observer.observe(el));

        return () => observer.disconnect();
    }, [content]);

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsDragging(true);
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';
    };

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isDragging) return;
            
            const newWidth = Math.max(200, Math.min(e.clientX, 500));
            setWidth(newWidth);

            // 更新内容区域的margin-left
            const container = document.querySelector('.announcement-container');
            if (container) {
                (container as HTMLElement).style.marginLeft = `${newWidth}px`;
            }
        };

        const handleMouseUp = () => {
            setIsDragging(false);
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
        };

        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, [isDragging]);

    const scrollToHeading = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <aside 
            ref={tocRef as React.RefObject<HTMLElement>} 
            className="table-of-contents"
            style={{ width: `${width}px` }}
        >
            <div className="toc-header">
                <span>目录</span>
                <button className="back-button" onClick={() => navigate('/')}>
                    返回
                </button>
            </div>
            <div className="toc-content">
                {toc.map((item) => (
                    <div
                        key={item.id}
                        className={`toc-item level-${item.level} ${activeId === item.id ? 'active' : ''}`}
                        onClick={() => scrollToHeading(item.id)}
                        style={{ paddingLeft: `${(item.level - 1) * 16 + 16}px` }}
                    >
                        {item.text}
                    </div>
                ))}
            </div>
            <div 
                className="resize-handle"
                onMouseDown={handleMouseDown}
            />
        </aside>
    );
};

export default TableOfContents;
