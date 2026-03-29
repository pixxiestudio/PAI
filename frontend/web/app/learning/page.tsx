'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  Activity,
  Target,
  Zap,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import { useLearning } from '@/hooks/useLearning';
import { useUser } from '@/contexts/UserContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ErrorAlert } from '@/components/ErrorDisplay';
import { LearningDashboardSkeleton } from '@/components/LoadingStates';

function LearningPageContent() {
  const { user } = useUser();
  const {
    patterns = [],
    preferences = [],
    successRate = 0,
    totalInteractions = 0,
    isLoading,
    error,
  } = useLearning(user?.paiInstanceId || '');

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <ArrowUp className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ArrowDown className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getEffectivenessColor = (effectiveness: number) => {
    if (effectiveness >= 0.85) return 'success';
    if (effectiveness >= 0.7) return 'warning';
    return 'outline';
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 p-4 shadow-sm sticky top-0 z-10">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center gap-3">
              <TrendingUp className="h-6 w-6 text-pai-accent" />
              <h1 className="text-2xl font-bold text-pai-dark">Learning Dashboard</h1>
            </div>
            <Link href="/" className="text-pai-primary hover:text-pai-secondary transition text-sm">
              ← Back to Dashboard
            </Link>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 p-4">
          <div className="max-w-7xl mx-auto space-y-6">
            {error && (
              <ErrorAlert
                error={error}
                title="Learning Data Error"
              />
            )}

            {isLoading && <LearningDashboardSkeleton />}
            {!isLoading && (
            <>
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    Total Interactions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-pai-primary">
                    {totalInteractions}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">tracked interactions</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    Success Rate
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-pai-secondary">
                    {Math.round(successRate * 100)}%
                  </div>
                  <p className="text-xs text-gray-500 mt-1">overall performance</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    Patterns Detected
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-pai-accent">
                    {patterns.length}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Active patterns</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    Preferences
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-600">
                    {preferences.length}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Learned preferences</p>
                </CardContent>
              </Card>
            </div>

            {/* Learning Patterns */}
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold text-pai-dark mb-4">
                  Learning Patterns
                </h2>
                <div className="space-y-3">
                  {patterns.map((pattern) => (
                    <Card key={pattern.id} className="hover:shadow-md transition">
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">
                              {pattern.pattern}
                            </p>
                            <div className="flex gap-4 mt-3">
                              <div className="text-sm">
                                <span className="text-gray-500">Frequency:</span>
                                <p className="font-semibold text-gray-900">
                                  {pattern.frequency} times
                                </p>
                              </div>
                              <div className="text-sm">
                                <span className="text-gray-500">Effectiveness:</span>
                                <p className="font-semibold text-gray-900">
                                  {Math.round(pattern.effectiveness * 100)}%
                                </p>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant={getEffectivenessColor(pattern.effectiveness)}>
                              {Math.round(pattern.effectiveness * 100)}%
                            </Badge>
                            {getTrendIcon(pattern.trend)}
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="mt-3">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-pai-primary to-pai-secondary h-2 rounded-full transition-all"
                              style={{
                                width: `${pattern.effectiveness * 100}%`,
                              }}
                            />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>

            {/* Learned Preferences */}
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold text-pai-dark mb-4">
                  Learned Preferences
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {preferences.map((pref) => (
                    <Card key={pref.id}>
                      <CardContent className="pt-6">
                        <div className="space-y-3">
                          <div className="flex items-start justify-between">
                            <p className="font-medium text-gray-900">
                              {pref.preference}
                            </p>
                            <Badge variant="secondary">
                              {Math.round(pref.weight * 100)}
                            </Badge>
                          </div>

                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-500">Confidence</span>
                            <span className="font-semibold text-gray-900">
                              {Math.round(pref.weight * 100)}%
                            </span>
                          </div>

                          {/* Confidence Bar */}
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-gradient-to-r from-pai-primary to-pai-secondary h-2 rounded-full transition-all"
                              style={{ width: `${pref.weight * 100}%` }}
                            />
                          </div>

                          <div className="text-xs text-gray-500">
                            Source: <span className="font-medium">{pref.source.replace(/_/g, ' ')}</span>
                          </div>

                          <Button variant="ghost" size="sm" className="w-full mt-2">
                            <Target className="h-3 w-3 mr-1" />
                            Adjust Weight
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </div>

            {/* Learning Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Recent Learning Events
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[
                    { time: '2 hours ago', event: 'Detected preference for async/await patterns' },
                    { time: '5 hours ago', event: 'Improved understanding of user API preferences' },
                    { time: '1 day ago', event: 'Learned user timezone preference' },
                    { time: '2 days ago', event: 'Detected communication style preferences' },
                  ].map((item, idx) => (
                    <div key={idx} className="flex gap-3 pb-3 border-b border-gray-200 last:border-0">
                      <div className="text-sm text-gray-500 min-w-fit">{item.time}</div>
                      <div className="text-sm text-gray-900">{item.event}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Export Button */}
            <div className="flex justify-end gap-2 pb-4">
              <Button variant="outline">Download Report</Button>
              <Button variant="default">Export Learning Data</Button>
            </div>
            </>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default function LearningPage() {
  return (
    <ErrorBoundary
      onError={(error) => {
        console.error('Learning page error:', error);
      }}
    >
      <LearningPageContent />
    </ErrorBoundary>
  );
}
