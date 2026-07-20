import { useMemo, useCallback, useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import createPlotlyComponent from 'react-plotly.js/factory'
import Plotly from 'plotly.js-dist-min'
import { setSelectedCluster, setSelectedPoint } from '../store/clusterSlice'

const Plot = createPlotlyComponent(Plotly)

function ClusterChart() {
  const dispatch = useDispatch()
  const { clusters, points, selectedCluster, selectedPoint } = useSelector((state) => state.cluster)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)')
    const onChange = () => setIsMobile(mq.matches)
    onChange()
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  const plotData = useMemo(() => {
    // Dynamic marker sizing based on total point count
    const totalPoints = points.length
    const markerSize = totalPoints >= 5000 ? 3 : totalPoints >= 1000 ? 4 : isMobile ? 10 : 8
    const markerOpacity = totalPoints >= 5000 ? 0.6 : totalPoints >= 1000 ? 0.7 : 0.8

    const traces = clusters.map(cluster => {
      const clusterPoints = points.filter(p => p.cluster === cluster.id)
      return {
        x: clusterPoints.map(p => p.x),
        y: clusterPoints.map(p => p.y),
        text: clusterPoints.map(p => p.text),
        confidence: clusterPoints.map(p => p.confidence),
        cluster: clusterPoints.map(p => p.cluster),
        type: 'scatter',
        mode: 'markers',
        name: `${cluster.name} (${cluster.size})`,
        marker: {
          color: cluster.color,
          size: markerSize,
          opacity: markerOpacity,
          line: {
            color: selectedCluster === cluster.id ? '#1f2937' : 'transparent',
            width: selectedCluster === cluster.id ? 2 : 0
          }
        },
        hovertemplate: `<b>%{text}</b><br>` +
          `Cluster: ${cluster.name}${cluster.description ? `<br>${cluster.description}` : ''}<br>` +
          `Confidence: %{customdata:.2f}<br>` +
          `<extra></extra>`,
        customdata: clusterPoints.map(p => p.confidence)
      }
    })
    return traces
  }, [clusters, points, selectedCluster, isMobile])

  const layout = useMemo(() => ({
    paper_bgcolor: '#f9fafb',
    plot_bgcolor: '#f9fafb',
    font: {
      family: 'Inter, system-ui, sans-serif',
      size: isMobile ? 11 : 12,
      color: '#374151'
    },
    title: {
      text: '',
      font: {
        size: 16,
        color: '#111827'
      }
    },
    xaxis: {
      title: {
        text: isMobile ? '' : 'Dimension 1',
        font: { size: 12, color: '#6b7280' }
      },
      showgrid: true,
      gridcolor: '#e5e7eb',
      zerolinecolor: '#d1d5db',
      zerolinewidth: 1
    },
    yaxis: {
      title: {
        text: isMobile ? '' : 'Dimension 2',
        font: { size: 12, color: '#6b7280' }
      },
      showgrid: true,
      gridcolor: '#e5e7eb',
      zerolinecolor: '#d1d5db',
      zerolinewidth: 1
    },
    legend: {
      orientation: 'h',
      x: 0.5,
      xanchor: 'center',
      y: -0.15,
      bgcolor: 'rgba(255,255,255,0.8)',
      bordercolor: '#e5e7eb',
      borderwidth: 1,
      borderradius: 4,
      itemclick: 'toggle',
      itemdoubleclick: 'toggleothers',
      font: { size: isMobile ? 10 : 12 }
    },
    margin: isMobile
      ? { l: 30, r: 16, t: 16, b: 70 }
      : { l: 50, r: 30, t: 30, b: 60 },
    hovermode: 'closest',
    showlegend: true
  }), [isMobile])

  const config = useMemo(() => ({
    displayModeBar: !isMobile,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    displaylogo: false,
    responsive: true,
    scrollZoom: !isMobile,
    doubleClick: isMobile ? 'reset' : 'autosize',
  }), [isMobile])

  const handlePlotClick = useCallback((event) => {
    if (event.points && event.points.length > 0) {
      const point = event.points[0]
      const trace = point.data
      dispatch(setSelectedPoint({
        x: point.x,
        y: point.y,
        text: trace.text[point.pointIndex],
        confidence: trace.customdata[point.pointIndex],
        cluster: trace.cluster[point.pointIndex]
      }))
    }
  }, [dispatch])

  const handlePlotSelected = useCallback((event) => {
    if (event && event.points && event.points.length > 0) {
      const selectedClusterId = event.points[0].data.cluster[event.points[0].pointIndex]
      dispatch(setSelectedCluster(selectedClusterId))
    }
  }, [dispatch])

  return (
    <div className="h-full w-full">
      <Plot
        data={plotData}
        layout={layout}
        config={config}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
        onClick={handlePlotClick}
        onSelected={handlePlotSelected}
      />
    </div>
  )
}

export default ClusterChart