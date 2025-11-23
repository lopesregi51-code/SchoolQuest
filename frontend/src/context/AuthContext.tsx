import React, { createContext, useState, useContext, useEffect, type ReactNode } from 'react';
import apiClient from '../api/client';

interface User {
    id: number;
    email: string;
    nome: string;
    papel: string;
    pontos: number;
    moedas: number;
    xp: number;
    nivel: number;
    serie?: string;
    escola_id?: number;
    escola_nome?: string;
    bio?: string;
    interesses?: string;
    streak_count?: number;
    avatar_url?: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        if (token) {
            fetchUserData();
        } else {
            setIsLoading(false);
        }
    }, [token]);

    const fetchUserData = async () => {
        setIsLoading(true);
        try {
            const response = await apiClient.get('/users/me');
            setUser(response.data);
            // Save user data to localStorage for role-based routing
            localStorage.setItem('user', JSON.stringify(response.data));
        } catch (error) {
            console.error('Failed to fetch user data:', error);
            logout();
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email: string, password: string) => {
        try {
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await apiClient.post('/auth/token', formData, {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            });

            const { access_token } = response.data;

            localStorage.setItem('token', access_token);
            setToken(access_token);
        } catch (error) {
            throw new Error('Login failed. Please check your credentials.');
        }
    };

    const logout = () => {
        localStorage.removeItem('token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
