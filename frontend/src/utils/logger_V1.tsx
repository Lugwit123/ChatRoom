import StackTrace from 'stacktrace-js';

// 辅助函数：异步提取调用者信息
const getCallerInfo = async (): Promise<any[]> => {
    try {
        return["11"];
        
        const stackframes = await StackTrace.get();
        // console.log(new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));
        const len = stackframes.length;
        for (let i = 0; i < len; i++) {
            if (i!==2) continue;
            const frame = stackframes[i];
            let fileName = frame.fileName || 'unknown';
            if (
                fileName.includes('logger.tsx') || // 根据实际文件名调整
                fileName.includes('node_modules')
            ) {
                continue;
            }
            const parts = fileName.split('/');
            const desiredParts = parts.slice(-2);
            fileName = desiredParts.join('/');
            const lineNumber = frame.lineNumber || 0;
            const columnNumber = frame.columnNumber || 0;
            const functionName = frame.functionName || 'anonymous';

            // 跳过与日志相关的堆栈帧
            
            // console.log(new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));
            const localTimestamp = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });
            return [
                `%c${localTimestamp} ${i}/${len}%c file%c:%c ${fileName}%c ,line:%c ${lineNumber}\n%c ,func:%c ${functionName}`,
                'color: #ff8080;', // 时间样式
                'color: #ff8040;', // file 样式
                'color: initial;', // fileName 默认样式
                'color: #00ffff;', // linenum 样式
                'color: #84ffff;', // lineNumber 样式
                'color: #00ff00;', // func 样式
                'color: initial;', // functionName 默认样式
                // 'color: #d1bad8;'  // 消息默认样式
            ];
        }
    } catch (error) {
        console.error('Error in getCallerInfo:', error);
    }
    return null;
};

// 通用的日志方法包装函数
class Logger {
    async info(...args) {
        const callerInfo = await getCallerInfo();
        if (callerInfo) {
            console.log(...callerInfo,args);
            console.log(...args);
            // console.log(args);
        } else {
            // console.log(`[INFO] ${new Date().toISOString()} - ${...args}`);
        }
    }
}

const logger = new Logger();
// logger.info("Hello", "World", 42); // 测试打印多个值
// const logger = new Logger();
// 创建 Logger 实例并命名导出
export { logger };
