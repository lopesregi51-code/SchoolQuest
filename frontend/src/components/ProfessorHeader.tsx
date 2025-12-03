import React from 'react';
import { Link } from 'react-router-dom';
import { LogOut, MessageSquare, ShoppingBag } from 'lucide-react';
import { ThemeSwitcher } from './ThemeSwitcher';

interface ProfessorHeaderProps {
    schoolName?: string;
    onLogout: () => void;
}

export const ProfessorHeader: React.FC<ProfessorHeaderProps> = ({ schoolName, onLogout }) => {
    return (
        <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h1 className="text-3xl font-bold">Painel do Professor</h1>
                <p className="text-gray-400">
                    Gerencie missões e alunos{schoolName ? ` • ${schoolName}` : ''}
                </p>
            </div>
            <div className="flex items-center gap-3">
                <ThemeSwitcher />
                <Link
                    to="/mural"
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
                >
                    <MessageSquare className="w-4 h-4" />
                    Mural
                </Link>
                <Link
                    to="/professor/shop"
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors"
                >
                    <ShoppingBag className="w-4 h-4" />
                    Lojinha
                </Link>
                <button
                    onClick={onLogout}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                    <LogOut className="w-4 h-4" />
                    Sair
                </button>
            </div>
        </header>
    );
};
