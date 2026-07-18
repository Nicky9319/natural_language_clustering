import { configureStore } from '@reduxjs/toolkit'
import clusterReducer from './clusterSlice'

export const store = configureStore({
  reducer: {
    cluster: clusterReducer,
  },
})
