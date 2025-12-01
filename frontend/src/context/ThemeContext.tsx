import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'default' | 'purple' | 'green' | 'orange' | 'pink';

interface ThemeContextType {
    theme: Theme;
    setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [theme, setTheme] = useState<Theme>(() => {
        const savedTheme = localStorage.getItem('schoolquest_theme');
        return (savedTheme as Theme) || 'default';
    });

    useEffect(() => {
        const root = window.document.documentElement;

        // Remove old theme classes
        root.classList.remove('theme-purple', 'theme-green', 'theme-orange', 'theme-pink');

        // Add new theme class if not default
        if (theme !== 'default') {
            root.classList.add(`theme-${theme}`);
        }

        localStorage.setItem('schoolquest_theme', theme);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};
