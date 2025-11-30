import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import {
    LineChart, Line, PieChart, Pie,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import apiClient from '../api/client';
import { TrendingUp, Users, Target, Award, Download, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import jsPDF from 'jspdf';
import * as XLSX from 'xlsx';

export const AnalyticsDashboard: React.FC = () => {
    const [overview, setOverview] = useState<any>(null);
    const [timeline, setTimeline] = useState<any[]>([]);
    const [categories, setCategories] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const { user } = useAuth();
    const [schools, setSchools] = useState<any[]>([]);
    const [selectedSchool, setSelectedSchool] = useState<string>('');
    const navigate = useNavigate();

    useEffect(() => {
        if (user?.papel === 'admin') {
            apiClient.get('/escolas/').then(res => setSchools(res.data)).catch(console.error);
        }
    }, [user]);

    useEffect(() => {
        fetchAnalytics();
    }, [selectedSchool]);

    const fetchAnalytics = async () => {
        try {
            const params = selectedSchool ? `escola_id=${selectedSchool}` : '';
            const query = params ? `?${params}` : '';
            const timelineQuery = params ? `?${params}&days=30` : '?days=30';

            const [overviewRes, timelineRes, categoriesRes] = await Promise.all([
                apiClient.get(`/analytics/school/overview${query}`),
                apiClient.get(`/analytics/school/activity-timeline${timelineQuery}`),
                apiClient.get(`/analytics/school/category-distribution${query}`)
            ]);

            console.log('Overview:', overviewRes.data);
            console.log('Timeline:', timelineRes.data);
            console.log('Categories:', categoriesRes.data);

            setOverview(overviewRes.data);
            setTimeline(timelineRes.data);
            setCategories(categoriesRes.data);
        } catch (error) {
            console.error('Erro ao carregar analytics:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const exportPDF = () => {
        const doc = new jsPDF();
        doc.setFontSize(20);
        doc.text('Relatório de Desempenho - SchoolQuest', 20, 20);

        doc.setFontSize(12);
        doc.text(`Data: ${new Date().toLocaleDateString()}`, 20, 30);

        if (overview) {
            doc.text('Resumo Geral:', 20, 45);
            doc.text(`Total de Alunos: ${overview.total_students}`, 30, 55);
            doc.text(`Total de Missões: ${overview.total_missions}`, 30, 65);
            doc.text(`Missões (Mês Atual): ${overview.missions_this_month}`, 30, 75);
            doc.text(`Média de XP: ${overview.avg_xp}`, 30, 85);
        }

        doc.save('relatorio-schoolquest.pdf');
    };

    const exportExcel = () => {
        const wb = XLSX.utils.book_new();

        // Overview Sheet
        if (overview) {
            const overviewData = [
                ['Métrica', 'Valor'],
                ['Total de Alunos', overview.total_students],
                ['Total de Missões', overview.total_missions],
                ['Missões (Mês Atual)', overview.missions_this_month],
                ['Média de XP', overview.avg_xp]
            ];
            const wsOverview = XLSX.utils.aoa_to_sheet(overviewData);
            XLSX.utils.book_append_sheet(wb, wsOverview, "Visão Geral");
        }

        // Timeline Sheet
        if (timeline.length > 0) {
            const wsTimeline = XLSX.utils.json_to_sheet(timeline);
            XLSX.utils.book_append_sheet(wb, wsTimeline, "Atividade Diária");
        }

        // Top Students Sheet
        if (overview && overview.top_students) {
            const wsStudents = XLSX.utils.json_to_sheet(overview.top_students);
            XLSX.utils.book_append_sheet(wb, wsStudents, "Top Alunos");
        }

        XLSX.writeFile(wb, 'relatorio-schoolquest.xlsx');
    };

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

    if (isLoading) return <div className="p-8 text-center text-white">Carregando dados...</div>;
    if (!overview) return <div className="p-8 text-center text-white">Erro ao carregar dados.</div>;

    return (
        <div className="min-h-screen bg-dark text-white p-6">
            <div className="max-w-7xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate(-1)}
                            className="p-2 hover:bg-gray-800 rounded-full transition-colors"
                        >
                            <ArrowLeft className="w-6 h-6" />
                        </button>
                        <h1 className="text-4xl font-bold">📊 Analytics Dashboard</h1>
                    </div>

                    {user?.papel === 'admin' && (
                        <div className="flex items-center gap-2">
                            <label htmlFor="school-select" className="text-gray-400">Filtrar por Escola:</label>
                            <select
                                id="school-select"
                                name="school-select"
                                value={selectedSchool}
                                onChange={(e) => setSelectedSchool(e.target.value)}
                                className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="">Todas as Escolas</option>
                                {schools.map((school) => (
                                    <option key={school.id} value={school.id}>
                                        {school.nome}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    <div className="flex gap-3">
                        <button
                            onClick={exportPDF}
                            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition-colors"
                        >
                            <Download className="w-4 h-4" /> PDF
                        </button>
                        <button
                            onClick={exportExcel}
                            className="flex items-center gap-2 bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg transition-colors"
                        >
                            <Download className="w-4 h-4" /> Excel
                        </button>
                    </div>
                </div>

                {/* KPIs */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">Total de Alunos</p>
                                <p className="text-3xl font-bold">{overview.total_students}</p>
                            </div>
                            <Users className="w-10 h-10 text-blue-500" />
                        </div>
                    </div>

                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">Total de Missões</p>
                                <p className="text-3xl font-bold">{overview.total_missions}</p>
                            </div>
                            <Target className="w-10 h-10 text-green-500" />
                        </div>
                    </div>

                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">Missões (Mês)</p>
                                <p className="text-3xl font-bold">{overview.missions_this_month}</p>
                            </div>
                            <TrendingUp className="w-10 h-10 text-yellow-500" />
                        </div>
                    </div>

                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-gray-400 text-sm">Média de XP</p>
                                <p className="text-3xl font-bold">{overview.avg_xp}</p>
                            </div>
                            <Award className="w-10 h-10 text-purple-500" />
                        </div>
                    </div>
                </div>

                {/* Charts Row 1 */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    {/* Activity Timeline */}
                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                        <h3 className="text-xl font-bold mb-6">Atividade Diária (30 dias)</h3>
                        <div className="h-80 w-full">
                            {timeline && timeline.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                                    <LineChart data={timeline}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                        <XAxis dataKey="date" stroke="#9CA3AF" />
                                        <YAxis stroke="#9CA3AF" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                                            itemStyle={{ color: '#fff' }}
                                        />
                                        <Line type="monotone" dataKey="missions" stroke="#8884d8" strokeWidth={2} dot={false} />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full text-gray-500">
                                    Sem dados de atividade
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Category Distribution */}
                    <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                        <h3 className="text-xl font-bold mb-6">Distribuição por Categoria</h3>
                        <div className="h-80 w-full">
                            {categories && categories.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                                    <PieChart>
                                        <Pie
                                            data={categories}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            outerRadius={100}
                                            fill="#8884d8"
                                            dataKey="count"
                                            nameKey="categoria"
                                            label={({ name, percent }: { name?: string | number; percent?: number }) => `${name ?? ''} ${((percent || 0) * 100).toFixed(0)}%`}
                                        >
                                            {categories.map((_, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px' }}
                                            itemStyle={{ color: '#fff' }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full text-gray-500">
                                    Sem dados de categorias
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Top Students Table */}
                <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
                    <h3 className="text-xl font-bold mb-6">Top 10 Alunos (XP)</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-gray-700">
                                    <th className="pb-3 text-gray-400 font-medium">Posição</th>
                                    <th className="pb-3 text-gray-400 font-medium">Nome</th>
                                    <th className="pb-3 text-gray-400 font-medium">Nível</th>
                                    <th className="pb-3 text-gray-400 font-medium text-right">XP Total</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-700">
                                {overview?.top_students?.map((student: any, index: number) => (
                                    <tr key={index} className="hover:bg-gray-700/50">
                                        <td className="py-4">
                                            {index < 3 ? (
                                                <span className={`
                          inline-flex items-center justify-center w-8 h-8 rounded-full font-bold
                          ${index === 0 ? 'bg-yellow-500/20 text-yellow-500' : ''}
                          ${index === 1 ? 'bg-gray-400/20 text-gray-400' : ''}
                          ${index === 2 ? 'bg-orange-500/20 text-orange-500' : ''}
                        `}>
                                                    {index + 1}
                                                </span>
                                            ) : (
                                                <span className="pl-3 text-gray-500">#{index + 1}</span>
                                            )}
                                        </td>
                                        <td className="py-4 font-medium">{student.nome}</td>
                                        <td className="py-4 text-gray-400">Nível {student.nivel}</td>
                                        <td className="py-4 text-right font-bold text-blue-400">{student.xp.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};
