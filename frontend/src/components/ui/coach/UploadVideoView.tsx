import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  Play, 
  Lightbulb, 
  Focus, 
  Ruler, 
  CheckCircle2, 
  X, 
  Activity,
  Cpu,
  Loader2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useUpload } from '@/context/UploadContext';

interface UploadVideoViewProps {
  athletes: any[];
  token: string;
  onAddSession?: (session: any) => void;
  setActiveTab: (tab: string) => void;
}

export const UploadVideoView: React.FC<UploadVideoViewProps> = ({
  athletes,
  token,
  onAddSession,
  setActiveTab
}) => {
  const [selectedAthleteId, setSelectedAthleteId] = useState('');
  const [videoLabel, setVideoLabel] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [analysisDone, setAnalysisDone] = useState(false);

  const { startUpload, isUploading: isAnalyzing, progress: uploadProgress } = useUpload();

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file: File) => {
    setSelectedFile(file);
    if (!videoLabel) {
      const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
      setVideoLabel(`${nameWithoutExt} - Biomechanics Scan`);
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedAthleteId) {
      toast.error("Please select a target athlete.");
      return;
    }
    if (!selectedFile && !videoLabel) {
      toast.error("Please select or upload a video file.");
      return;
    }

    await startUpload(selectedFile!, videoLabel, token, selectedAthleteId, (data) => {
        setAnalysisDone(true);
        // Optional: you could call onAddSession here if you want it to appear immediately in dashboard without refresh
        // For now, it will be fetched when they go to dashboard
    });
  };

  return (
    <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl md:text-3xl font-extrabold text-[#191c1f]">
          Upload Biomechanics Video
        </h2>
        <p className="text-sm md:text-base text-[#424656] mt-1">
          Securely upload athlete footage for AI-driven risk assessment and kinematic analysis.
        </p>
      </div>

      {/* Removed errorMsg because UploadContext handles errors globally now */}

      {/* Upload Card */}
      <div className="bg-white rounded-xl shadow-xs border border-[#c3c6d8] p-6 md:p-8 space-y-6">
        <form onSubmit={(e) => e.preventDefault()} className="space-y-6">
          {/* Top Form Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Target Athlete Select */}
            <div className="space-y-1.5">
              <label htmlFor="athlete-select" className="block text-xs font-bold text-[#191c1f] uppercase tracking-wider">
                Target Athlete *
              </label>
              <select
                id="athlete-select"
                value={selectedAthleteId}
                onChange={(e) => setSelectedAthleteId(e.target.value)}
                className="w-full bg-white border border-[#c3c6d8] rounded-lg px-4 py-3 text-sm text-[#191c1f] focus:outline-none focus:border-[#004ccd] focus:ring-1 focus:ring-[#004ccd]"
              >
                <option value="">Select an athlete...</option>
                {athletes.map((ath) => (
                  <option key={ath.id} value={ath.id}>
                    {ath.full_name || `${ath.firstName || ''} ${ath.lastName || ''}`} ({ath.sport || ath.profile?.sport || 'General'} • {ath.position || 'Athlete'})
                  </option>
                ))}
              </select>
            </div>

            {/* Video Label */}
            <div className="space-y-1.5">
              <label htmlFor="video-label" className="block text-xs font-bold text-[#191c1f] uppercase tracking-wider">
                Video Label / Session Name
              </label>
              <input
                id="video-label"
                type="text"
                value={videoLabel}
                onChange={(e) => setVideoLabel(e.target.value)}
                placeholder="e.g., Sprint Start Form Check - Oct 12"
                className="w-full bg-white border border-[#c3c6d8] rounded-lg px-4 py-3 text-sm text-[#191c1f] focus:outline-none focus:border-[#004ccd] focus:ring-1 focus:ring-[#004ccd] placeholder-[#737687]"
              />
            </div>
          </div>

          {/* Dashed Drag and Drop Area */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-[#191c1f] uppercase tracking-wider">
              Media File
            </label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 md:p-12 flex flex-col items-center justify-center cursor-pointer transition-all ${
                isDragging
                  ? 'border-[#004ccd] bg-[#004ccd]/5 scale-[1.01]'
                  : 'border-[#c3c6d8] bg-[#f7f9fd] hover:bg-[#f2f4f8] hover:border-[#004ccd]/50'
              }`}
            >
              <div className="w-16 h-16 rounded-full bg-[#f3f3ff] text-[#004ccd] flex items-center justify-center mb-4 transition-transform group-hover:scale-110">
                <UploadCloud className="w-8 h-8" />
              </div>

              <h3 className="text-base font-bold text-[#191c1f] mb-1">
                Drag and drop video here
              </h3>
              <p className="text-xs text-[#424656] mb-6 text-center max-w-md leading-relaxed">
                Supported formats: .MP4, .MOV (Max 500MB). For best analysis results, ensure 60fps minimum and clear, unobstructed views of major joints.
              </p>

              <button
                type="button"
                className="px-6 py-2.5 rounded-lg border border-[#004ccd] text-[#004ccd] font-semibold text-xs uppercase tracking-wider hover:bg-[#004ccd]/5 transition-colors"
              >
                Browse Files
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/quicktime,video/*"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            {/* Selected File & Upload Progress */}
            {selectedFile && uploadProgress !== null && (
              <div className="mt-4 p-4 rounded-lg border border-[#c3c6d8] bg-white flex items-center gap-4">
                <Play className="w-8 h-8 text-[#004ccd] shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-[#191c1f] truncate">{selectedFile.name}</span>
                    <span className="text-[#424656]">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-[#e0e2e6] rounded-full h-1.5 overflow-hidden">
                    <div 
                      className="bg-[#004ccd] h-1.5 rounded-full transition-all duration-300" 
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                  className="p-1.5 rounded-full text-[#424656] hover:text-[#ba1a1a] hover:bg-[#ffdad6]"
                  title="Remove File"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-4 pt-4 border-t border-[#c3c6d8]">
            <button
              type="button"
              onClick={() => setActiveTab('dashboard')}
              className="px-6 py-3 rounded-lg text-[#424656] font-semibold text-xs uppercase tracking-wider hover:bg-[#e0e2e6] transition-colors"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleRunAnalysis}
              disabled={isAnalyzing}
              className="px-8 py-3 rounded-lg bg-[#004ccd] text-white font-semibold text-xs uppercase tracking-wider hover:bg-[#003da9] shadow-sm transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <Cpu className="w-4 h-4" />
              {isAnalyzing ? 'Analyzing AI Kinematics...' : 'Run Analysis'}
            </button>
          </div>
        </form>
      </div>

      {/* Using Global Upload Progress Widget instead of full screen modal */}

      {/* Analysis Done Confirmation Banner */}
      {analysisDone && (
        <div className="bg-[#c4f2c7] border border-[#11801c]/30 rounded-xl p-6 text-[#0f5132] flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-8 h-8 text-[#11801c] shrink-0" />
            <div>
              <h4 className="text-base font-bold">Analysis Complete!</h4>
              <p className="text-xs text-[#0f5132]">
                New motion scan data recorded for target athlete. Session summary added to Dashboard activity.
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setAnalysisDone(false);
                setActiveTab('dashboard');
              }}
              className="px-4 py-2 bg-[#11801c] text-white rounded-lg text-xs font-semibold hover:bg-[#0f5132]"
            >
              View Dashboard
            </button>
          </div>
        </div>
      )}

      {/* Guidance Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-[#c3c6d8] flex gap-4 items-start shadow-xs">
          <Lightbulb className="w-5 h-5 text-[#304db9] mt-0.5 shrink-0" />
          <div>
            <h4 className="text-sm font-bold text-[#191c1f] mb-1">Lighting Matters</h4>
            <p className="text-xs text-[#424656]">
              Ensure the athlete is well-lit from the front. Avoid severe backlighting to improve joint tracking accuracy.
            </p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#c3c6d8] flex gap-4 items-start shadow-xs">
          <Focus className="w-5 h-5 text-[#304db9] mt-0.5 shrink-0" />
          <div>
            <h4 className="text-sm font-bold text-[#191c1f] mb-1">Frame Consistency</h4>
            <p className="text-xs text-[#424656]">
              Keep the camera stationary throughout the movement. Panning can skew kinematic calculations.
            </p>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-[#c3c6d8] flex gap-4 items-start shadow-xs">
          <Ruler className="w-5 h-5 text-[#304db9] mt-0.5 shrink-0" />
          <div>
            <h4 className="text-sm font-bold text-[#191c1f] mb-1">Calibration Object</h4>
            <p className="text-xs text-[#424656]">
              If possible, include an object of known length in the frame to calibrate absolute measurements.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
