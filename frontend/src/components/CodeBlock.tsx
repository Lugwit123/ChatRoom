import React, { useEffect, useRef } from 'react';
import './CodeBlock.css';

interface CodeBlockProps {
    children: React.ReactNode;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ children }) => {
    const codeRef = useRef<HTMLPreElement>(null);

    useEffect(() => {
        const codeBlocks = document.querySelectorAll('pre');
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
    }, []);

    return (
        <pre ref={codeRef}>
            {children}
        </pre>
    );
};

export default CodeBlock;
