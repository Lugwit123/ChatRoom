// frontend/src/types/wangeditor.d.ts

import '@wangeditor/editor';

declare module '@wangeditor/editor' {
    interface IDomEditor {
        cmd: {
            do: (cmdName: string, value: any) => void;
        };
    }
}
