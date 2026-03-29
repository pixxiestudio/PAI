'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import {
  Brain,
  Plus,
  Search,
  Trash2,
  Edit,
  Eye,
  EyeOff,
  ChevronDown,
} from 'lucide-react';
import { useMemory, Memory } from '@/hooks/useMemory';
import { useUser } from '@/contexts/UserContext';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ErrorAlert } from '@/components/ErrorDisplay';
import { MemoryListSkeleton, EmptyState } from '@/components/LoadingStates';
import { useErrorHandler } from '@/hooks/useAsyncOperation';

function MemoryPageContent() {
  const { user } = useUser();
  const { error: operationError, handleError } = useErrorHandler();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [expandedMemoryId, setExpandedMemoryId] = useState<string | null>(null);
  const [showNewMemoryForm, setShowNewMemoryForm] = useState(false);
  const [newMemory, setNewMemory] = useState({ content: '', category: '' });

  const {
    memories,
    isLoading,
    error: memoryError,
    saveMemory,
    isSaving,
    updateImportance,
    isUpdating,
    deleteMemory,
    isDeleting,
  } = useMemory(user?.id || '');

  const categories = ['preferences', 'interests', 'knowledge', 'patterns'];

  const filteredMemories = memories.filter((memory) => {
    const matchesSearch = memory.content
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesCategory = !selectedCategory || memory.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemory.content.trim()) return;

    try {
      await saveMemory({
        content: newMemory.content,
        category: newMemory.category || 'knowledge',
        importance: 0.5,
      });
      setNewMemory({ content: '', category: '' });
      setShowNewMemoryForm(false);
    } catch (err) {
      handleError(err);
    }
  };

  const handleDeleteMemory = async (id: string) => {
    try {
      await deleteMemory(id);
    } catch (err) {
      handleError(err);
    }
  };

  const handleUpdateImportance = async (id: string, newImportance: number) => {
    try {
      await updateImportance(id, newImportance);
    } catch (err) {
      handleError(err);
    }
  };

  const getImportanceBadgeColor = (importance: number) => {
    if (importance >= 0.8) return 'success';
    if (importance >= 0.5) return 'warning';
    return 'outline';
  };

  return (
    <main className="min-h-screen bg-gray-50">
      <div className="flex h-screen flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 p-4 shadow-sm">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Brain className="h-6 w-6 text-pai-secondary" />
              <h1 className="text-2xl font-bold text-pai-dark">Memory Browser</h1>
            </div>
            <Link href="/" className="text-pai-primary hover:text-pai-secondary transition text-sm">
              ← Back to Dashboard
            </Link>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-7xl mx-auto space-y-4">
            {(memoryError || operationError) && (
              <ErrorAlert
                error={memoryError || operationError}
                title="Memory Error"
              />
            )}
            {/* Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search memories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* New Memory Button */}
              <Button
                onClick={() => setShowNewMemoryForm(!showNewMemoryForm)}
                variant="default"
                className="justify-center"
              >
                <Plus className="h-4 w-4 mr-2" />
                New Memory
              </Button>
            </div>

            {/* Category Filter */}
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={selectedCategory === null ? 'default' : 'outline'}
                onClick={() => setSelectedCategory(null)}
                size="sm"
              >
                All
              </Button>
              {categories.map((cat) => (
                <Button
                  key={cat}
                  variant={selectedCategory === cat ? 'default' : 'outline'}
                  onClick={() => setSelectedCategory(cat)}
                  size="sm"
                  className="capitalize"
                >
                  {cat}
                </Button>
              ))}
            </div>

            {/* New Memory Form */}
            {showNewMemoryForm && (
              <Card className="border-pai-primary/50 bg-blue-50">
                <CardHeader>
                  <CardTitle className="text-lg">Add New Memory</CardTitle>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleAddMemory} className="space-y-4">
                    <Textarea
                      placeholder="Memory content..."
                      value={newMemory.content}
                      onChange={(e) => setNewMemory({ ...newMemory, content: e.target.value })}
                      className="min-h-24"
                    />
                    <div className="flex gap-2">
                      <select
                        value={newMemory.category}
                        onChange={(e) =>
                          setNewMemory({ ...newMemory, category: e.target.value })
                        }
                        className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pai-primary flex-1"
                      >
                        <option value="">Select Category</option>
                        {categories.map((cat) => (
                          <option key={cat} value={cat}>
                            {cat}
                          </option>
                        ))}
                      </select>
                      <Button type="submit" disabled={isSaving}>
                        {isSaving ? 'Saving...' : 'Save'}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        disabled={isSaving}
                        onClick={() => {
                          setShowNewMemoryForm(false);
                          setNewMemory({ content: '', category: '' });
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            )}

            {/* Memories Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {isLoading ? (
                <MemoryListSkeleton />
              ) : filteredMemories.length === 0 ? (
                <Card className="md:col-span-2">
                  <CardContent className="pt-6">
                    <EmptyState
                      title="No memories found"
                      description="Create one to get started!"
                      icon={Brain}
                    />
                  </CardContent>
                </Card>
              ) : (
                filteredMemories.map((memory) => (
                  <Card
                    key={memory.id}
                    className="overflow-hidden hover:shadow-md transition"
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <Badge
                            variant="secondary"
                            className="capitalize mb-2"
                          >
                            {memory.category}
                          </Badge>
                        </div>
                        <Badge variant={getImportanceBadgeColor(memory.importance)}>
                          {Math.round(memory.importance * 100)}%
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p
                        className={`text-sm ${
                          expandedMemoryId === memory.id
                            ? ''
                            : 'line-clamp-2'
                        }`}
                      >
                        {memory.content}
                      </p>

                      {/* Importance Slider */}
                      <div className="space-y-2">
                        <label className="text-xs text-gray-600">
                          Importance
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.1"
                          value={memory.importance}
                          onChange={(e) =>
                            handleUpdateImportance(
                              memory.id,
                              parseFloat(e.target.value)
                            )
                          }
                          className="w-full"
                        />
                      </div>

                      {/* Meta Info */}
                      <div className="text-xs text-gray-500 flex justify-between">
                        <span>
                          Created: {new Date(memory.createdAt).toLocaleDateString()}
                        </span>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 pt-2 border-t border-gray-200">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            setExpandedMemoryId(
                              expandedMemoryId === memory.id ? null : memory.id
                            )
                          }
                          className="flex-1"
                        >
                          {expandedMemoryId === memory.id ? (
                            <>
                              <EyeOff className="h-3 w-3 mr-1" />
                              Hide
                            </>
                          ) : (
                            <>
                              <Eye className="h-3 w-3 mr-1" />
                              More
                            </>
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={isDeleting}
                          className="text-red-500 hover:text-red-700"
                          onClick={() => handleDeleteMemory(memory.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>

            {/* Stats */}
            <Card className="bg-gradient-to-r from-pai-primary/10 to-pai-secondary/10">
              <CardHeader>
                <CardTitle className="text-lg">Memory Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Memories</p>
                    <p className="text-2xl font-bold text-pai-primary">
                      {memories.length}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Avg Importance</p>
                    <p className="text-2xl font-bold text-pai-secondary">
                      {memories.length > 0
                        ? Math.round(
                          (memories.reduce((sum, m) => sum + m.importance, 0) /
                            memories.length) *
                          100
                        )
                        : 0}
                      %
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Top Category</p>
                    <p className="text-lg font-semibold text-pai-accent capitalize">
                      {memories.length > 0
                        ? categories.reduce((max, cat) => {
                          const count = memories.filter(m => m.category === cat).length;
                          const maxCount = memories.filter(m => m.category === max).length;
                          return count > maxCount ? cat : max;
                        })
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}

export default function MemoryPage() {
  return (
    <ErrorBoundary
      onError={(error) => {
        console.error('Memory page error:', error);
      }}
    >
      <MemoryPageContent />
    </ErrorBoundary>
  );
}
