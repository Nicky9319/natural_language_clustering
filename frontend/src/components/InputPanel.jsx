import { useCallback, useState, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setInputText, runClustering, loadSampleTexts } from '../store/clusterSlice'
import { IconPlus, IconClose, IconBolt, IconSparkles, IconInfo, IconSpinner, IconText, IconChevronDown } from './icons'
import { useVirtualizer } from '@tanstack/react-virtual'

const SAMPLE_COUNTS = [
  { value: 100, label: '100 texts' },
  { value: 1000, label: '1,000 texts' },
  { value: 5000, label: '5,000 texts' },
  { value: 10000, label: '10,000 texts' },
]

const ITEM_HEIGHT = 48  // fixed height per list row (px)

function InputPanel() {
  const dispatch = useDispatch()
  const { inputText, status, error } = useSelector((state) => state.cluster)
  const [newText, setNewText] = useState('')
  const [method, setMethod] = useState('hdbscan')
  const [nClusters, setNClusters] = useState('5')
  const [minClusterSize, setMinClusterSize] = useState('5')
  const [sampleCount, setSampleCount] = useState(100)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const inputRef = useRef(null)
  const listContainerRef = useRef(null)

  const texts = inputText
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.length > 0)

  // Virtual scroller — only renders visible rows
  const virtualizer = useVirtualizer({
    count: texts.length,
    getScrollElement: () => listContainerRef.current,
    estimateSize: () => ITEM_HEIGHT,
    overscan: 5,
  })

  const handleTextChange = useCallback((e) => {
    dispatch(setInputText(e.target.value))
  }, [dispatch])

  const handleAddText = useCallback(() => {
    if (newText.trim()) {
      const newInput = inputText ? `${inputText}\n${newText.trim()}` : newText.trim()
      dispatch(setInputText(newInput))
      setNewText('')
      inputRef.current?.focus()
    }
  }, [dispatch, inputText, newText])

  const handleRemoveText = useCallback((index) => {
    const newTexts = texts.filter((_, i) => i !== index)
    dispatch(setInputText(newTexts.join('\n')))
  }, [dispatch, texts])

  const handleRunClustering = useCallback(() => {
    if (texts.length < 2) {
      alert('Please enter at least 2 text lines to cluster.')
      return
    }
    const parsed = parseInt(nClusters, 10)
    // 0, 1, or empty → auto-detect (send null), otherwise use the value
    const clusterCount = (parsed === 0 || parsed === 1 || isNaN(parsed)) ? null : Math.min(20, Math.max(2, parsed))
    const smallestClusterSize = Math.max(2, parseInt(minClusterSize, 10) || 2)
    const options = {
      method,
      n_clusters: method === 'kmeans' ? clusterCount : null,
      min_cluster_size: method === 'hdbscan' ? smallestClusterSize : undefined
    }
    dispatch(runClustering({ texts, options }))
  }, [dispatch, texts, method, nClusters, minClusterSize])

  const handleClear = useCallback(() => {
    dispatch(setInputText(''))
  }, [dispatch])

  const handleSampleData = useCallback(() => {
    dispatch(loadSampleTexts(sampleCount))
  }, [dispatch, sampleCount])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleAddText()
    }
  }, [handleAddText])

  const handleClusterCountBlur = useCallback(() => {
    // Keep 0 and 1 as-is (they mean auto-detect), otherwise clamp to 2-20
    const parsed = parseInt(nClusters, 10)
    if (parsed === 0 || parsed === 1 || isNaN(parsed)) {
      return // leave as-is
    }
    setNClusters(String(Math.min(20, Math.max(2, parsed))))
  }, [nClusters])

  const handleSmallestClusterSizeBlur = useCallback(() => {
    setMinClusterSize(String(Math.max(2, parseInt(minClusterSize, 10) || 2)))
  }, [minClusterSize])

  const isLoading = status === 'loading'
  const canRun = texts.length >= 4

  // Pagination info for virtual list
  const virtualItems = virtualizer.getVirtualItems()
  const startIndex = virtualItems.length > 0 ? virtualItems[0].startIndex : 0
  const endIndex = virtualItems.length > 0 ? virtualItems[virtualItems.length - 1].endIndex : 0

  return (
    <div className="flex flex-col h-full">
      <div className="hidden md:block mb-4">
        <h2 className="panel-header">Input Text</h2>
      </div>

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Text list view — virtualized */}
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden rounded-lg bg-white mb-3 border border-gray-200">
          {texts.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400 text-sm px-6 py-12">
              <IconText className="w-10 h-10 text-gray-300 mb-3" />
              <p className="font-medium text-gray-500">No texts added yet</p>
              <p className="text-xs text-gray-400 mt-1 text-center">
                Type a sentence below and press Enter, or load sample data
              </p>
            </div>
          ) : (
            <>
              {/* Scrollable virtual list */}
              <div
                ref={listContainerRef}
                className="flex-1 overflow-y-auto scrollbar-thin"
                style={{ contain: 'strict' }}
              >
                <div
                  style={{
                    height: virtualizer.getTotalSize(),
                    width: '100%',
                    position: 'relative',
                  }}
                >
                  {virtualItems.map((virtualRow) => {
                    const text = texts[virtualRow.index]
                    return (
                      <div
                        key={virtualRow.key}
                        className="list-row group absolute left-0 right-0 flex items-center"
                        style={{
                          top: virtualRow.start,
                          height: ITEM_HEIGHT,
                        }}
                      >
                        <span className="text-xs text-gray-400 mt-0.5 w-6 text-right flex-shrink-0 font-mono tabular-nums px-1">
                          {virtualRow.index + 1}
                        </span>
                        <span className="text-sm text-gray-700 flex-1 break-words px-1">
                          {text}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveText(virtualRow.index)}
                          className="text-gray-400 hover:text-red-500 active:text-red-600 transition-colors flex-shrink-0 -mr-1 p-1 touch-target md:opacity-0 md:group-hover:opacity-100"
                          disabled={isLoading}
                          aria-label={`Remove text ${virtualRow.index + 1}`}
                        >
                          <IconClose className="w-4 h-4" />
                        </button>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Virtual scroll position indicator */}
              {texts.length > 0 && (
                <div className="flex items-center justify-between text-xs text-gray-500 px-3 py-1.5 border-t border-gray-100 bg-gray-50">
                  <span className="font-semibold text-gray-700 tabular-nums">
                    {texts.length.toLocaleString()}
                  </span>
                  <span className="text-gray-400">
                    {texts.length > 30
                      ? `Showing ${startIndex + 1}–${endIndex + 1} of ${texts.length.toLocaleString()}`
                      : `${texts.length} ${texts.length === 1 ? 'text' : 'texts'}`}
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Add new text input */}
        <div className="flex gap-2 mb-3">
          <input
            ref={inputRef}
            type="text"
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add a sentence..."
            className="input-field text-sm"
            disabled={isLoading}
            enterKeyHint="done"
          />
          <button
            type="button"
            onClick={handleAddText}
            className="btn-secondary text-sm flex-shrink-0"
            disabled={isLoading || !newText.trim()}
            aria-label="Add text"
          >
            <IconPlus className="w-4 h-4" />
            <span className="hidden sm:inline">Add</span>
          </button>
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500 mb-3 px-1">
          <span>
            <span className="font-semibold text-gray-700 tabular-nums">{texts.length.toLocaleString()}</span>{' '}
            {texts.length === 1 ? 'text' : 'texts'} added
          </span>
          <button
            type="button"
            onClick={handleClear}
            className="text-red-500 hover:text-red-600 active:text-red-700 disabled:opacity-50 font-medium py-2 px-2 -mr-2"
            disabled={isLoading || texts.length === 0}
          >
            Clear all
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg animate-scale-in">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Clustering Options */}
      <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
        >
          <span className="flex items-center gap-2">
            <IconSparkles className="w-4 h-4 text-primary-500" />
            Clustering Options
          </span>
          <IconChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} />
        </button>

        {showAdvanced && (
          <div className="mt-3 space-y-3">
            {/* Cluster count selection */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Cluster count</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setMethod('hdbscan')}
                  className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-colors ${
                    method === 'hdbscan'
                      ? 'bg-primary-50 border-primary-300 text-primary-700 font-medium'
                      : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                  }`}
                >
                  Auto choose
                </button>
                <button
                  type="button"
                  onClick={() => setMethod('kmeans')}
                  className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-colors ${
                    method === 'kmeans'
                      ? 'bg-primary-50 border-primary-300 text-primary-700 font-medium'
                      : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                  }`}
                >
                  Choose number
                </button>
              </div>
              <p className="mt-1.5 text-xs text-gray-500 flex items-start gap-1">
                <IconInfo className="w-3 h-3 flex-shrink-0 mt-0.5" />
                {method === 'hdbscan'
                  ? 'Automatically estimates a suitable number of clusters.'
                  : 'Set 0 or 1 to auto-detect, or 2-20 to specify exact count.'}
              </p>
            </div>

            {/* Manual: Number of Clusters */}
            {method === 'kmeans' && (
              <div>
                <label htmlFor="n-clusters" className="block text-xs font-medium text-gray-600 mb-1.5">
                  Number of clusters
                </label>
                <input
                  id="n-clusters"
                  type="number"
                  min={0}
                  max={20}
                  value={nClusters}
                  onChange={(e) => setNClusters(e.target.value)}
                  onBlur={handleClusterCountBlur}
                  placeholder="0 = auto"
                  className="w-24 px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <span className="ml-2 text-xs text-gray-500">0 or 1 = auto-detect, 2-20 = exact</span>
              </div>
            )}

            {/* Auto choose: Min cluster size */}
            {method === 'hdbscan' && (
              <div>
                <label htmlFor="min-cluster-size" className="block text-xs font-medium text-gray-600 mb-1.5">
                  Smallest cluster size
                </label>
                <input
                  id="min-cluster-size"
                  type="number"
                  min={2}
                  max={20}
                  value={minClusterSize}
                  onChange={(e) => setMinClusterSize(e.target.value)}
                  onBlur={handleSmallestClusterSizeBlur}
                  className="w-24 px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <span className="ml-2 text-xs text-gray-500">minimum (2-20)</span>
                <p className="mt-1 text-xs text-gray-400">
                  Remark: smaller values can create more clusters; larger values create fewer, broader clusters.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <button
          type="button"
          onClick={handleRunClustering}
          disabled={isLoading || !canRun}
          className="btn-primary w-full"
        >
          {isLoading ? (
            <>
              <IconSpinner className="w-4 h-4 animate-spin" />
              <span>Processing…</span>
            </>
          ) : (
            <>
              <IconBolt className="w-4 h-4" />
              <span>Run Clustering</span>
            </>
          )}
        </button>

        {/* Sample data — count selector + load button */}
        <div className="flex gap-2">
          <select
            value={sampleCount}
            onChange={(e) => setSampleCount(Number(e.target.value))}
            disabled={isLoading}
            className="px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-700 flex-shrink-0"
            aria-label="Sample data count"
          >
            {SAMPLE_COUNTS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleSampleData}
            className="btn-secondary flex-1"
            disabled={isLoading}
          >
            <IconSparkles className="w-4 h-4" />
            <span>Load Sample Data</span>
          </button>
        </div>
      </div>

      <details className="mt-4 pt-4 border-t border-gray-200 group">
        <summary className="text-xs font-medium text-gray-600 flex items-center gap-1.5 cursor-pointer list-none touch-target -mx-2 px-2 py-1 rounded hover:bg-gray-50">
          <IconInfo className="w-3.5 h-3.5 text-gray-400" />
          <span>Tips</span>
          <span className="ml-auto text-gray-400 group-open:rotate-90 transition-transform">›</span>
        </summary>
        <ul className="text-xs text-gray-500 space-y-1.5 mt-3 pl-1">
          <li className="flex items-start gap-2">
            <span className="text-primary-500 font-mono tabular-nums w-3 flex-shrink-0">1</span>
            Add one sentence per text line
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-500 font-mono tabular-nums w-3 flex-shrink-0">2</span>
            Need at least 4 texts to cluster
          </li>
          <li className="flex items-start gap-2">
            <span className="text-primary-500 font-mono tabular-nums w-3 flex-shrink-0">3</span>
            Similar texts group together automatically
          </li>
        </ul>
      </details>
    </div>
  )
}

export default InputPanel
