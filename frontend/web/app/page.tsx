'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-pai-primary to-pai-secondary p-4">
      <div className="max-w-4xl mx-auto">
        <div className="rounded-lg bg-white shadow-xl p-8">
          <h1 className="text-4xl font-bold text-pai-dark mb-2">
            PAI Dashboard
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Personal AI Instance - Web Interface (Phase 3.1)
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link href="/chat">
              <div className="border-2 border-pai-primary rounded-lg p-6 hover:shadow-lg hover:border-opacity-100 transition cursor-pointer bg-gradient-to-br from-blue-50 to-blue-100">
                <h2 className="text-xl font-semibold text-pai-primary mb-2">
                  💬 Chat
                </h2>
                <p className="text-gray-600">
                  Interact with your PAI instance through a web-based chat interface.
                </p>
                <p className="text-sm text-gray-500 mt-4">Click to open →</p>
              </div>
            </Link>

            <div className="border-2 border-pai-secondary rounded-lg p-6 hover:shadow-lg transition opacity-50 cursor-not-allowed">
              <h2 className="text-xl font-semibold text-pai-secondary mb-2">
                🧠 Memory
              </h2>
              <p className="text-gray-600">
                Browse and manage memories learned by your PAI instance.
              </p>
              <p className="text-xs text-gray-400 mt-4">Coming in Phase 3.2</p>
            </div>

            <div className="border-2 border-pai-accent rounded-lg p-6 hover:shadow-lg transition opacity-50 cursor-not-allowed">
              <h2 className="text-xl font-semibold text-pai-accent mb-2">
                📊 Learning
              </h2>
              <p className="text-gray-600">
                View learning patterns and effectiveness metrics.
              </p>
              <p className="text-xs text-gray-400 mt-4">Coming in Phase 3.2</p>
            </div>
          </div>

          <div className="mt-12 p-6 bg-pai-dark text-white rounded-lg">
            <h3 className="text-xl font-semibold mb-4">System Status</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-400">Backend API</p>
                <p className="text-lg font-semibold">http://localhost:8000</p>
                <p className="text-xs text-gray-500">Configure in .env.local</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Dashboard Version</p>
                <p className="text-lg font-semibold">0.1.0</p>
                <p className="text-xs text-gray-500">Phase 3.1 Foundation</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Framework</p>
                <p className="text-lg font-semibold">Next.js 14</p>
                <p className="text-xs text-gray-500">App Router + TypeScript</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Authentication</p>
                <p className="text-lg font-semibold">NextAuth.js v4</p>
                <p className="text-xs text-gray-500">Coming soon</p>
              </div>
            </div>
          </div>

          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-900">
              <span className="font-semibold">ℹ️ Getting Started:</span> Make sure your PAI backend (Phase 2) is running on port 8000. Update <code className="bg-white px-2 py-1 rounded">.env.local</code> with your API configuration.
            </p>
          </div>

          <div className="mt-8 grid grid-cols-3 gap-4 text-center text-sm text-gray-600">
            <div>
              <p className="font-semibold mb-1">Documentation</p>
              <a href="/docs" className="text-pai-primary hover:underline">
                View Docs
              </a>
            </div>
            <div>
              <p className="font-semibold mb-1">API Status</p>
              <a href="/api/proxy/health" className="text-pai-primary hover:underline">
                Check Health
              </a>
            </div>
            <div>
              <p className="font-semibold mb-1">Settings</p>
              <a href="/settings" className="text-pai-primary hover:underline">
                Configure
              </a>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
