import React from 'react';
import { 
  Users, 
  AlertTriangle, 
  Info, 
  CheckCircle2, 
  Clock, 
  UploadCloud, 
  Filter, 
  Plus, 
  TrendingUp,
  Activity,
  ChevronRight
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

interface DashboardViewProps {
  athletes: any[];
  recentSessions: any[];
  setActiveTab: (tab: string) => void;
  onSelectAthlete: (athlete: any) => void;
  searchQuery: string;
  stats?: any;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  athletes,
  recentSessions,
  setActiveTab,
  onSelectAthlete,
  searchQuery,
  stats
}) => {
  // Compute metrics strictly from real live data or stats
  const highRiskCount = stats?.high_risk ?? athletes.filter(a => a.risk_category?.toLowerCase().includes('high') || a.riskLevel === 'High Risk').length;
  const mediumRiskCount = stats?.medium_risk ?? athletes.filter(a => a.risk_category?.toLowerCase().includes('medium') || a.risk_category?.toLowerCase().includes('moderate') || a.riskLevel === 'Medium Risk').length;
  const lowRiskCount = stats?.low_risk ?? athletes.filter(a => a.risk_category?.toLowerCase().includes('low') || a.riskLevel === 'Low Risk').length;
  const totalCount = stats?.total_athletes ?? athletes.length;

  const displayTotal = totalCount;
  const displayHigh = highRiskCount;
  const displayMedium = mediumRiskCount;
  const displayLow = lowRiskCount;
  const pendingReviews = stats?.pending_requests ?? 0;
  const todayUploads = stats?.today_uploads ?? 0;

  const highRiskPct = displayTotal > 0 ? ((displayHigh / displayTotal) * 100).toFixed(1) : "0.0";
  const mediumRiskPct = displayTotal > 0 ? ((displayMedium / displayTotal) * 100).toFixed(1) : "0.0";
  const lowRiskPct = displayTotal > 0 ? ((displayLow / displayTotal) * 100).toFixed(1) : "0.0";

  // Donut dataset
  const pieData = displayTotal > 0 ? [
    { name: 'High Risk', value: displayHigh, color: '#ba1a1a' },
    { name: 'Medium Risk', value: displayMedium, color: '#e69c00' },
    { name: 'Low Risk', value: displayLow, color: '#198754' },
  ] : [
    { name: 'No Athletes', value: 1, color: '#e0e2e6' }
  ];

  // Filter recent sessions strictly from real activity feed
  const sessionsToDisplay = stats?.activity_feed && stats.activity_feed.length > 0
    ? stats.activity_feed.map((feed: any, idx: number) => ({
        id: `sess-live-${idx}`,
        athleteId: feed.athlete_id || `ath-live-${idx}`,
        athleteName: feed.athlete_name || 'Athlete',
        avatarUrl: feed.avatarUrl || '',
        movementType: feed.video_name || 'Kinematic Motion Scan',
        summary: feed.summary || 'Form assessment complete.',
        riskLevel: feed.risk_category || 'Low Risk',
        timestamp: 'Just now'
      }))
    : recentSessions;

  const filteredSessions = sessionsToDisplay.filter((s: any) => {
    const name = s.athleteName || s.athlete_name || '';
    const move = s.movementType || s.video_name || '';
    const sum = s.summary || '';
    const q = searchQuery.toLowerCase();
    return name.toLowerCase().includes(q) || move.toLowerCase().includes(q) || sum.toLowerCase().includes(q);
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-[#191c1f] tracking-tight">
            Dashboard Overview
          </h1>
          <p className="text-sm md:text-base text-[#424656] mt-1">
            Real-time biomechanics risk assessment.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setActiveTab('athletes')}
            className="px-4 py-2 border border-[#c3c6d8] bg-white rounded-lg text-xs font-semibold text-[#191c1f] hover:bg-[#f2f4f8] transition-colors flex items-center gap-2"
          >
            <Filter className="w-4 h-4 text-[#737687]" />
            Filter
          </button>
          <button 
            onClick={() => setActiveTab('upload_video')}
            className="px-4 py-2 bg-[#004ccd] text-white rounded-lg text-xs font-semibold hover:bg-[#003da9] transition-colors flex items-center gap-2 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            New Analysis
          </button>
        </div>
      </div>

      {/* Summary Metrics Bento Grid */}
      <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Athletes */}
        <div className="card-level-1 rounded-xl p-4 flex flex-col justify-between h-32 bg-white">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-semibold text-[#424656]">Total Athletes</h3>
            <Users className="w-5 h-5 text-[#004ccd]" />
          </div>
          <div>
            <p className="text-2xl font-bold text-[#191c1f]">
              {displayTotal.toLocaleString()}
            </p>
            <p className="text-xs font-medium text-[#424656] mt-1">
              {stats?.weekly_growth ? (
                <span className="text-[#0052dd] flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" /> +{stats.weekly_growth} this week
                </span>
              ) : (
                'Active roster'
              )}
            </p>
          </div>
        </div>

        {/* High Risk */}
        <div className="card-level-1 rounded-xl p-4 flex flex-col justify-between h-32 bg-white border-t-4 border-t-[#ba1a1a]">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-semibold text-[#424656]">High Risk</h3>
            <AlertTriangle className="w-5 h-5 text-[#ba1a1a]" />
          </div>
          <div>
            <p className="text-2xl font-bold text-[#ba1a1a]">
              {displayHigh}
            </p>
            <p className="text-xs font-medium text-[#424656] mt-1 truncate">
              Require immediate attention
            </p>
          </div>
        </div>

        {/* Medium Risk */}
        <div className="card-level-1 rounded-xl p-4 flex flex-col justify-between h-32 bg-white border-t-4 border-t-[#e69c00]">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-semibold text-[#424656]">Medium Risk</h3>
            <Info className="w-5 h-5 text-[#e69c00]" />
          </div>
          <div>
            <p className="text-2xl font-bold text-[#191c1f]">
              {displayMedium}
            </p>
            <p className="text-xs font-medium text-[#424656] mt-1 truncate">
              Monitor next session
            </p>
          </div>
        </div>

        {/* Low Risk */}
        <div className="card-level-1 rounded-xl p-4 flex flex-col justify-between h-32 bg-white border-t-4 border-t-[#198754]">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-semibold text-[#424656]">Low Risk</h3>
            <CheckCircle2 className="w-5 h-5 text-[#198754]" />
          </div>
          <div>
            <p className="text-2xl font-bold text-[#191c1f]">
              {displayLow.toLocaleString()}
            </p>
            <p className="text-xs font-medium text-[#424656] mt-1 truncate">
              Optimal condition
            </p>
          </div>
        </div>

        {/* Pending Reviews */}
        <div className="card-level-1 rounded-xl p-4 flex flex-col justify-between h-32 bg-white">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-semibold text-[#424656]">Pending Reviews</h3>
            <Clock className="w-5 h-5 text-[#585f66]" />
          </div>
          <div>
            <p className="text-2xl font-bold text-[#191c1f]">{pendingReviews}</p>
            <p className="text-xs font-medium text-[#424656] mt-1 truncate">
              Analyses processing
            </p>
          </div>
        </div>

        {/* Today's Uploads */}
        <div className="card-level-1 rounded-xl p-4 flex flex-col justify-between h-32 bg-white">
          <div className="flex justify-between items-start">
            <h3 className="text-xs font-semibold text-[#424656]">Today's Uploads</h3>
            <UploadCloud className="w-5 h-5 text-[#304db9]" />
          </div>
          <div>
            <p className="text-2xl font-bold text-[#191c1f]">{todayUploads}</p>
            <p className="text-xs font-medium text-[#424656] mt-1 truncate">
              Videos uploaded
            </p>
          </div>
        </div>
      </section>

      {/* Main Data Layout: Risk Distribution & Recent Activity */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Risk Distribution Card */}
        <div className="card-level-1 rounded-xl p-6 lg:col-span-1 flex flex-col items-center bg-white">
          <div className="w-full mb-4">
            <h2 className="text-lg font-bold text-[#191c1f]">Risk Distribution</h2>
            <p className="text-xs text-[#424656]">Current active roster status</p>
          </div>

          <div className="flex-1 flex flex-col items-center justify-center w-full min-h-[220px]">
            <div className="relative w-48 h-48 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(val: any) => [`${val} athletes`, 'Count']}
                  />
                </PieChart>
              </ResponsiveContainer>
              
              {/* Donut Center Display */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
                <span className="text-2xl font-extrabold text-[#191c1f]">
                  {highRiskPct}%
                </span>
                <span className="text-[11px] font-medium text-[#424656]">
                  High Risk Rate
                </span>
              </div>
            </div>

            {/* Legend Breakdown */}
            <div className="w-full space-y-2.5 mt-4 pt-4 border-t border-[#c3c6d8]">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#ba1a1a]"></span>
                  <span className="font-medium text-[#191c1f]">High Risk</span>
                </div>
                <span className="text-[#424656]">{displayHigh} ({highRiskPct}%)</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#e69c00]"></span>
                  <span className="font-medium text-[#191c1f]">Medium Risk</span>
                </div>
                <span className="text-[#424656]">{displayMedium} ({mediumRiskPct}%)</span>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-[#198754]"></span>
                  <span className="font-medium text-[#191c1f]">Low Risk</span>
                </div>
                <span className="text-[#424656]">{displayLow.toLocaleString()} ({lowRiskPct}%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity Feed */}
        <div className="card-level-1 rounded-xl p-6 lg:col-span-2 flex flex-col bg-white">
          <div className="w-full mb-4 flex justify-between items-end">
            <div>
              <h2 className="text-lg font-bold text-[#191c1f]">Recent Activity</h2>
              <p className="text-xs text-[#424656]">Latest biomechanics analyses</p>
            </div>
            <button 
              onClick={() => setActiveTab('athletes')}
              className="text-xs font-semibold text-[#004ccd] hover:underline flex items-center gap-1"
            >
              View All <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3.5 max-h-[420px] pr-1">
            {filteredSessions.map((session: any, idx: number) => {
              const matchedAthlete = athletes.find((a: any) => 
                a.id === session.athleteId || 
                a.full_name?.toLowerCase().includes((session.athleteName || '').toLowerCase()) ||
                a.firstName === (session.athleteName || '').split(' ')[0]
              );

              const isHigh = session.riskLevel === 'High Risk' || session.riskLevel?.toLowerCase().includes('high');
              const isMedium = session.riskLevel === 'Medium Risk' || session.riskLevel?.toLowerCase().includes('medium') || session.riskLevel?.toLowerCase().includes('moderate');

              return (
                <div
                  key={session.id || idx}
                  onClick={() => {
                    if (matchedAthlete) {
                      onSelectAthlete(matchedAthlete);
                    }
                  }}
                  className="p-4 rounded-lg border border-[#c3c6d8] hover:bg-[#f2f4f8] transition-colors flex items-center justify-between gap-4 cursor-pointer group"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="w-10 h-10 rounded-full bg-[#f2f4f8] border border-[#c3c6d8] overflow-hidden shrink-0 flex items-center justify-center">
                      {session.avatarUrl || matchedAthlete?.profile_picture_url ? (
                        <img 
                          src={session.avatarUrl || matchedAthlete?.profile_picture_url} 
                          alt={session.athleteName} 
                          className="w-full h-full object-cover" 
                        />
                      ) : (
                        <Activity className="w-5 h-5 text-[#004ccd]" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-[#191c1f] group-hover:text-[#004ccd] transition-colors truncate">
                        {session.athleteName}
                      </h4>
                      <p className="text-xs text-[#424656] truncate">
                        <span className="font-medium text-[#191c1f]">{session.movementType}</span> • {session.summary}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <span 
                      className={`px-2.5 py-0.5 rounded text-[11px] font-semibold ${
                        isHigh
                          ? 'bg-[#ffdad6] text-[#93000a]'
                          : isMedium
                          ? 'bg-[#ffe4c2] text-[#856404]'
                          : 'bg-[#c4f2c7] text-[#0f5132]'
                      }`}
                    >
                      {session.riskLevel}
                    </span>
                    <span className="text-[11px] text-[#424656]">
                      {session.timestamp || 'Just now'}
                    </span>
                  </div>
                </div>
              );
            })}

            {filteredSessions.length === 0 && (
              <div className="p-8 text-center text-[#737687] text-sm">
                No recent activity matching your search.
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};
