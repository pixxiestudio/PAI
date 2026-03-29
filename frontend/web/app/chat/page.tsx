'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string>('');
  const [message, setMessage] = useState('');

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement message sending with useChat hook
    console.log('Sending message:', message);
    setMessage('');
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-pai-primary to-pai-secondary">
      <div className="flex h-screen">
        {/* Sidebar */}
        <aside className="w-64 bg-pai-dark text-white p-4 border-r border-pai-primary">
          <div className="mb-6">
            <h1 className="text-2xl font-bold">PAI Chat</h1>
          </div>

          <div className="space-y-2">
            <button className="w-full bg-pai-primary text-white py-2 px-4 rounded-lg hover:bg-opacity-90 transition">
              + New Chat
            </button>
          </div>

          <div className="mt-8 border-t border-gray-700 pt-4">
            <h2 className="text-sm font-semibold text-gray-400 mb-4">RECENT</h2>
            <div className="space-y-2">
              <p className="text-sm text-gray-400">No recent chats</p>
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 p-4 shadow-sm">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-pai-dark">
                {sessionId || 'Select or Create a Chat'}
              </h2>
              <Link
                href="/"
                className="text-pai-primary hover:text-pai-secondary transition"
              >
                ← Back
              </Link>
            </div>
          </header>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
            <div className="max-w-2xl mx-auto">
              <div className="text-center text-gray-500 mt-8">
                <p>Select a chat to start messaging or create a new one</p>
              </div>
            </div>
          </div>

          {/* Input Area */}
          <div className="bg-white border-t border-gray-200 p-4 shadow-lg">
            <form onSubmit={handleSendMessage} className="max-w-2xl mx-auto">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type your message..."
                  disabled={!sessionId}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-pai-primary disabled:bg-gray-100 disabled:text-gray-400"
                />
                <button
                  type="submit"
                  disabled={!message || !sessionId}
                  className="bg-pai-primary text-white px-6 py-3 rounded-lg hover:bg-opacity-90 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Send
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </main>
  );
}
