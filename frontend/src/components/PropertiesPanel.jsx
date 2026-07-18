import { useMemo } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { setSelectedCluster, clearSelectedCluster, setSelectedPoint } from '../store/clusterSlice'
import { IconTarget, IconClose } from './icons'

function ClusterList({ clusters, selectedCluster, onSelect }) {
  const sorted = useMemo(
    () => [...clusters].sort((a, b) => b.size - a.size),
    [clusters]
  )

  if (sorted.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-gray-400">
        Run clustering to see groups
      </div>
    )
  }

  return (
    <div className="space-y-1.5">
      {sorted.map(cluster => {
        const isActive = selectedCluster === cluster.id
        return (
          <button
            key={cluster.id}
            type="button"
            onClick={() => onSelect(cluster.id)}
            aria-pressed={isActive}
            className={`cluster-chip ${isActive ? 'cluster-chip-active' : ''}`}
          >
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ backgroundColor: cluster.color }}
              aria-hidden="true"
            />
            <span className="text-sm font-medium text-gray-900 truncate flex-1 text-left">
              {cluster.name}
            </span>
            <span className={`text-xs font-mono tabular-nums px-1.5 py-0.5 rounded ${
              isActive ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-600'
            }`}>
              {cluster.size}
            </span>
          </button>
        )
      })}
    </div>
  )
}

function SelectedPointCard({ point, clusterName, onClear }) {
  if (!point) return null
  return (
    <div className="bg-primary-50 border border-primary-200 rounded-lg p-3 relative">
      <button
        type="button"
        onClick={onClear}
        className="absolute top-2 right-2 text-primary-400 hover:text-primary-600 active:text-primary-700 p-1 -mr-1 -mt-1 touch-target"
        aria-label="Clear selection"
      >
        <IconClose className="w-4 h-4" />
      </button>
      <h3 className="text-xs font-semibold text-primary-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
        <IconTarget className="w-3.5 h-3.5" />
        Selected Point
      </h3>
      <p className="text-sm text-gray-900 font-medium mb-3 break-words pr-6">
        "{point.text}"
      </p>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold mb-0.5">Cluster</p>
          <p className="font-medium text-gray-900 truncate">{clusterName || 'Unknown'}</p>
        </div>
        <div>
          <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold mb-0.5">Confidence</p>
          <p className="font-mono tabular-nums font-semibold text-primary-700">
            {point.confidence.toFixed(3)}
          </p>
        </div>
      </div>
    </div>
  )
}

function SelectedClusterCard({ cluster, topItems }) {
  if (!cluster) return null
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-3">
        <span
          className="w-3 h-3 rounded-full flex-shrink-0"
          style={{ backgroundColor: cluster.color }}
          aria-hidden="true"
        />
        <h3 className="text-sm font-semibold text-gray-900 truncate flex-1">
          {cluster.name}
        </h3>
      </div>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold mb-0.5">Size</p>
          <p className="font-mono tabular-nums font-semibold text-gray-900">{cluster.size}</p>
        </div>
        <div>
          <p className="text-gray-500 uppercase tracking-wider text-[10px] font-semibold mb-0.5">ID</p>
          <p className="font-mono tabular-nums text-gray-600">{cluster.id}</p>
        </div>
      </div>

      {topItems.length > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Top by confidence
          </h4>
          <ul className="space-y-1.5 max-h-56 overflow-y-auto scrollbar-thin -mx-1 px-1">
            {topItems.map((item, index) => (
              <li
                key={index}
                className="text-xs p-2 bg-white border border-gray-100 rounded hover:border-gray-200 transition-colors"
              >
                <p className="text-gray-700 break-words leading-snug">{item.text}</p>
                <p className="font-mono tabular-nums text-primary-600 mt-1 font-semibold">
                  {item.confidence.toFixed(3)}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function StatisticsGrid({ stats }) {
  if (!stats) return null
  return (
    <div className="grid grid-cols-3 gap-2">
      <div className="stat-tile">
        <span className="stat-tile-label">Points</span>
        <span className="stat-tile-value">{stats.total_points}</span>
      </div>
      <div className="stat-tile">
        <span className="stat-tile-label">Clusters</span>
        <span className="stat-tile-value">{stats.num_clusters}</span>
      </div>
      <div className="stat-tile">
        <span className="stat-tile-label">Silhouette</span>
        <span className="stat-tile-value text-primary-600">
          {stats.silhouette_score?.toFixed(3) ?? '—'}
        </span>
      </div>
    </div>
  )
}

function PropertiesPanel() {
  const dispatch = useDispatch()
  const { clusters, points, stats, selectedCluster, selectedPoint } = useSelector((state) => state.cluster)

  const selectedClusterData = useMemo(() => {
    if (!selectedCluster) return null
    return clusters.find(c => c.id === selectedCluster)
  }, [clusters, selectedCluster])

  const clusterPoints = useMemo(() => {
    if (!selectedCluster) return []
    return points.filter(p => p.cluster === selectedCluster)
  }, [points, selectedCluster])

  const topItems = useMemo(() => {
    if (clusterPoints.length === 0) return []
    return [...clusterPoints]
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 5)
  }, [clusterPoints])

  const handleClusterClick = (clusterId) => {
    if (selectedCluster === clusterId) {
      dispatch(clearSelectedCluster())
    } else {
      dispatch(setSelectedCluster(clusterId))
    }
  }

  const selectedPointClusterName = selectedPoint
    ? clusters.find(c => c.id === selectedPoint.cluster)?.name
    : null

  return (
    <div className="flex flex-col h-full">
      <div className="hidden md:block mb-4">
        <h2 className="panel-header">Properties</h2>
      </div>

      <div className="flex-1 min-h-0 flex flex-col gap-4 overflow-y-auto scrollbar-thin -mx-1 px-1 pb-2">
        <SelectedPointCard
          point={selectedPoint}
          clusterName={selectedPointClusterName}
          onClear={() => dispatch(setSelectedPoint(null))}
        />

        <SelectedClusterCard
          cluster={selectedClusterData}
          topItems={topItems}
        />

        <div>
          <h3 className="panel-header mb-2 flex items-center justify-between">
            <span>All Clusters</span>
            <span className="text-gray-400 normal-case tracking-normal font-mono tabular-nums">
              {clusters.length}
            </span>
          </h3>
          <ClusterList
            clusters={clusters}
            selectedCluster={selectedCluster}
            onSelect={handleClusterClick}
          />
        </div>

        {stats && (
          <div className="pt-4 border-t border-gray-200">
            <h3 className="panel-header mb-3">Statistics</h3>
            <StatisticsGrid stats={stats} />
          </div>
        )}
      </div>
    </div>
  )
}

export default PropertiesPanel