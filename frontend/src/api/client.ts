import axios, { type AxiosInstance, type AxiosError } from 'axios';
import { API_BASE_URL } from '../config/api';

/**
 * Axios instance configurado com interceptors
 * - Adiciona automaticamente o token JWT em todas as requisições
 * - Trata erros globalmente
 * - Faz logout automático em caso de 401
 */

const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 120 seconds to handle Render cold starts
});

// Request interceptor - adiciona token automaticamente
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - trata erros globalmente
apiClient.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
        // Logout automático em caso de 401
        // Logout automático em caso de 401, exceto no login
        if (error.response?.status === 401 && !error.config?.url?.includes('/auth/token')) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            window.location.href = '/';
        }

        // Log de erros para debug
        console.error('API Error:', {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            data: error.response?.data
        });

        return Promise.reject(error);
    }
);

export default apiClient;
