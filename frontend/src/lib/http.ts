import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('campuswap_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[api] request failed', error);
    throw error;
  }
);

export default api;
