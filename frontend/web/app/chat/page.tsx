'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Send, Plus, MessageSquare, Square } from 'lucide-react';
import { useChat, useSessions } from '@/hooks/useChat';
import { useUser } from '@/contexts/UserContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ErrorAlert } from '@/components/ErrorDisplay';
import { MessageListSkeleton } from '@/components/LoadingStates';
import { useErrorHandler } from '@/hooks/useAsyncOperation';
import { useStreaming } from '@/hooks/useStreaming';

function ChatPageContent() {
  const { user } = useUser();
  const [sessionId, setSessionId] = useState<string>('');
  const [message, setMessage] = useState('');
  const [streamingMessage, setStreamingMessage] = useState('');
  const { error: sessionError, handleError } = useErrorHandler();

  // Fetch user's sessions
  const {
    sessions,
    isLoading: sessionsLoading,
    error: sessionsError,
    createSession,
    isCreating,
  } = useSessions(user?.id || '');

  // Fetch messages for current session
  const {
    messages,
    isLoading: messagesLoading,
    error: messagesError,
    sendMessage,
    isSending,
  } = useChat(sessionId);

  // Streaming support
  const { startStream, stopStream, isStreaming, content: streamedContent } = useStreaming();

  // Update streaming message when content changes
  useEffect(() => {
    setStreamingMessage(streamedContent);
  }, [streamedContent]);

  const handleCreateNewChat = async () => {
    try {
      const newSession = await createSession('New Chat');
      setSessionId(newSession.id);
      setMessage('');
    } catch (err) {
      handleError(err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || !sessionId) return;

    const userMessage = message;
    setMessage('');
    setStreamingMessage('');

    try {
      // Send the user message first
      await sendMessage(userMessage);

      // Start streaming the AI response
      // Note: This assumes the API supports streaming at /api/proxy/sessions/{id}/stream
      await startStream({
        endpoint: `/api/proxy/sessions/${sessionId}/stream?message=${encodeURIComponent(userMessage)}`,
        onChunk: (chunk) => {
          setStreamingMessage((prev) => prev + chunk);
        },
        onComplete: (fullContent) => {
          // Store the complete streamed message
          console.log('Stream completed:', fullContent);
        },
        onError: (err) => {
          handleError(err);
        },
      });
    } catch (err) {
      handleError(err);
    }
  };

  const isLoading = messagesLoading || sessionsLoading;
  const error = messagesError || sessionsError || sessionError;

  return (
    <main className="min-h-screen bg-gray-100">
      <div className="flex h-screen">
        {/* Sidebar */}
        <aside className="w-64 bg-pai-dark text-white flex flex-col border-r border-pai-primary">
          <div className="p-4 border-b border-gray-700">
            <h1 className="text-2xl font-bold">PAI Chat</h1>
          </div>

          <div className="p-4 space-y-2 flex-1 flex flex-col">
            <Button
              onClick={handleCreateNewChat}
              className="w-full justify-start gap-2"
              variant="default"
            >
              <Plus className="h-4 w-4" />
              New Chat
            </Button>

            <div className="mt-8">
              <h2 className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-wide">
                Recent
              </h2>
              <div className="space-y-2">
                {sessionId ? (
                  <button
                    onClick={() => {}}
                    className="w-full text-left px-3 py-2 rounded bg-pai-primary/20 text-gray-100 hover:bg-pai-primary/30 transition text-sm flex items-center gap-2"
                  >
                    <MessageSquare className="h-4 w-4" />
                    {sessionId}
                  </button>
                ) : (
                  <p className="text-xs text-gray-500">No recent chats</p>
                )}
              </div>
            </div>
          </div>

          <div className="p-4 border-t border-gray-700">
            <Link
              href="/"
              className="text-xs text-gray-400 hover:text-gray-300 transition"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </aside>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col bg-white">
          {/* Header */}
          <header className="border-b border-gray-200 p-4 shadow-sm">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-xl font-semibold text-pai-dark">
                  {sessionId ? (
                    <div className="flex items-center gap-2">
                      <MessageSquare className="h-5 w-5 text-pai-primary" />
                      {sessionId}
                    </div>
                  ) : (
                    'Create or select a chat to start'
                  )}
                </h2>
              </div>
              <Badge variant={sessionId ? 'success' : 'outline'}>
                {sessionId ? 'Active' : 'No session'}
              </Badge>
            </div>
          </header>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {error && (
              <ErrorAlert
                error={error}
                onRetry={() => {}}
                title="Chat Error"
              />
            )}

            {!sessionId ? (
              <div className="h-full flex items-center justify-center">
                <Card className="w-full max-w-md">
                  <CardHeader>
                    <CardTitle className="text-center">Welcome to PAI Chat</CardTitle>
                  </CardHeader>
                  <CardContent className="text-center space-y-4">
                    <p className="text-gray-600">
                      Create a new chat session to start interacting with your PAI instance.
                    </p>
                    <Button
                      onClick={handleCreateNewChat}
                      disabled={isCreating}
                      className="w-full"
                      variant="default"
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      {isCreating ? 'Creating...' : 'Create New Chat'}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="space-y-4 max-w-2xl mx-auto w-full">
                {isLoading ? (
                  <MessageListSkeleton />
                ) : messages.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-30" />
                    <p>Start a conversation with your PAI instance</p>
                  </div>
                ) : (
                  <>
                    {messages.map((msg) => (
                      <div
                        key={msg.id}
                        className={`flex ${
                          msg.role === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                      >
                        <div
                          className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-lg ${
                            msg.role === 'user'
                              ? 'bg-pai-primary text-white rounded-br-none'
                              : 'bg-gray-100 text-gray-900 rounded-bl-none'
                          }`}
                        >
                          <p className="text-sm">{msg.content}</p>
                        </div>
                      </div>
                    ))}

                    {/* Streaming message display */}
                    {isStreaming && streamingMessage && (
                      <div className="flex justify-start">
                        <div className="max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-lg bg-gray-100 text-gray-900 rounded-bl-none">
                          <p className="text-sm whitespace-pre-wrap">{streamingMessage}</p>
                          <span className="inline-block w-2 h-4 bg-gray-400 ml-1 animate-pulse" />
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          {/* Input Area */}
          {sessionId && (
            <div className="bg-gray-50 border-t border-gray-200 p-4 shadow-lg">
              <form onSubmit={handleSendMessage} className="max-w-2xl mx-auto">
                <div className="flex gap-2">
                  <Input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Type your message..."
                    disabled={isSending || isStreaming}
                    className="flex-1"
                  />
                  {isStreaming ? (
                    <Button
                      type="button"
                      onClick={stopStream}
                      size="icon"
                      variant="destructive"
                      title="Stop streaming"
                    >
                      <Square className="h-4 w-4 fill-current" />
                    </Button>
                  ) : (
                    <Button
                      type="submit"
                      disabled={!message.trim() || isSending}
                      size="icon"
                      variant="default"
                    >
                      {isSending ? (
                        <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Send className="h-4 w-4" />
                      )}
                    </Button>
                  )}
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

export default function ChatPage() {
  return (
    <ErrorBoundary
      onError={(error) => {
        console.error('Chat page error:', error);
      }}
    >
      <ChatPageContent />
    </ErrorBoundary>
  );
}
