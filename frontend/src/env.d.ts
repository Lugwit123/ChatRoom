/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_PORT: string
  readonly VITE_DISABLE_HOST_CHECK: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
