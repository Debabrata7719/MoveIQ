"use client";

import React from 'react';
import { useUpload } from '@/context/UploadContext';
import { Loader2, CheckCircle2, AlertCircle, X } from 'lucide-react';

export const GlobalUploadProgress: React.FC = () => {
  const { isUploading, progress, fileName, error, clearUpload } = useUpload();

  if (!isUploading && !error && progress !== 100) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 bg-white border border-[#c3c6d7] rounded-xl shadow-2xl p-4 animate-in slide-in-from-bottom-5">
      
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 text-[#191c1f]">
          {error ? (
            <AlertCircle className="w-5 h-5 text-red-500" />
          ) : progress === 100 ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
          ) : (
            <Loader2 className="w-5 h-5 animate-spin text-[#004ccd]" />
          )}
          <span className="font-bold text-sm truncate max-w-[200px]">
            {error ? "Upload Failed" : progress === 100 ? "Analysis Complete!" : fileName || "Uploading Video..."}
          </span>
        </div>
        
        {/* Allow dismissing if error or complete */}
        {(error || progress === 100) && (
          <button onClick={clearUpload} className="text-slate-400 hover:text-slate-700">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {!error && (
        <div className="w-full mt-3">
          <div className="flex justify-between text-xs font-bold text-[#434654] mb-1">
              <span>{progress < 100 ? 'Analyzing Biomechanics...' : 'Done'}</span>
              <span className="text-[#004ccd]">{progress}%</span>
          </div>
          <div className="w-full bg-[#e2e1ed] rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ease-out ${
                progress === 100 ? 'bg-emerald-500' : 'bg-[#00379b]'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="mt-2 text-xs font-semibold text-red-600">
          {error}
        </div>
      )}
    </div>
  );
};
