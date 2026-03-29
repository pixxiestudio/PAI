'use client';

import { useRef, useState, useCallback } from 'react';
import { Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface UploadFile {
  file: File;
  progress: number;
  error?: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  preview?: string;
}

interface FileUploadProps {
  onUpload: (files: File[]) => Promise<void>;
  accept?: string;
  maxSize?: number; // in bytes
  maxFiles?: number;
  disabled?: boolean;
  onError?: (error: Error) => void;
}

/**
 * File Upload Component with drag-and-drop support
 * Handles file selection, validation, and upload progress tracking
 */
export function FileUpload({
  onUpload,
  accept = '*',
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  disabled = false,
  onError,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const validateFiles = (filesToValidate: File[]): UploadFile[] => {
    const validatedFiles: UploadFile[] = [];

    for (const file of filesToValidate) {
      if (file.size > maxSize) {
        const error = `File ${file.name} is too large (max ${maxSize / 1024 / 1024}MB)`;
        validatedFiles.push({
          file,
          progress: 0,
          error,
          status: 'error',
        });
        continue;
      }

      // Create preview for images
      let preview: string | undefined;
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          preview = e.target?.result as string;
        };
        reader.readAsDataURL(file);
      }

      validatedFiles.push({
        file,
        progress: 0,
        status: 'pending',
        preview,
      });
    }

    return validatedFiles;
  };

  const handleFiles = useCallback(
    (filesToHandle: File[]) => {
      if (filesToHandle.length + files.length > maxFiles) {
        const error = new Error(`Maximum ${maxFiles} files allowed`);
        onError?.(error);
        return;
      }

      const validated = validateFiles(filesToHandle);
      setFiles((prev) => [...prev, ...validated]);
    },
    [files.length, maxFiles, onError, validateFiles]
  );

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    handleFiles(droppedFiles);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      handleFiles(selectedFiles);
    }
  };

  const handleUpload = async () => {
    const filesToUpload = files
      .filter((f) => f.status === 'pending' || f.status === 'error')
      .map((f) => f.file);

    if (filesToUpload.length === 0) return;

    setIsUploading(true);

    try {
      // Update status to uploading
      setFiles((prev) =>
        prev.map((f) =>
          filesToUpload.includes(f.file) ? { ...f, status: 'uploading' } : f
        )
      );

      // Simulated upload with progress (real implementation would use XMLHttpRequest)
      await onUpload(filesToUpload);

      // Mark as success
      setFiles((prev) =>
        prev.map((f) =>
          filesToUpload.includes(f.file)
            ? { ...f, status: 'success', progress: 100 }
            : f
        )
      );
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      onError?.(new Error(errorMessage));

      setFiles((prev) =>
        prev.map((f) =>
          filesToUpload.includes(f.file)
            ? { ...f, status: 'error', error: errorMessage }
            : f
        )
      );
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    setFiles([]);
  };

  const pendingCount = files.filter((f) => f.status === 'pending').length;
  const successCount = files.filter((f) => f.status === 'success').length;

  return (
    <div className="space-y-4">
      {/* Drag and Drop Area */}
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-pai-primary bg-pai-primary/5'
            : 'border-gray-300 hover:border-gray-400'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          onChange={handleInputChange}
          disabled={disabled || isUploading}
          className="hidden"
        />

        <Upload className="h-12 w-12 mx-auto mb-2 text-gray-400" />
        <p className="text-gray-700 font-medium">Drag files here or click to select</p>
        <p className="text-sm text-gray-500">
          Maximum {maxFiles} files, {maxSize / 1024 / 1024}MB each
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <p className="text-sm font-medium text-gray-700">
              {files.length} file{files.length !== 1 ? 's' : ''} selected
            </p>
            {files.length > 0 && (
              <button
                onClick={clearAll}
                disabled={isUploading}
                className="text-xs text-gray-500 hover:text-gray-700 disabled:opacity-50"
              >
                Clear all
              </button>
            )}
          </div>

          {files.map((uploadFile, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 bg-gray-50 rounded border border-gray-200"
            >
              {/* File Preview */}
              {uploadFile.preview ? (
                <img
                  src={uploadFile.preview}
                  alt={uploadFile.file.name}
                  className="w-10 h-10 rounded object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded bg-gray-200 flex items-center justify-center">
                  <span className="text-xs font-semibold text-gray-600">
                    {uploadFile.file.name.split('.').pop()?.toUpperCase().slice(0, 3)}
                  </span>
                </div>
              )}

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {uploadFile.file.name}
                </p>
                <p className="text-xs text-gray-500">
                  {(uploadFile.file.size / 1024).toFixed(2)} KB
                </p>

                {/* Progress Bar */}
                {uploadFile.status === 'uploading' && (
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-1">
                    <div
                      className="bg-pai-primary h-1 rounded-full transition-all"
                      style={{ width: `${uploadFile.progress}%` }}
                    />
                  </div>
                )}

                {/* Error Message */}
                {uploadFile.error && (
                  <p className="text-xs text-red-600 mt-1">{uploadFile.error}</p>
                )}
              </div>

              {/* Status Icon */}
              <div className="flex-shrink-0">
                {uploadFile.status === 'success' && (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                )}
                {uploadFile.status === 'error' && (
                  <AlertCircle className="h-5 w-5 text-red-600" />
                )}
                {(uploadFile.status === 'pending' || uploadFile.status === 'uploading') && (
                  <button
                    onClick={() => removeFile(index)}
                    disabled={isUploading}
                    className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Button */}
      {pendingCount > 0 && (
        <Button
          onClick={handleUpload}
          disabled={isUploading || pendingCount === 0}
          className="w-full"
        >
          {isUploading ? 'Uploading...' : `Upload ${pendingCount} file${pendingCount !== 1 ? 's' : ''}`}
        </Button>
      )}

      {/* Success Message */}
      {successCount > 0 && (
        <div className="p-3 bg-green-50 border border-green-200 rounded text-sm text-green-800">
          ✓ {successCount} file{successCount !== 1 ? 's' : ''} uploaded successfully
        </div>
      )}
    </div>
  );
}
