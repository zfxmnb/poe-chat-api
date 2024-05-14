/// <reference types="vite/client" />

interface Window extends Record<string, any> {
  __INIT__: { currentPage: 'Home' | 'Signin' | 'Admin'; tokens?: { b: string; lat: string }; role?: 'admin' | 'user' } & Record<string, any>;
}
