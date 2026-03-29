'use client';

import { useState, useCallback } from 'react';
import { useAsyncOperation } from './useAsyncOperation';

export interface UploadProgress {
  fileIndex: number;
  fileName: string;
  progress: number;
}

export interface FileUploadResult {
  fileName: string;
  success: boolean;
  url?: string;
  error?: string;
}

interface UseFileUploadOptions {
  endpoint: string; // API endpoint path (e.g., '/users/123/memories')
  onProgress?: (progress: UploadProgress) => void;
  onSuccess?: (results: FileUploadResult[]) => void;
  onError?: (error: Error) => void;
}

/**
 * Hook for handling file uploads to the API
 * Manages upload progress, error states, and integrates with FileUpload component
 */
export function useFileUpload(options: UseFileUploadOptions) {
  const { endpoint, onProgress, onSuccess, onError } = options;
  const { execute, isLoading, error } = useAsyncOperation<FileUploadResult[]>();
  const [progress, setProgress] = useState<Record<string, number>>({});

  const uploadFiles = useCallback(
    async (files: File[]) => {
      try {
        const results: FileUploadResult[] = [];

        // Upload files sequentially to track progress per file
        for (let i = 0; i < files.length; i++) {
          const file = files[i];

          // Simulate progress tracking
          const progressInterval = setInterval(() => {
            setProgress((prev) => {
              const currentProgress = prev[file.name] || 0;
              const newProgress = Math.min(currentProgress + 10, 90);
              return { ...prev, [file.name]: newProgress };
            });

            onProgress?.({
              fileIndex: i,
              fileName: file.name,
              progress: progress[file.name] || 0,
            });
          }, 100);

          try {
            // Create FormData for multipart upload
            const formData = new FormData();
            formData.append('file', file);
            formData.append('fileName', file.name);
            formData.append('fileSize', file.size.toString());
            formData.append('fileType', file.type);

            const response = await fetch(`/api/proxy/${endpoint}`, {
              method: 'POST',
              body: formData,
              headers: {
                Authorization: `Bearer ${localStorage.getItem('authToken') || ''}`,
              },
            });

            clearInterval(progressInterval);

            if (!response.ok) {
              const errorData = await response.json().catch(() => ({}));
              results.push({
                fileName: file.name,
                success: false,
                error: errorData.error || `Upload failed with status ${response.status}`,
              });
              continue;
            }

            const data = await response.json();

            // Mark as complete
            setProgress((prev) => ({
              ...prev,
              [file.name]: 100,
            }));

            onProgress?.({
              fileIndex: i,
              fileName: file.name,
              progress: 100,
            });

            results.push({
              fileName: file.name,
              success: true,
              url: data.url || data.path,
            });
          } catch (err) {
            clearInterval(progressInterval);

            const errorMessage = err instanceof Error ? err.message : 'Upload failed';
            results.push({
              fileName: file.name,
              success: false,
              error: errorMessage,
            });
          }
        }

        // Call success callback
        onSuccess?.(results);

        // Return results from execute
        return results;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Upload failed');
        onError?.(error);
        throw error;
      }
    },
    [endpoint, onProgress, onSuccess, onError, progress]
  );

  const performUpload = useCallback(
    async (files: File[]) => {
      return execute(() => uploadFiles(files));
    },
    [execute, uploadFiles]
  );

  return {
    uploadFiles: performUpload,
    isUploading: isLoading,
    error,
    progress,
  };
}
