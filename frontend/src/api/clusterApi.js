import axios from 'axios'

const API_URL = '/api/cluster'

export const clusterApi = {
  runClustering: async (texts, options = {}) => {
    const { n_clusters = null, method = 'kmeans', min_cluster_size } = options

    const payload = { texts, n_clusters, method }

    if (method === 'hdbscan' && min_cluster_size !== undefined) {
      payload.min_cluster_size = min_cluster_size
    }

    const response = await axios.post(API_URL, payload)
    return response.data
  },

  getSampleTexts: async (count = 100) => {
    const response = await axios.get(`${API_URL.replace('/cluster', '/sample')}?count=${count}`)
    return response.data
  }
}

export default clusterApi
