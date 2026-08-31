"use client";

import React, { createContext, useContext, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface UploadContextType {
  isUploading: boolean;
  progress: number;
  fileName: string;
  error: string | null;
  startUpload: (file: File, customName: string, token: string, athleteId?: string, onSuccess?: (data: any) => void) => Promise<void>;
  clearUpload: () => void;
}

const UploadContext = createContext<UploadContextType | undefined>(undefined);

export const UploadProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const router = useRouter();
  
  const wsRef = useRef<WebSocket | null>(null);

  const clearUpload = useCallback(() => {
    setIsUploading(false);
    setProgress(0);
    setFileName('');
    setError(null);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const startUpload = useCallback(async (file: File, customName: string, token: string, athleteId?: string, onSuccess?: (data: any) => void) => {
    if (isUploading) {
      setError("An upload is already in progress.");
      return;
    }
    
    if (!token) {
      setError("Authentication token missing.");
      return;
    }

    setIsUploading(true);
    setProgress(0);
    setFileName(file.name);
    setError(null);

    try {
      // 1. Get Signature
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const sigResponse = await fetch(`${apiUrl}/api/sessions/upload-signature`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!sigResponse.ok) {
        throw new Error('Failed to get upload signature');
      }
      const sigData = await sigResponse.json();
      
      // 2. Upload directly to Cloudinary
      const cloudinaryFormData = new FormData();
      cloudinaryFormData.append('file', file);
      cloudinaryFormData.append('api_key', sigData.api_key);
      cloudinaryFormData.append('timestamp', sigData.timestamp);
      cloudinaryFormData.append('signature', sigData.signature);
      cloudinaryFormData.append('folder', 'sports_injury_raw_videos');
      
      setProgress(10);
      const cloudRes = await fetch(`https://api.cloudinary.com/v1_1/${sigData.cloud_name}/video/upload`, {
        method: 'POST',
        body: cloudinaryFormData
      });
      
      if (!cloudRes.ok) {
        throw new Error('Direct upload to cloud failed');
      }
      const cloudData = await cloudRes.json();
      setProgress(50);
      
      // 3. Trigger processing on backend
      const payload: any = {
        secure_url: cloudData.secure_url,
        custom_name: customName.trim() || undefined
      };
      if (athleteId) {
        payload.athlete_id = athleteId;
      }
      
      const processRes = await fetch(`${apiUrl}/api/sessions/process-video`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
      });

      const data = await processRes.json();

      if (!processRes.ok) {
        throw new Error(data.detail || 'Failed to start analysis');
      }

      // 4. Connect WebSocket for Progress
      const wsProtocol = apiUrl.startsWith('https') ? 'wss' : 'ws';
      const wsHost = apiUrl.replace(/^https?:\/\//, '');
      const ws = new WebSocket(`${wsProtocol}://${wsHost}/api/ws/progress/${data.session_id}?token=${token}`);
      wsRef.current = ws;

      ws.onmessage = async (event) => {
        const msg = JSON.parse(event.data);
        
        if (msg.progress) {
          setProgress(msg.progress);
        }
        
        if (msg.step === "Analysis Complete") {
          ws.close();
          setProgress(100);
          
          try {
            // Fetch the final session data
            const res = await fetch(`${apiUrl}/api/sessions/${data.session_id}`, {
              headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
              const sessionData = await res.json();
              if (onSuccess) {
                onSuccess(sessionData);
              }
              // Wait 2 seconds before dismissing the global UI
              setTimeout(() => {
                clearUpload();
                // Optionally redirect to result page if needed
              }, 2000);
            }
          } catch (e) {
             console.error("Failed to fetch final session", e);
             clearUpload();
          }
        }
        
        if (msg.step === "ERROR") {
          ws.close();
          setError(msg.error || 'Pipeline failed');
          setIsUploading(false); // keep error visible, but not uploading
        }
      };

      ws.onerror = () => {
        setError('WebSocket connection failed.');
        setIsUploading(false);
      };

      ws.onclose = (event) => {
        if (!event.wasClean && isUploading) {
           // We might just log this, or set an error if it closed prematurely before 100%
           console.log("WebSocket disconnected");
        }
      };

    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.');
      setIsUploading(false);
    }
  }, [isUploading, clearUpload]);

  return (
    <UploadContext.Provider value={{ isUploading, progress, fileName, error, startUpload, clearUpload }}>
      {children}
    </UploadContext.Provider>
  );
};

export const useUpload = () => {
  const context = useContext(UploadContext);
  if (context === undefined) {
    throw new Error('useUpload must be used within an UploadProvider');
  }
  return context;
};
