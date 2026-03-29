'use client';

import { useState, useCallback, useRef } from 'react';

export interface StreamingOptions {
  endpoint: string;
  onChunk?: (chunk: string) => void;
  onComplete?: (fullContent: string) => void;
  onError?: (error: Error) => void;
  headers?: Record<string, string>;
}

/**
 * Hook for handling streaming responses (SSE)
 * Handles real-time updates from API endpoints that support streaming
 */
export function useStreaming() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [content, setContent] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(
    async (options: StreamingOptions) => {
      const { endpoint, onChunk, onComplete, onError: onErrorCallback, headers } = options;

      setIsStreaming(true);
      setError(null);
      setContent('');

      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();

      try {
        const authToken = localStorage.getItem('authToken');
        const defaultHeaders: Record<string, string> = {
          'Authorization': `Bearer ${authToken || ''}`,
          ...headers,
        };

        const response = await fetch(endpoint, {
          method: 'GET',
          headers: defaultHeaders,
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.error || `Streaming failed with status ${response.status}`
          );
        }

        // Handle Server-Sent Events (SSE)
        if (response.headers.get('content-type')?.includes('text/event-stream')) {
          const reader = response.body?.getReader();
          if (!reader) throw new Error('No response body');

          const decoder = new TextDecoder();
          let fullContent = '';

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split('\n');

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.slice(6);
                  if (data === '[DONE]') {
                    // Stream complete
                    onComplete?.(fullContent);
                    break;
                  }

                  try {
                    const parsed = JSON.parse(data);
                    const text = parsed.content || parsed.text || '';
                    fullContent += text;
                    onChunk?.(text);
                    setContent(fullContent);
                  } catch (e) {
                    // Invalid JSON, skip
                  }
                }
              }
            }
          } finally {
            reader.releaseLock();
          }
        } else {
          // Handle regular streaming (chunked transfer)
          const reader = response.body?.getReader();
          if (!reader) throw new Error('No response body');

          const decoder = new TextDecoder();
          let fullContent = '';

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              fullContent += chunk;
              onChunk?.(chunk);
              setContent(fullContent);
            }
          } finally {
            reader.releaseLock();
          }

          onComplete?.(fullContent);
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          // Stream was cancelled
          return;
        }

        const error = err instanceof Error ? err : new Error('Streaming failed');
        setError(error);
        onErrorCallback?.(error);
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    []
  );

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  }, []);

  const reset = useCallback(() => {
    stopStream();
    setContent('');
    setError(null);
  }, [stopStream]);

  return {
    startStream,
    stopStream,
    reset,
    isStreaming,
    error,
    content,
  };
}
