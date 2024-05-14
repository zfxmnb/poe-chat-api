/// <reference types="vite/client" />

interface Window extends Record<string, any> {
  __INIT__: { currentPage: 'Home' | 'Signin' | 'Admin' } & Record<string, any>;
}
