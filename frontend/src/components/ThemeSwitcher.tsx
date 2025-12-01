import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { Palette, X } from 'lucide-react';

export const ThemeSwitcher: React.FC = () => {
    const { theme, setTheme } = useTheme();
    const [isOpen, setIsOpen] = useState(false);

    const themes = [
        { id: 'default', name: 'Azul (Padrão)', color: '#2B6CB0' },
        { id: 'purple', name: 'Roxo', color: '#9333EA' },
        { id: 'green', name: 'Verde', color: '#16A34A' },
        { id: 'orange', name: 'Laranja', color: '#EA580C' },
        { id: 'pink', name: 'Rosa', color: '#DB2777' },
    ] as const;

    return (
        <div className="fixed bottom-6 right-6 z-50">
            {isOpen && (
                <div className="absolute bottom-16 right-0 bg-gray-800 border border-gray-700 rounded-xl p-4 shadow-xl w-64 mb-2 animate-fade-in">
                    <div className="flex justify-between items-center mb-3">
                        <h3 className="text-white font-bold">Escolha um Tema</h3>
                        <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white">
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                    <div className="grid grid-cols-5 gap-2">
                        {themes.map((t) => (
                            <button
                                key={t.id}
                                onClick={() => setTheme(t.id)}
                                className={`w-8 h-8 rounded-full border-2 transition-transform hover:scale-110 ${theme === t.id ? 'border-white scale-110' : 'border-transparent'
                                    }`}
                                style={{ backgroundColor: t.color }}
                                title={t.name}
                            />
                        ))}
                    </div>
                </div>
            )}

            <button
                onClick={() => setIsOpen(!isOpen)}
                className="bg-primary hover:bg-blue-600 text-white p-4 rounded-full shadow-lg transition-all transform hover:scale-110"
                title="Mudar Tema"
            >
                <Palette className="w-6 h-6" />
            </button>
        </div>
    );
};
