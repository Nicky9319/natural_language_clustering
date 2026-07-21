import { useState } from 'react'
import { useSelector } from 'react-redux'
import InputPanel from './components/InputPanel'
import ClusterChart from './components/ClusterChart'
import PropertiesPanel from './components/PropertiesPanel'
import MobileTabBar from './components/MobileTabBar'
import { IconChart, IconAlert } from './components/icons'

function Header() {
  const { status, stats, error } = useSelector((state) => state.cluster)
  const isLoading = status === 'loading'

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-20 pt-safe-top">
      <div className="px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center flex-shrink-0 shadow-sm">
                <IconChart className="w-5 h-5 text-white" />
              </div>
              <div className="min-w-0">
                <h1 className="text-base sm:text-xl font-bold text-gray-900 truncate">
                  <span className="hidden sm:inline">Natural Language Clustering</span>
                  <span className="sm:hidden">NL Clustering</span>
                </h1>
                <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">
                  Semantic text clustering visualization
                </p>
              </div>
            </div>
          </div>

          {/* Desktop stats */}
          {stats && (
            <div className="hidden lg:flex items-center gap-3 xl:gap-4">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500 text-xs uppercase tracking-wider font-medium">Points</span>
                <span className="font-mono tabular-nums font-semibold text-gray-900">{stats.total_points}</span>
              </div>
              <div className="w-px h-5 bg-gray-200" />
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500 text-xs uppercase tracking-wider font-medium">Clusters</span>
                <span className="font-mono tabular-nums font-semibold text-gray-900">{stats.num_clusters}</span>
              </div>
              <div className="w-px h-5 bg-gray-200" />
              <div className="flex items-center gap-2 text-sm">
                <span className="text-gray-500 text-xs uppercase tracking-wider font-medium">Silhouette</span>
                <span className="font-mono tabular-nums font-semibold text-primary-600">
                  {stats.silhouette_score?.toFixed(3) ?? '—'}
                </span>
              </div>
            </div>
          )}

          {/* Mobile status indicator */}
          <div className="flex lg:hidden items-center gap-2">
            {isLoading && (
              <span className="flex items-center gap-1.5 text-xs text-primary-600 font-medium">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500" />
                </span>
                <span>Processing</span>
              </span>
            )}
            {!isLoading && stats && (
              <div className="text-right text-xs">
                <div className="font-mono tabular-nums font-semibold text-gray-900">
                  {stats.total_points} <span className="text-gray-400 font-normal">pts</span>
                </div>
                <div className="font-mono tabular-nums text-gray-500">
                  {stats.num_clusters} <span className="text-gray-400 font-normal">clusters</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Mobile stats row */}
        {stats && (
          <div className="lg:hidden mt-3 grid grid-cols-3 gap-2">
            <div className="stat-tile">
              <span className="stat-tile-label">Points</span>
              <span className="stat-tile-value text-sm">{stats.total_points}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-tile-label">Clusters</span>
              <span className="stat-tile-value text-sm">{stats.num_clusters}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-tile-label">Silhouette</span>
              <span className="stat-tile-value text-sm text-primary-600">
                {stats.silhouette_score?.toFixed(3) ?? '—'}
              </span>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}

function EmptyChartState() {
  const { status } = useSelector((state) => state.cluster)
  const isLoading = status === 'loading'

  return (
    <div className="h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border-2 border-dashed border-gray-200">
      <div className="text-center px-6 max-w-sm">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary-100 to-primary-50 flex items-center justify-center">
          <IconChart className="w-8 h-8 text-primary-400" />
        </div>
        <h3 className="text-base font-semibold text-gray-900 mb-1">
          {isLoading ? 'Processing your text' : 'No visualization yet'}
        </h3>
        <p className="text-sm text-gray-500">
          {isLoading
            ? 'Generating clusters and embeddings…'
            : 'Enter at least 4 text lines, then tap Run Clustering to begin.'}
        </p>
      </div>
    </div>
  )
}

function ChartErrorBanner() {
  const { error } = useSelector((state) => state.cluster)
  if (!error) return null
  return (
    <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2 animate-fade-in">
      <IconAlert className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
      <p className="text-sm text-red-700 flex-1">{error}</p>
    </div>
  )
}

function ChartPanel() {
  const { status } = useSelector((state) => state.cluster)

  return (
    <div className="card p-3 sm:p-4 flex flex-col h-full overflow-hidden">
      <div className="hidden md:flex items-center justify-between mb-3">
        <h2 className="panel-header">Cluster Visualization</h2>
      </div>
      <ChartErrorBanner />
      <div className="flex-1 min-h-0">
        {status === 'succeeded' ? <ClusterChart /> : <EmptyChartState />}
      </div>
    </div>
  )
}

function App() {
  const { stats } = useSelector((state) => state.cluster)
  const [activeTab, setActiveTab] = useState('input')

  const textsCount = useSelector((state) => {
    const text = state.cluster.inputText || ''
    return text.split('\n').map(l => l.trim()).filter(l => l.length).length
  })

  return (
    <div className="min-h-screen-mobile bg-gray-50">
      <Header />

      {/* Mobile: tabbed single-panel view */}
      <main className="md:hidden px-4 pt-4 pb-24 h-screen-mobile overflow-hidden flex flex-col">
        {activeTab === 'input' && (
          <div className="card p-4 flex-1 flex flex-col overflow-hidden min-h-0 animate-fade-in">
            <InputPanel />
          </div>
        )}
        {activeTab === 'chart' && (
          <div className="flex-1 flex flex-col min-h-0 animate-fade-in">
            <ChartPanel />
          </div>
        )}
        {activeTab === 'insights' && (
          <div className="card p-4 flex-1 flex flex-col overflow-hidden min-h-0 animate-fade-in">
            <div className="md:hidden mb-4">
              <h2 className="panel-header">Properties</h2>
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <PropertiesPanel />
            </div>
          </div>
        )}
      </main>

      {/* Tablet: 2-column (input | chart) */}
      <main className="hidden md:block lg:hidden p-4 sm:p-6 h-screen-mobile overflow-hidden">
        <div className="flex gap-4 sm:gap-6 h-full pb-4">
          <div className="w-72 flex-shrink-0 card overflow-hidden flex flex-col">
            <InputPanel />
          </div>
          <div className="flex-1 min-w-0 flex flex-col min-h-0 overflow-hidden">
            <ChartPanel />
          </div>
        </div>
      </main>

      {/* Desktop: 3-column — fixed-width sidebar + flex chart + fixed properties */}
      <main className="hidden lg:block p-6 h-screen-mobile overflow-hidden">
        <div className="flex gap-6 h-full pb-6">
          {/* Left: fixed-width input panel */}
          <div className="w-80 flex-shrink-0 card overflow-hidden flex flex-col">
            <InputPanel />
          </div>

          {/* Center: flex chart area */}
          <div className="flex-1 min-w-0 flex flex-col min-h-0 overflow-hidden">
            <ChartPanel />
          </div>

          {/* Right: fixed-width properties panel */}
          <div className="w-72 flex-shrink-0 card overflow-hidden flex flex-col">
            <PropertiesPanel />
          </div>
        </div>
      </main>

      <MobileTabBar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        textsCount={textsCount}
        clustersCount={stats?.num_clusters || 0}
      />
    </div>
  )
}

export default App
