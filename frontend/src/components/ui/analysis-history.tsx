import React, { useState, useEffect } from 'react';
import { Loader2, Activity, Calendar, ExternalLink, TrendingUp, Trash2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface AnalysisHistoryProps {
    token: string;
    onOpenSession: (sessionId: string) => void;
}

export const AnalysisHistory = ({ token, onOpenSession }: AnalysisHistoryProps) => {
    const [sessions, setSessions] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/sessions/history`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('Failed to fetch history');
                const data = await res.json();
                setSessions(data);
            } catch (err: any) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchHistory();
    }, [token]);

    const handleDelete = async (sessionId: string) => {
        if (!confirm("Are you sure you want to delete this session? This action cannot be undone.")) return;
        
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to delete session');
            }
            // Remove from local state
            setSessions(prev => prev.filter(s => s.session_id !== sessionId));
        } catch (err: any) {
            alert(err.message);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full min-h-[400px]">
                <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center p-8 bg-rose-500/10 border border-rose-500/20 rounded-2xl">
                <p className="text-rose-400">{error}</p>
            </div>
        );
    }

    if (sessions.length === 0) {
        return (
            <div className="text-center p-12 bg-slate-900/50 rounded-2xl border border-slate-800 backdrop-blur-xl max-w-2xl mx-auto w-full mt-12">
                <Activity className="w-16 h-16 text-slate-700 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">No Analysis History</h2>
                <p className="text-slate-400">Upload and analyze a video on the Dashboard to see your history here.</p>
            </div>
        );
    }

    const getTrendData = () => {
        return [...sessions]
            .sort((a, b) => new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime())
            .map((s, i, arr) => {
                const score = s.risk_data?.overall_health_score ?? 100;
                const efficiency = s.risk_data?.biomechanical_efficiency_score ?? score;
                const valgus = s.risk_data?.valgus_angle ?? 0;
                const prevScore = i > 0 ? (arr[i - 1].risk_data?.overall_health_score ?? 100) : score;
                const diff = score - prevScore;
                const diffLabel = i === 0 ? 'Baseline' : diff > 0 ? `+${diff} pts` : diff < 0 ? `${diff} pts` : 'No change';
                return {
                    name: `S${i + 1}`,
                    date: s.created_at ? new Date(s.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : `S${i + 1}`,
                    video: s.video_name || `Session ${i + 1}`,
                    score: score,
                    efficiency: efficiency,
                    valgus: Number(valgus.toFixed(1)),
                    diff: diff,
                    diffLabel: diffLabel
                };
            });
    };

    const chartData = getTrendData();
    const latestDiff = chartData[chartData.length - 1]?.diff ?? 0;
    const latestDiffLabel = chartData[chartData.length - 1]?.diffLabel ?? 'Baseline';

    return (
        <div className="max-w-6xl mx-auto w-full space-y-6">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight mb-2 flex items-center gap-3">
                    <Activity className="w-8 h-8 text-cyan-400" />
                    Analysis History & Progress
                </h1>
                <p className="text-slate-400">View chronological session analytics and progress from previous assessments.</p>
            </div>

            {sessions.length > 0 && (
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-xl mb-8 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
                        <div className="flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-cyan-400" />
                            <h2 className="text-xl font-bold text-white">Session-over-Session Progress Analytics</h2>
                        </div>
                        {chartData.length > 1 && (
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-slate-400">Latest vs Prev Session:</span>
                                <span className={`px-2.5 py-1 rounded-full text-xs font-extrabold ${
                                    latestDiff > 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                                    latestDiff < 0 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                                    'bg-slate-800 text-slate-300 border border-slate-700'
                                }`}>
                                    {latestDiffLabel}
                                </span>
                            </div>
                        )}
                    </div>
                    <div className="h-72 w-full pt-2">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} fontStyle="bold" />
                                <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={12} />
                                <Tooltip 
                                    content={({ active, payload }: any) => {
                                        if (active && payload && payload.length) {
                                            const data = payload[0].payload;
                                            return (
                                                <div className="bg-slate-900 text-white p-3 rounded-xl shadow-xl border border-slate-700 text-xs space-y-1.5 min-w-[190px]">
                                                    <p className="font-bold text-cyan-400 border-b border-slate-700 pb-1">{data.video} ({data.date})</p>
                                                    <p className="flex justify-between font-semibold"><span className="text-slate-400">Health Score:</span> <strong className="text-cyan-300">{data.score}/100</strong></p>
                                                    <p className="flex justify-between font-semibold"><span className="text-slate-400">Efficiency:</span> <strong className="text-emerald-400">{data.efficiency}/100</strong></p>
                                                    <p className="flex justify-between font-semibold"><span className="text-slate-400">Valgus Angle:</span> <strong className="text-amber-400">{data.valgus}°</strong></p>
                                                    <div className="pt-1 border-t border-slate-700 flex justify-between items-center font-bold">
                                                        <span className="text-slate-400">vs Prev Session:</span>
                                                        <span className={data.diff > 0 ? 'text-emerald-400' : data.diff < 0 ? 'text-rose-400' : 'text-slate-400'}>
                                                            {data.diffLabel}
                                                        </span>
                                                    </div>
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                                <Legend wrapperStyle={{ fontSize: '12px', fontWeight: 600, paddingTop: '10px' }} />
                                <Line name="Health Score" type="monotone" dataKey="score" stroke="#06b6d4" strokeWidth={3} dot={{ fill: '#06b6d4', strokeWidth: 2, r: 5 }} activeDot={{ r: 8 }} />
                                <Line name="Efficiency" type="monotone" dataKey="efficiency" stroke="#10b981" strokeWidth={2.5} strokeDasharray="4 4" dot={{ fill: '#10b981', r: 4 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sessions.map((session) => (
                    <div key={session.session_id} className="bg-slate-900/50 border border-slate-800 hover:border-slate-700 transition-colors rounded-2xl p-6 backdrop-blur-xl flex flex-col h-full">
                        <div className="flex justify-between items-start mb-4">
                            <div>
                                <h3 className="font-bold text-white text-lg line-clamp-1">{session.video_name || "Unknown Video"}</h3>
                                <div className="flex items-center gap-2 text-slate-400 text-sm mt-1">
                                    <Calendar className="w-4 h-4" />
                                    <span>{new Date(session.created_at).toLocaleString()}</span>
                                </div>
                            </div>
                            <div className={`px-3 py-1 rounded-full text-xs font-bold border ${
                                session.risk_data?.risk_category === 'Low Risk' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                                session.risk_data?.risk_category === 'Moderate Risk' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                'bg-rose-500/10 text-rose-400 border-rose-500/20'
                            }`}>
                                {session.risk_data?.risk_category || "Unknown"}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mb-6 mt-2">
                            <div className="bg-slate-950 rounded-xl p-3 border border-slate-800">
                                <p className="text-xs text-slate-500 mb-1">Health Score</p>
                                <p className="text-xl font-bold text-white">{session.risk_data?.overall_health_score || 0}/100</p>
                            </div>
                            <div className="bg-slate-950 rounded-xl p-3 border border-slate-800">
                                <p className="text-xs text-slate-500 mb-1">Efficiency</p>
                                <p className="text-xl font-bold text-white">{session.risk_data?.biomechanical_efficiency_score || 0}/100</p>
                            </div>
                        </div>

                        <div className="mt-auto pt-4 border-t border-slate-800 flex gap-2">
                            <button
                                onClick={() => onOpenSession(session.session_id)}
                                className="flex-1 flex items-center justify-center gap-2 py-3 bg-slate-800 hover:bg-slate-700 text-white font-medium rounded-xl transition-all"
                            >
                                <ExternalLink className="w-4 h-4" /> Open in Dashboard
                            </button>
                            <button
                                onClick={() => handleDelete(session.session_id)}
                                className="px-4 flex items-center justify-center bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 rounded-xl transition-all border border-rose-500/20 hover:border-rose-500/40"
                                title="Delete Session"
                            >
                                <Trash2 className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};
