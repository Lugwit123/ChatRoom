export  const is_developenv = true;

export const isLocalEnv = navigator.userAgent.includes("Qt")

export const executeByEnv = <T,>(
  ) => {
    const isLocalEnv =navigator.userAgent.includes("Qt")
    if (isLocalEnv) {
        (window as any).pyObj.pythonFunction("Hello from JavaScript!");
    } else {
        alert("网络环境");
    }

  };




export const exit_app = <T,>(
    ) => {
    const isLocalEnv =navigator.userAgent.includes("Qt")
    if (isLocalEnv) {
        (window as any).pyObj.exit_app("Hello from JavaScript!");
    } else {
        alert("网络环境");
    }

};

export const localHandlenewMessage = async (message: string) => {
    const pyObj = (window as any).pyObj
    return new Promise<string>((resolve, reject) => {
        try {
            if (typeof pyObj.handleNewMessage !== "undefined"){
                const handler = async (result: string) => {
                    console.log("收到Python返回的结果:", result);
                    pyObj.notificationComplete.disconnect(handler);
                    resolve(result);
                };
                // 先连接信号
                pyObj.notificationComplete.connect(handler);
                console.log("处理通知:", message,typeof message);
                // 然后发送通知
                
                pyObj.handleNewMessage(message).then(() => {
                    console.log("通知已发送",message);
                }).catch((error: any) => {
                    console.error("发送通知失败:", error);
                    reject(error);
                });
            }
            
        } catch (error) {
            console.error("处理通知时出错:", error);
            reject(error);
        }
    });
};

export const get_sid = async () => {
    return new Promise<string>((resolve, reject) => {
        try {
            const handler = async (result: string) => {
                console.log("收到Python返回的结果:", result);
                (window as any).pyObj.notificationComplete.disconnect(handler);
                resolve(result);
            };
            
            (window as any).pyObj.notificationComplete.connect(handler);
            (window as any).pyObj.sendNotification("Hello from JavaScript!").catch((error: any) => {
                reject(error);
            });
        } catch (error) {
            reject(error);
        }
    });
};