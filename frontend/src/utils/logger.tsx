class Logger {
    private originalLog: (...args: any[]) => void;
    private useConsoleLog: boolean;  // 新增的条件判断标志

    constructor(useConsoleLog: boolean = false) {
        this.originalLog = console.log;
        this.useConsoleLog = useConsoleLog;  // 默认值为 false
    }

    info(...args: any[]) {
        const timestamp = new Date().toLocaleString();
        if (this.useConsoleLog) {
            console.log(`[INFO] [${timestamp}]`, ...args);  // 临时使用 console.log
        } else {
            console.trace(`[INFO] [${timestamp}] Trace Information`, ...args);
            this.originalLog(`[INFO] [${timestamp}]`, ...args); // 使用原本的 logger 处理
        }
    }

    warn(...args: any[]) {
        const timestamp = new Date().toLocaleString();
        console.trace(`[WARN] [${timestamp}] Trace Information`, ...args);
        this.originalLog(`[WARN] [${timestamp}]`, ...args);
    }

    error(...args: any[]) {
        const timestamp = new Date().toLocaleString();
        console.trace(`[ERROR] [${timestamp}] Trace Information`, ...args);
        this.originalLog(`[ERROR] [${timestamp}]`, ...args);
    }
}


// 创建 Logger 实例并导出
const logger = new Logger(true);
logger.info=console.log
export { logger };
