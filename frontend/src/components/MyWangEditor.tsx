// frontend/src/components/MyWangEditor.tsx

import '@wangeditor/editor/dist/css/style.css'; // 引入 WangEditor 的 CSS
import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Editor, Toolbar } from '@wangeditor/editor-for-react';
import { IDomEditor, IEditorConfig, IToolbarConfig } from '@wangeditor/editor';
import './MyWangEditor.css';
import imageCompression from 'browser-image-compression'; // 导入图片压缩库
import { apiUrl } from '../services/api';

interface MyWangEditorProps {
    className?: string; // 可选的 className 参数
    initialValue?: string; // 接收外部传递的初始内容
    onSend?: (content: string) => void; // 修改 onSend 回调，传递内容
}

// 定义上传成功后服务器返回的响应类型
interface UploadSuccessResponse {
    url: string;
}

// 定义上传失败后服务器返回的响应类型
interface UploadFailResponse {
    message: string;
}

// 定义通过 ref 暴露的方法
export interface MyWangEditorHandle {
    getContent: () => string;
    setContent: (content: string) => void;
    getText : () => string
}

const MyWangEditor = forwardRef<MyWangEditorHandle, MyWangEditorProps>(
    ({ className = '', initialValue = "", onSend }, ref) => {
        // editor 实例
        const [editor, setEditor] = useState<IDomEditor | null>(null);
        // 管理编辑器内容的状态
        const [editorContent, setEditorContent] = useState<string>(initialValue);
        // 状态管理用于显示/隐藏代码视图
        const [showCode, setShowCode] = useState<boolean>(false);

        // 添加键盘事件监听
        useEffect(() => {
            if (editor) {
                const handleKeyDown = (event: KeyboardEvent) => {
                    if (event.ctrlKey && event.key === 'Enter') {
                        event.preventDefault();
                        if (onSend) {
                            onSend(editorContent);
                        }
                    }
                };

                const editorElem = editor.getEditableContainer();
                editorElem.addEventListener('keydown', handleKeyDown);

                return () => {
                    editorElem.removeEventListener('keydown', handleKeyDown);
                };
            }
        }, [editor, editorContent, onSend]);

        // 工具栏配置
        const toolbarConfig: Partial<IToolbarConfig> = {
            // 根据需要排除或添加工具栏按钮
            excludeKeys: [], // 示例：排除某些按钮
        };

        // 上传配置
        const uploadConfig = {
            server: `${apiUrl}/upload`,
            fieldName: 'file',
            maxFileSize: 1024 * 1024 * 50, // 50MB
            maxNumberOfFiles: 1,
            allowedFileTypes: ['image/*', 'video/*'],
        };

        // 编辑器配置
        const editorConfig: Partial<IEditorConfig> = {
            placeholder: '请输入内容...',
            MENU_CONF: {
                // 自定义上传图片
                uploadImage: {
                    ...uploadConfig,
                    allowedFileTypes: ['image/*'],
                    maxFileSize: 1024 * 1024 * 10, // 图片限制 10MB
                    maxNumberOfFiles: 5,
                    customUpload: async (files, insertFn) => {
                        try {
                            // 确保 files 为数组
                            const fileArray = Array.isArray(files) ? files : [files];
                            if (fileArray.length > uploadConfig.maxNumberOfFiles) {
                                alert(`一次最多上传 ${uploadConfig.maxNumberOfFiles} 个文件`);
                                return;
                            }
                            
                            // 压缩图片
                            const compressedFiles = await (await Promise.all(
                                fileArray.map(async (file) => {
                                    try {
                                        const options = {
                                            maxSizeMB: 1,
                                            maxWidthOrHeight: 1920,
                                            useWebWorker: true,
                                        };
                                        return await imageCompression(file, options);
                                    } catch (error) {
                                        return null;
                                    }
                                })
                            )).filter(file => file !== null);

                            if (!compressedFiles.length) {
                                alert('没有可上传的文件');
                                return;
                            }

                            // 创建 FormData
                            const formData = new FormData();
                            compressedFiles.forEach(file => {
                                formData.append(uploadConfig.fieldName, file);
                            });

                            // 上传图片
                            const response = await fetch(uploadConfig.server, {
                                method: 'POST',
                                body: formData,
                            });

                            if (!response.ok) {
                                throw new Error('上传失败');
                            }

                            const result = await response.json();

                            // 插入图片到编辑器
                            if (result.errno === 0) {
                                insertFn(result.data.url);
                            } else {
                                throw new Error(result.message || '上传失败');
                            }
                        } catch (error) {
                            alert(`图片上传失败: ${error.message}`);
                        }
                    },
                },
                // 自定义上传视频
                uploadVideo: {
                    ...uploadConfig,
                    allowedFileTypes: ['video/*'],
                    maxFileSize: 1024 * 1024 * 50, // 视频限制 50MB
                    maxNumberOfFiles: 1,
                    customUpload: async (files, insertFn) => {
                        try {
                            // 确保 files 为数组
                            const fileArray = Array.isArray(files) ? files : [files];
                            if (fileArray.length > 1) {
                                alert('一次只能上传一个视频文件');
                                return;
                            }

                            // 检查文件大小
                            if (fileArray[0].size > uploadConfig.maxFileSize) {
                                alert(`视频文件大小不能超过 ${uploadConfig.maxFileSize / 1024 / 1024}MB`);
                                return;
                            }

                            // 创建 FormData
                            const formData = new FormData();
                            formData.append(uploadConfig.fieldName, fileArray[0]);

                            // 上传视频
                            const response = await fetch(uploadConfig.server, {
                                method: 'POST',
                                body: formData,
                            });

                            if (!response.ok) {
                                throw new Error('上传失败');
                            }

                            const result = await response.json();

                            // 插入视频到编辑器
                            if (result.errno === 0) {
                                insertFn(result.data.url);
                            } else {
                                throw new Error(result.message || '上传失败');
                            }
                        } catch (error) {
                            alert(`视频上传失败: ${error.message}`);
                        }
                    },
                },
            }
        };

        // 监听编辑器内容变化
        useEffect(() => {
            if (editor) {
                editor.on('change', () => {
                    const content = editor.getHtml();
                    setEditorContent(content);
                });
            }
        }, [editor]);

        // 使用 useImperativeHandle 暴露方法给父组件
        useImperativeHandle(ref, () => ({
            getContent: () => {
                return editor ? editor.getHtml() : editorContent;
            },
            setContent: (content: string) => {
                if (editor) {
                    editor.setHtml(content);
                    setEditorContent(content);
                }
            },
            clearContent: () => {
                if (editor) {
                    editor.clear();
                    setEditorContent('');
                }
            },
            getText: () => {
                if (editor) {
                    return editor.getText();
                }
                return '123';
            }
        }), [editor, editorContent]);

        // 及时销毁 editor
        useEffect(() => {
            return () => {
                if (editor == null) return;
                editor.destroy();
                setEditor(null);
            };
        }, [editor]);

        // 切换代码视图的函数
        const toggleShowCode = () => {
            setShowCode(!showCode);
        };

        // 复制代码的函数
        const copyCode = () => {
            navigator.clipboard.writeText(editorContent).then(() => {
                alert('代码已复制到剪贴板！');
            }).catch(err => {
                alert('复制失败，请重试。');
            });
        };

        return (
            <div className={`my-wang-editor ${className}`}>
                <div style={{ border: '1px solid #ccc', zIndex: 100, position: 'relative' }}>
                    <Toolbar
                        editor={editor}
                        defaultConfig={toolbarConfig}
                        mode="default"
                    />
                    <Editor
                        defaultConfig={editorConfig}
                        value={editorContent}
                        onCreated={setEditor}
                        onChange={(editor) => setEditorContent(editor.getHtml())}
                        mode="default"
                    />
                    {/* 添加显示代码的按钮 */}
                    <div className="editor-actions">
                        <button onClick={toggleShowCode}>
                            {showCode ? '隐藏代码' : '显示代码'}
                        </button>
                        <button onClick={copyCode}>
                            复制代码
                        </button>
                    </div>
                    {showCode && (
                        <pre className="editor-code">
                            {editorContent}
                        </pre>
                    )}
                </div>
            </div>
        );
    }
);

export default MyWangEditor;
