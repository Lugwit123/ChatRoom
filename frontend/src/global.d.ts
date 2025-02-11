// frontend/src/global.d.ts

export {}; // 确保这是一个模块

declare global {
    interface Window {
        setFormData: (data: Partial<FormDataType>) => void;
    }
}

// 定义 FormDataType，根据您的实际数据结构进行调整
interface FormDataType {
    username?: string;
    nickname?: string;
    password?: string;
    email?: string;
    age?: number;
}




declare global {
    interface PyWebViewAPI {
      copy_to_clipboard: (text: string) => Promise<boolean>;
    }
  
    interface Window {
      pywebview?: {
        api: PyWebViewAPI;
      };
    }
  }
