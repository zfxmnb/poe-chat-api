interface Response<T> {
  code: number;
  status: Boolean;
  data: T;
}
let errors: Record<string, any>[] = [];
let t: number | null | undefined = null;
export const request = {
  get: function <T = any>(url: string, params?: Record<string, any>) {
    let newUrl = url;
    if (params && Object.keys(params).length > 0) {
      newUrl = `${url}?${new URLSearchParams(params).toString()}`;
    }
    return fetch(newUrl, {
      method: 'GET'
    })
      .then((res) => res.json() as unknown as Response<T>)
      .then((res) => {
        if (res?.status) {
          return res.data;
        }
        errors.push({ [newUrl]: res.data ?? '接口错误' });
        t && clearTimeout(t);
        t = setTimeout(() => {
          errors.length && alert(JSON.stringify(errors, null, 2));
          errors = [];
        }, 3000);
        return Promise.reject(res);
      });
  },
  post: function post<T = any>(url: string, data?: Record<string, any>) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data ?? {})
    })
      .then((res) => res.json() as unknown as Response<T>)
      .then((res) => {
        if (res?.status) {
          return res.data;
        }
        errors.push({ [url]: res.data ?? '接口错误' });
        t = setTimeout(() => {
          errors.length && alert(JSON.stringify(errors, null, 2));
          errors = [];
        }, 3000);
        return Promise.reject(res);
      });
  }
};

export const postSignIn = (data: { username: string; password: string }) => {
  return request.post('/api/signin', data);
};

export const postTokens = (data: { b: string; lat: string }) => {
  return request.post('/api/tokens', data);
};

export interface Chat {
  bot: string;
  chatCode: string;
  chatId: string;
  id: string;
  title: string;
}

export const getChats = () => {
  return request.get<Chat[]>('/api/chats');
};

export const sendMessage = (data: { chatId: string; msg: string }) => {
  return request.post(`/api/chats/${data?.chatId}/send`, { msg: data?.msg });
};

export const createChat = (data: { bot: string; prompt: string }) => {
  return request.post(`/api/chats/create`, data);
};

export const deleteChat = (data: { bot: string; chatId: string }) => {
  return request.post(`/api/chats/delete`, data);
};

export interface Bot {
  nickname: string;
  displayName: string;
  isLimitedAccess: boolean;
  limitedAccessType: 'no_limit' | 'subscriber_access';
}
export const queryBots = (data?: { count?: number }) => {
  return request.get<Bot[]>(`/api/bots`, data);
};

export const updateinstance = () => {
  return request.post(`/api/instance`);
};
