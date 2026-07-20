import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import axios from 'axios'
import { clusterApi } from '../api/clusterApi'

const API_URL = '/api/cluster'

export const runClustering = createAsyncThunk(
  'cluster/runClustering',
  async ({ texts, options = {} }, { rejectWithValue }) => {
    try {
      const { n_clusters = null, method = 'kmeans', min_cluster_size } = options
      const payload = { texts, n_clusters, method }
      if (method === 'hdbscan' && min_cluster_size !== undefined) {
        payload.min_cluster_size = min_cluster_size
      }
      const response = await axios.post(API_URL, payload)
      return response.data
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || error.message || 'Failed to run clustering'
      )
    }
  }
)

export const loadSampleTexts = createAsyncThunk(
  'cluster/loadSampleTexts',
  async (count = 100, { rejectWithValue }) => {
    try {
      const response = await clusterApi.getSampleTexts(count)
      return response.texts
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.detail || error.message || 'Failed to load sample texts'
      )
    }
  }
)

const initialState = {
  status: 'idle',
  inputText: '',
  clusters: [],
  points: [],
  stats: null,
  selectedCluster: null,
  selectedPoint: null,
  error: null
}

const clusterSlice = createSlice({
  name: 'cluster',
  initialState,
  reducers: {
    setInputText: (state, action) => {
      state.inputText = action.payload
    },
    setSelectedCluster: (state, action) => {
      state.selectedCluster = action.payload
      state.selectedPoint = null
    },
    setSelectedPoint: (state, action) => {
      state.selectedPoint = action.payload
      state.selectedCluster = null
    },
    clearSelectedCluster: (state) => {
      state.selectedCluster = null
      state.selectedPoint = null
    },
    resetState: (state) => {
      state.status = 'idle'
      state.clusters = []
      state.points = []
      state.stats = null
      state.selectedCluster = null
      state.selectedPoint = null
      state.error = null
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(runClustering.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(runClustering.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.clusters = action.payload.clusters
        state.points = action.payload.points
        state.stats = action.payload.stats
        state.selectedCluster = null
        state.selectedPoint = null
        state.error = null
      })
      .addCase(runClustering.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.payload
      })
      .addCase(loadSampleTexts.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(loadSampleTexts.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.inputText = action.payload.join('\n')
        state.error = null
      })
      .addCase(loadSampleTexts.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.payload
      })
  }
})

export const {
  setInputText,
  setSelectedCluster,
  setSelectedPoint,
  clearSelectedCluster,
  resetState
} = clusterSlice.actions

export default clusterSlice.reducer
