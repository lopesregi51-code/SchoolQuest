import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { StudentDashboard } from './pages/StudentDashboard';
import { UserProfile } from './pages/UserProfile';
import { ClanPage } from './pages/ClanPage';
import { ProfessorPanel } from './pages/ProfessorPanel';
import { ManagerPanel } from './pages/ManagerPanel';
import { AdminPanel } from './pages/AdminPanel';
import { MuralPage } from './pages/MuralPage';
import { ShopPage } from './pages/ShopPage';
import { AnalyticsDashboard } from './pages/AnalyticsDashboard';
import { BookOpen, Shield, Trophy } from 'lucide-react';

const HomePage = () => {
  return (
    <div className="min-h-screen bg-dark text-white flex flex-col items-center justify-center p-4">
      <header className="mb-12 text-center">
        <div className="flex items-center justify-center mb-4">
          <Shield className="w-16 h-16 text-primary mr-4" />
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Escolas Maranhão
          </h1>
        </div>
        <p className="text-xl text-gray-400">A Gamificação da sua Jornada Escolar</p>
      </header>

      <div className="grid md:grid-cols-3 gap-8 max-w-4xl w-full">
        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-primary transition-colors">
          <Trophy className="w-12 h-12 text-yellow-500 mb-4" />
          <h2 className="text-2xl font-bold mb-2">Conquiste XP</h2>
          <p className="text-gray-400">Complete missões, ganhe pontos e suba de nível na sua turma.</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-secondary transition-colors">
          <BookOpen className="w-12 h-12 text-blue-400 mb-4" />
          <h2 className="text-2xl font-bold mb-2">Missões Diárias</h2>
          <p className="text-gray-400">Tarefas exclusivas criadas pelos seus professores.</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-xl border border-gray-700 hover:border-success transition-colors">
          <Shield className="w-12 h-12 text-green-400 mb-4" />
          <h2 className="text-2xl font-bold mb-2">Sua Casa</h2>
          <p className="text-gray-400">Colabore com sua equipe e vença o campeonato escolar.</p>
        </div>
      </div>

      <a
        href="/login"
        className="mt-12 px-8 py-3 bg-primary hover:bg-blue-600 text-white font-bold rounded-full transition-all transform hover:scale-105 shadow-lg shadow-blue-500/30"
      >
        Entrar no Sistema
      </a>
    </div>
  );
};

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark flex items-center justify-center">
        <div className="text-white text-xl">Carregando...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.papel)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

const DashboardRouter: React.FC = () => {
  const { user } = useAuth();

  if (!user) return <Navigate to="/login" replace />;

  if (user.papel === 'admin') {
    return <AdminPanel />;
  }

  if (user.papel === 'gestor') {
    return <ManagerPanel />;
  }

  if (user.papel === 'professor') {
    return <ProfessorPanel />;
  }

  return <StudentDashboard />;
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardRouter />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile/:id"
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/clans"
            element={
              <ProtectedRoute>
                <ClanPage />
              </ProtectedRoute>
            }
          />
          <Route path="/mural" element={
            <ProtectedRoute allowedRoles={['aluno', 'professor', 'gestor', 'admin']}>
              <MuralPage />
            </ProtectedRoute>
          } />
          <Route path="/shop" element={
            <ProtectedRoute allowedRoles={['aluno']}>
              <ShopPage />
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute allowedRoles={['gestor', 'admin']}>
              <AnalyticsDashboard />
            </ProtectedRoute>
          } />
          <Route path="/professor" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
