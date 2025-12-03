import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Mail, Lock, AlertCircle } from 'lucide-react';

export const Login: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();



    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err: any) {
            console.error("Login error:", err);

            let errorMessage = 'Erro desconhecido';
            let technicalDetails = '';

            if (err.response) {
                // O servidor respondeu com um status de erro
                if (err.response.status === 401) {
                    errorMessage = 'Email ou senha incorretos';
                } else {
                    errorMessage = `Erro no servidor: ${err.response.status}`;
                }
                technicalDetails = `Status: ${err.response.status}\nURL: ${err.config?.url}\nBaseURL: ${err.config?.baseURL}`;
            } else if (err.request) {
                // A requisição foi feita mas não houve resposta
                errorMessage = 'Erro de conexão. O servidor não respondeu.';
                technicalDetails = `Sem resposta do servidor.\nURL Tentada: ${err.config?.baseURL}${err.config?.url}\nErro: ${err.message}`;
            } else {
                // Algo aconteceu na configuração da requisição
                errorMessage = 'Erro ao configurar a requisição.';
                technicalDetails = `Erro: ${err.message}`;
            }

            setError(errorMessage);
            // Salvar detalhes técnicos no estado para exibir se necessário (opcional, aqui vou logar ou mostrar num tooltip/expandable)
            console.log('Detalhes técnicos:', technicalDetails);

            // Hack rápido para mostrar detalhes na tela de erro para debug
            setError(`${errorMessage} \n\n[DEBUG INFO]\n${technicalDetails}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-dark flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="bg-gray-800 rounded-2xl shadow-2xl p-8 border border-gray-700">
                    <div className="flex items-center justify-center mb-8">
                        <Shield className="w-12 h-12 text-primary mr-3" />
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                            Escolas Maranhão
                        </h1>
                    </div>

                    <h2 className="text-2xl font-bold text-white mb-6 text-center">
                        Entre na Aventura
                    </h2>

                    {error && (
                        <div className="mb-4 p-3 bg-red-900/30 border border-red-500 rounded-lg flex items-center">
                            <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                            <span className="text-red-200 text-sm whitespace-pre-wrap">{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-gray-300 text-sm font-medium mb-2">
                                Email
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                    placeholder="seu@email.com"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-gray-300 text-sm font-medium mb-2">
                                Senha
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3 bg-primary hover:bg-blue-600 text-white font-bold rounded-lg transition-all transform hover:scale-105 shadow-lg shadow-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                        >
                            {isLoading ? 'Entrando...' : 'Entrar'}
                        </button>
                    </form>


                </div>
            </div>
        </div>
    );
};
