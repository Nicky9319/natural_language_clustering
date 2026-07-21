import { useCallback, useState, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { setInputText, runClustering, loadSampleTexts } from '../store/clusterSlice'
import { IconPlus, IconClose, IconBolt, IconSparkles, IconInfo, IconSpinner, IconText, IconChevronDown } from './icons'
import { useVirtualizer } from '@tanstack/react-virtual'

const SAMPLE_COUNTS = [
  { value: 100, label: '100' },
  { value: 1000, label: '1K' },
  { value: 5000, label: '5K' },
  { value: 10000, label: '10K' },
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
  const [showMethodInfo, setShowMethodInfo] = useState(false)
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
    const parsed = parseInt(nClusters, 10)
    if (parsed === 0 || parsed === 1 || isNaN(parsed)) {
      return
    }
    setNClusters(String(Math.min(20, Math.max(2, parsed))))
  }, [nClusters])

  const handleSmallestClusterSizeBlur = useCallback(() => {
    setMinClusterSize(String(Math.max(2, parseInt(minClusterSize, 10) || 2)))
  }, [minClusterSize])

  const isLoading = status === 'loading'
  const canRun = texts.length >= 4

  const virtualItems = virtualizer.getVirtualItems()
  const startIndex = virtualItems.length > 0 ? virtualItems[0].startIndex : 0
  const endIndex = virtualItems.length > 0 ? virtualItems[virtualItems.length - 1].endIndex : 0

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* ===== STICKY HEADER: sample data + clustering options ===== */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white z-10">
        {/* Sample data row */}
        <div className="px-3 pt-3 pb-2">
          <div className="flex items-center gap-2">
            <select
              value={sampleCount}
              onChange={(e) => setSampleCount(Number(e.target.value))}
              disabled={isLoading}
              className="px-2.5 py-1.5 text-sm border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-700 font-medium flex-shrink-0 cursor-pointer"
              aria-label="Sample data count"
            >
              {SAMPLE_COUNTS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={handleSampleData}
              className="btn-secondary flex-1 text-sm py-2"
              disabled={isLoading}
            >
              <IconSparkles className="w-4 h-4" />
              <span>Load Sample Data</span>
            </button>
          </div>
        </div>

        {/* Clustering options bar */}
        <div className="px-3 pb-3">
          <div className="flex items-center gap-3">
            {/* Method toggle */}
            <div className="flex bg-gray-100 rounded-lg p-0.5 flex-shrink-0">
              <button
                type="button"
                onClick={() => setMethod('hdbscan')}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all duration-150 ${
                  method === 'hdbscan'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Auto
              </button>
              <button
                type="button"
                onClick={() => setMethod('kmeans')}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all duration-150 ${
                  method === 'kmeans'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Manual
              </button>
            </div>

            {/* Method-specific control */}
            {method === 'kmeans' && (
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <label htmlFor="n-clusters" className="text-xs text-gray-500 whitespace-nowrap">Clusters:</label>
                <input
                  id="n-clusters"
                  type="number"
                  min={0}
                  max={20}
                  value={nClusters}
                  onChange={(e) => setNClusters(e.target.value)}
                  onBlur={handleClusterCountBlur}
                  className="w-14 px-2 py-1 text-xs border border-gray-200 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-700"
                />
              </div>
            )}

            {method === 'hdbscan' && (
              <div className="flex items-center gap-1.5 flex-shrink-0">
                <label htmlFor="min-cluster-size" className="text-xs text-gray-500 whitespace-nowrap">Min size:</label>
                <input
                  id="min-cluster-size"
                  type="number"
                  min={2}
                  max={20}
                  value={minClusterSize}
                  onChange={(e) => setMinClusterSize(e.target.value)}
                  onBlur={handleSmallestClusterSizeBlur}
                  className="w-14 px-2 py-1 text-xs border border-gray-200 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-gray-700"
                />
              </div>
            )}

            {/* Info toggle */}
            <button
              type="button"
              onClick={() => setShowMethodInfo(!showMethodInfo)}
              className="ml-auto text-gray-400 hover:text-gray-600 transition-colors p-1"
              aria-label="Toggle method info"
            >
              <IconInfo className="w-4 h-4" />
            </button>
          </div>

          {/* Expanded method info */}
          {showMethodInfo && (
            <div className="mt-2 text-xs text-gray-500 bg-gray-50 rounded-lg px-3 py-2 leading-relaxed">
              {method === 'hdbscan'
                ? 'HDBSCAN automatically finds the optimal number of clusters based on data density. Adjust "Min size" to control how general or specific the clusters are.'
                : 'K-Means lets you specify exactly how many clusters to create. Set to 0 or 1 for auto-detection.'}
            </div>
          )}
        </div>
      </div>

      {/* ===== TEXT LIST (scrollable, takes remaining space) ===== */}
      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {texts.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400 text-sm px-6">
            <IconText className="w-10 h-10 text-gray-300 mb-3" />
            <p className="font-medium text-gray-500">No texts added yet</p>
            <p className="text-xs text-gray-400 mt-1 text-center">
              Load sample data or type sentences below
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
                      className="group absolute left-0 right-0 flex items-center px-3 hover:bg-primary-50 active:bg-primary-100 transition-colors duration-100 border-b border-gray-100 last:border-b-0"
                      style={{
                        top: virtualRow.start,
                        height: ITEM_HEIGHT,
                      }}
                    >
                      <span className="text-xs text-gray-400 w-11 text-right flex-shrink-0 font-mono tabular-nums pr-2">
                        {virtualRow.index + 1}
                      </span>
                      <span
                        className="text-sm text-gray-800 flex-1 min-w-0 truncate font-medium"
                        title={text}
                      >
                        {text}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveText(virtualRow.index)}
                        className="text-gray-300 hover:text-red-500 active:text-red-600 transition-colors flex-shrink-0 p-1 opacity-0 group-hover:opacity-100"
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
            <div className="flex items-center justify-between text-xs text-gray-500 px-3 py-1.5 border-t border-gray-100 bg-gray-50 flex-shrink-0">
              <span className="font-semibold text-gray-700 tabular-nums">
                {texts.length.toLocaleString()}
              </span>
              <span className="text-gray-400">
                {texts.length > 30
                  ? `${startIndex + 1}–${endIndex + 1} of ${texts.length.toLocaleString()}`
                  : `${texts.length} ${texts.length === 1 ? 'text' : 'texts'}`}
              </span>
            </div>
          </>
        )}
      </div>

      {/* ===== ADD TEXT INPUT ===== */}
      <div className="flex-shrink-0 px-3 py-2 border-t border-gray-100 bg-white">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={newText}
            onChange={(e) => setNewText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a sentence and press Enter…"
            className="input-field text-sm flex-1"
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
          </button>
        </div>
      </div>

      {/* ===== STICKY ACTION FOOTER ===== */}
      <div className="flex-shrink-0 px-3 py-3 border-t border-gray-200 bg-white space-y-2">
        {error && (
          <div className="p-2.5 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}

        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={handleClear}
            className="text-xs text-red-500 hover:text-red-600 active:text-red-700 font-medium px-2 py-1.5 rounded-md hover:bg-red-50 transition-colors disabled:opacity-40"
            disabled={isLoading || texts.length === 0}
          >
            Clear all
          </button>

          <button
            type="button"
            onClick={handleRunClustering}
            disabled={isLoading || !canRun}
            className="btn-primary flex-1"
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
        </div>

        <p className="text-xs text-gray-400 text-center leading-relaxed">
          {texts.length < 4
            ? `Add ${4 - texts.length} more ${4 - texts.length === 1 ? 'text' : 'texts'} to cluster`
            : `${texts.length.toLocaleString()} ${texts.length === 1 ? 'text' : 'texts'} ready to cluster`}
        </p>
      </div>
    </div>
  )
}

export default InputPanel
