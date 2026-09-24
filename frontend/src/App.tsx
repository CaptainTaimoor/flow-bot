import React, { useState } from 'react';
import { QueryClient, QueryClientProvider, useQuery, useMutation } from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { Sidebar, NavItem } from './components/Sidebar';
import { OverviewPage } from './pages/OverviewPage';
import { CreateVideoPage } from './pages/CreateVideoPage';
import { ActiveJobsPage } from './pages/ActiveJobsPage';
import { QueuePage } from './pages/QueuePage';
import { VideoLibraryPage } from './pages/VideoLibraryPage';
import { HistoryPage } from './pages/HistoryPage';
import { DiagnosticsPage } from './pages/DiagnosticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { VideoDetailModal } from './components/VideoDetailModal';
import { useEvents } from './hooks/useEvents';
import { api } from './api/client';
import { Asset, Job } from './types';
import { Bell, CheckCircle, AlertTriangle, X } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 3000,
      refetchOnWindowFocus: true,
    },
  },
});

interface Toast {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'error';
}

const MainApp: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavItem>('overview');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [createPrompt, setCreatePrompt] = useState<string>('');
  const [toasts, setToasts] = useState<Toast[]>([]);

  // Fetch status for active counts
  const { data: status } = useQuery({
    queryKey: ['status'],
    queryFn: api.getStatus,
    refetchInterval: 10000,
  });

  // Query jobs to match selectedAsset to its job for the detail modal
  const { data: jobs = [] } = useQuery({
    queryKey: ['jobs'],
    queryFn: () => api.getJobs(),
  });

  const addToast = (title: string, message: string, type: 'info' | 'success' | 'error' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev.slice(-4), { id, title, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 6000);
  };

  // Wire SSE events
  useEvents((event) => {
    if (event.type === 'job.completed') {
      addToast('Generation Complete', `Job #${event.data.job_id} generated video successfully!`, 'success');
    } else if (event.type === 'job.failed') {
      addToast('Job Failed', event.data.error || `Job #${event.data.job_id} failed`, 'error');
    } else if (event.type === 'auth.required') {
      addToast('Authentication Required', 'Please complete Google Flow login in the browser window.', 'error');
    }
  });

  // Mutations
  const createJobMutation = useMutation({
    mutationFn: api.createJob,
    onSuccess: (newJob) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
      addToast('Job Queued', `Job #${newJob.id} added to execution queue.`, 'info');
      setCurrentTab('active');
    },
    onError: (err: any) => {
      addToast('Failed to queue job', err.message, 'error');
    },
  });

  const retryJobMutation = useMutation({
    mutationFn: api.retryJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
      addToast('Job Retried', 'Job has been re-queued for execution.', 'info');
    },
  });

  const cancelJobMutation = useMutation({
    mutationFn: api.cancelJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
      addToast('Job Cancelled', 'Job was cancelled successfully.', 'info');
    },
  });

  const duplicateJobMutation = useMutation({
    mutationFn: api.duplicateJob,
    onSuccess: (newJob) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['status'] });
      addToast('Job Duplicated', `Job #${newJob.id} created and queued.`, 'info');
    },
  });

  const handleNavigateToCreate = (prompt?: string) => {
    if (prompt) setCreatePrompt(prompt);
    setCurrentTab('create');
  };

  const selectedJob = selectedAsset
    ? jobs.find((j) => j.id === selectedAsset.job_id)
    : undefined;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onTabChange={setCurrentTab}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          activeJobsCount={status?.stats.active || 0}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {currentTab === 'overview' && (
            <OverviewPage
              onCreateJob={(prompt) => handleNavigateToCreate(prompt)}
              onSelectAsset={setSelectedAsset}
              onNavigate={(tab) => setCurrentTab(tab)}
            />
          )}

          {currentTab === 'create' && (
            <CreateVideoPage
              initialPrompt={createPrompt}
              onSubmit={(jobData) => createJobMutation.mutate(jobData)}
            />
          )}

          {currentTab === 'active' && (
            <ActiveJobsPage
              onCancelJob={(id) => cancelJobMutation.mutate(id)}
              onOpenDiagnostics={() => setCurrentTab('diagnostics')}
            />
          )}

          {currentTab === 'queue' && (
            <QueuePage
              onRetry={(id) => retryJobMutation.mutate(id)}
              onCancel={(id) => cancelJobMutation.mutate(id)}
              onDuplicate={(id) => duplicateJobMutation.mutate(id)}
            />
          )}

          {currentTab === 'library' && (
            <VideoLibraryPage
              onSelectAsset={setSelectedAsset}
            />
          )}

          {currentTab === 'history' && (
            <HistoryPage
              onSelectAsset={setSelectedAsset}
              onNavigateToCreate={handleNavigateToCreate}
            />
          )}

          {currentTab === 'diagnostics' && (
            <DiagnosticsPage />
          )}

          {currentTab === 'settings' && (
            <SettingsPage />
          )}
        </main>
      </div>

      {/* Video Detail Modal with range-streaming player */}
      {selectedAsset && (
        <VideoDetailModal
          asset={selectedAsset}
          job={selectedJob}
          onClose={() => setSelectedAsset(null)}
          onDuplicatePrompt={(prompt) => {
            setSelectedAsset(null);
            handleNavigateToCreate(prompt);
          }}
        />
      )}

      {/* Toast Notification Container */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border shadow-2xl backdrop-blur-md transition-all animate-slide-up ${
              toast.type === 'success'
                ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-100'
                : toast.type === 'error'
                ? 'bg-rose-950/90 border-rose-500/40 text-rose-100'
                : 'bg-slate-900/90 border-slate-700/60 text-slate-100'
            }`}
          >
            {toast.type === 'success' && <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />}
            {toast.type === 'error' && <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />}
            {toast.type === 'info' && <Bell className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />}
            <div className="flex-1 min-w-0">
              <h4 className="text-xs font-semibold">{toast.title}</h4>
              <p className="text-xs opacity-90 mt-0.5 break-words">{toast.message}</p>
            </div>
            <button
              onClick={() => setToasts((prev) => prev.filter((t) => t.id !== toast.id))}
              className="text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MainApp />
    </QueryClientProvider>
  );
}
