# Natural Language Clustering

An intelligent semantic text clustering and visualization application that groups similar texts together using state-of-the-art embedding models and clustering algorithms, presented through an interactive 2D visualization.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technologies](#technologies)
- [Clustering Mechanisms](#clustering-mechanisms)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Docker Compose Setup](#docker-compose-setup)
- [Development](#development)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)

---

## Overview

This application performs semantic text clustering by:

1. **Embedding**: Converting text into dense vector representations using the BGE-m3 transformer model
2. **Clustering**: Grouping similar texts using either K-Means or HDBSCAN algorithms
3. **Visualization**: Projecting high-dimensional vectors to 2D using UMAP for interactive visualization
4. **Naming**: Auto-generating descriptive cluster names using Cerebras AI

## Use Case

**AI / LLM Evaluation Output Analysis** — When you ask an LLM to evaluate a dataset (customer conversations, survey responses, support tickets, product reviews, or any collection of text), it returns rich qualitative feedback. This tool clusters that feedback to surface patterns, themes, and actionable insights:

- **Understand large volumes of LLM analysis at a glance** — instead of reading hundreds of individual responses, see thematic clusters emerge naturally
- **Derive numerical insights from qualitative data** — quantify how responses group together (e.g., "40% of LLM responses flagged billing concerns, 25% mentioned shipping delays")
- **Visualize the data landscape** — see how topics relate spatially through the 2D UMAP projection
- **Get AI-generated cluster names** — Cerebras automatically names each cluster, saving manual labeling effort
- **Drive actionable decisions** — identify the largest or most critical cluster and prioritize accordingly

In short, this tool bridges **qualitative LLM outputs** and **quantitative business decisions** — turning unstructured text evaluation into structured, visual insight that teams can act on.

---

## Architecture

**Single-container deployment**: The React frontend is built and served directly by the FastAPI backend on port 5000. All static assets (`/`, `/cluster`, etc.) are served from the backend, while API routes (`/api/*`) handle clustering logic.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'primaryTextColor': '#e6edf3', 'lineColor': '#8b949e' }} }%%
flowchart TB
    subgraph App["App Container (FastAPI + React) - Port 5000"]
        A[Static Files<br/>React Build] --> B[FastAPI Backend]
        B --> C["API Routes<br/>/api/cluster, /api/sample, /health"]
        C --> D[Embedder Service]
        C --> E[Clusterer Service]
        C --> F[Namer Service]

        D -->|BGE-m3| G[1024-dim Vectors]
        E -->|K-Means or HDBSCAN| H[Cluster Labels]
        F -->|Cerebras AI| I[Cluster Names]
    end

    style App fill:#1f3a5f,stroke:#58a6ff,color:#e6edf3
    style D fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style E fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style F fill:#1f4a32,stroke:#7ee787,color:#e6edf3
```

### Data Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'secondaryColor': '#7ee787', 'lineColor': '#8b949e', 'tertiaryColor': '#d29922' }} }%%
flowchart LR
    A["User Input<br/>Texts"] --> B["1. Embedding<br/>BGE-m3 Model"]
    B --> C["1024-dim<br/>Vectors"]
    C --> D["2. Clustering<br/>K-Means or HDBSCAN"]
    D --> E["Cluster<br/>Labels"]
    E --> F["3. UMAP<br/>Projection"]
    F --> G["2D<br/>Coordinates"]
    G --> H["4. Normalization<br/>MinMaxScaler"]
    H --> I["[0, 1]<br/>Normalized"]
    I --> J["5. Cluster Naming<br/>Google Gemini AI"]
    J --> K["Descriptive<br/>Names"]
    K --> L["Visualization<br/>Data"]

    style B fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style D fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style F fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style H fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style J fill:#1f4a32,stroke:#7ee787,color:#e6edf3
```

---

## Technologies

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.109.0 | Async web framework |
| **Uvicorn** | 0.27.0 | ASGI server |
| **sentence-transformers** | 2.3.1 | Text embedding generation |
| **transformers** | 4.36.2 | HuggingFace transformer models |
| **huggingface-hub** | 0.20.3 | Model caching and downloading |
| **PyTorch** | CPU | Deep learning tensor operations |
| **scikit-learn** | 1.4.0 | K-Means clustering, silhouette scoring |
| **UMAP** | 0.5.5 | Dimensionality reduction |
| **HDBSCAN** | 0.8.1 | Density-based clustering |
| **Google Generative AI** | 0.8.5 | AI-powered cluster naming |
| **NumPy** | 1.26.3 | Numerical computations |
| **Pandas** | 2.2.0 | Data manipulation |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.2.0 | UI framework |
| **Redux Toolkit** | 1.9.5 | State management |
| **Plotly.js** | 2.26.0 | Interactive visualization |
| **react-plotly.js** | 2.6.0 | React bindings for Plotly |
| **Axios** | 1.5.0 | HTTP client |
| **Vite** | 5.0.0 | Build tool and dev server |
| **TailwindCSS** | 3.3.5 | CSS framework |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Single-container orchestration |
| **Micromamba** | Fast conda environment management |
| **Node.js** | Frontend build (bundled in backend container) |

---

## Clustering Mechanisms

### 1. Embedding Model: BGE-m3

**Model**: `BAAI/bge-m3` (State-of-the-art multilingual embedding model)

- **Dimensionality**: 1024 dimensions
- **Normalization**: L2 normalization (cosine similarity compatibility)
- **Loading**: Lazy loading on first request (or preloaded with `PRELOAD_EMBEDDING_MODEL=true`)
- **Pattern**: Singleton - model is loaded once and reused across requests

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'lineColor': '#8b949e' }} }%%
flowchart LR
    A["Input Text"] --> B["Tokenizer"]
    B --> C["Transformer<br/>BGE-m3"]
    C --> D["1024-dim<br/>Embedding"]
    D --> E["L2<br/>Normalize"]
    E --> F["Normalized<br/>Vector"]

    style C fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style E fill:#1f3a5f,stroke:#58a6ff,color:#e6edf3
```

### 2. K-Means Clustering

**Algorithm**: Lloyd's K-Means with scikit-learn implementation

**Optimal K Selection**:
- Searches range `k_min=5` to `k_max=15` (configurable)
- Uses **Silhouette Score** to find optimal K
- Silhouette score measures how similar texts are to their own cluster vs other clusters
- Range: -1 to 1 (higher = better defined clusters)

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'lineColor': '#8b949e', 'tertiaryColor': '#d29922' }} }%%
flowchart TD
    A["Embeddings<br/>[N x 1024]"] --> B["Search K: 5 to 15"]
    B --> C{"Calculate<br/>Silhouette Score"}
    C --> D["Select Best K"]
    D --> E["K-Means<br/>with Optimal K"]
    E --> F["Cluster Labels<br/>[N x 1]"]
    F --> G["Cluster Centers<br/>[K x 1024]"]
    G --> H["Calculate<br/>Confidence"]
    H --> I["1 / (1 + distance)"]

    style C fill:#3d2e1f,stroke:#d29922,color:#e6edf3
    style E fill:#1f4a32,stroke:#7ee787,color:#e6edf3
```

### 3. HDBSCAN Clustering

**Algorithm**: Hierarchical Density-Based Spatial Clustering of Applications with Noise

**Advantages over K-Means**:
- Automatic cluster detection (no need to specify K)
- Identifies noise points (label = -1)
- Handles clusters of varying densities and shapes

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'lineColor': '#8b949e', 'tertiaryColor': '#d29922' }} }%%
flowchart TD
    A["Embeddings<br/>[N x 1024]"] --> B["Build Density<br/>Hierarchy"]
    B --> C["Condensed<br/>Tree"]
    C --> D["Extract<br/>Clusters"]
    D --> E{"Noise<br/>Points?"}
    E -->|Yes| F["Label = -1<br/>Unclustered"]
    E -->|No| G["Cluster<br/>Membership"]
    F --> H["Confidence =<br/>membership_prob"]
    G --> H
    H --> I["Cluster Labels<br/>& Probabilities"]

    style E fill:#3d2020,stroke:#f85149,color:#e6edf3
    style G fill:#1f4a32,stroke:#7ee787,color:#e6edf3
```

**Noise Handling**:
- Points labeled -1 are grouped into "Unclustered" pseudo-cluster
- Displayed separately in visualization

### 4. UMAP Dimensionality Reduction

**Purpose**: Project 1024-dimensional embeddings to 2D for visualization

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'lineColor': '#8b949e', 'tertiaryColor': '#d29922' }} }%%
flowchart LR
    A["1024-dim<br/>Embeddings"] --> B["UMAP"]
    B --> C["Nearest<br/>Neighbors Graph"]
    C --> D["Fuzzy Topological<br/>Simplification"]
    D --> E["2D<br/>Projection"]

    subgraph Config["UMAP Configuration"]
        F["n_neighbors=15"]
        G["min_dist=0.1"]
        H["metric=cosine"]
    end

    B --> Config

    style B fill:#1f4a32,stroke:#7ee787,color:#e6edf3
    style Config fill:#2d333b,stroke:#8b949e,color:#e6edf3
```

### 5. Cluster Naming (Google Gemini AI)

**Model**: `gemini-3.5-flash-lite` via Google AI (configurable in `backend/config.json`)

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'lineColor': '#8b949e', 'tertiaryColor': '#d29922', 'noteBkgColor': '#2d333b', 'noteTextColor': '#e6edf3' }} }%%
sequenceDiagram
    participant BE as Backend
    participant Cerebras as Cerebras API

    BE->>BE: Sample up to 5 texts<br/>per cluster (100 chars each)
    BE->>Cerebras: POST /chat/completions
    Note over Cerebras: Prompt: "You are a data analyst...<br/>Samples: text1, text2..."
    Cerebras-->>BE: Response with<br/>cluster name
    BE->>BE: Extract name from<br/>response
    alt LLM Available
        BE->>BE: Use AI-generated name
    else LLM Unavailable
        BE->>BE: Fallback to "Cluster 1, 2, 3..."
    end
```

---

## Project Structure

```
natural_language_clustering/
├── docker-compose.yml           # Docker orchestration (single container)
├── README.md                   # This file
├── AGENTS.md                   # Agent instructions
│
├── backend/
│   ├── Dockerfile              # Backend container (builds + serves frontend)
│   ├── config.json            # Model configuration (embedding + LLM)
│   ├── requirements.txt        # Python dependencies
│   ├── .env                   # Environment variables (GOOGLE_API_KEY)
│   └── app/
│       ├── main.py            # FastAPI app + static file serving
│       ├── static/            # Built React frontend (generated at build time)
│       ├── models/
│       │   └── schemas.py     # Pydantic request/response models
│       ├── routes/
│       │   └── cluster.py     # API endpoints
│       └── services/
│           ├── embedder.py     # BGE-m3 embedding service
│           ├── clusterer.py    # K-Means/HDBSCAN + UMAP
│           └── namer.py        # Cerebras AI cluster naming
│
└── frontend/
    ├── package.json           # Node dependencies
    ├── pnpm-lock.yaml        # pnpm lock file
    ├── vite.config.js        # Vite config
    ├── tailwind.config.js    # Tailwind CSS config
    ├── index.html             # HTML entry point
    └── src/
        ├── App.jsx            # Main React component
        ├── main.jsx           # React entry point
        ├── index.css          # Global styles
        ├── api/
        │   └── clusterApi.js  # API client
        ├── store/
        │   ├── index.js       # Redux store config
        │   └── clusterSlice.js # Redux state management
        └── components/
            ├── ClusterChart.jsx    # Plotly visualization
            ├── InputPanel.jsx      # Text input + options
            ├── PropertiesPanel.jsx # Cluster details + stats
            ├── MobileTabBar.jsx    # Mobile navigation
            ├── BottomSheet.jsx     # Mobile bottom sheet
            └── icons.jsx           # SVG icons
```

---

## Configuration

### Single Container Architecture

The frontend is built during the Docker image build and served as static files by FastAPI.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#58a6ff', 'lineColor': '#8b949e', 'tertiaryColor': '#d29922' }} }%%
flowchart LR
    subgraph DockerHost["Docker Host"]
        subgraph AppContainer["app container (FastAPI + React)"]
            B[FastAPI<br/>Port 5000<br/>Serves React build] --> C[HuggingFace<br/>Cache Volume]
            B --> D[Static Files<br/>/app/app/static]
        end
    end

    User([User Browser]) -->|Port 5000| B

    C -.->|Persist models| HV[HuggingFace<br/>Cache Volume]

    style DockerHost fill:#161b22,stroke:#30363d,color:#e6edf3
    style AppContainer fill:#1f3a5f,stroke:#58a6ff,color:#e6edf3
    style HV fill:#2d333b,stroke:#8b949e,color:#e6edf3
```

### App Service

| Setting | Value | Description |
|---------|-------|-------------|
| Build Context | `.` | Root project directory |
| Dockerfile | `backend/Dockerfile` | Multi-stage build (Python + Node.js) |
| Container Name | `app` | Docker container name |
| Port | `5000:5000` | Host:Container port mapping |
| Environment File | `./backend/.env` | CEREBRAS_API_KEY |
| Volume | `backend-huggingface-cache:/home/mambauser/.cache/huggingface` | Model cache persistence |
| Health Check | `GET /health` | Container health verification |

### Docker Volumes

| Volume | Purpose | Persistence |
|--------|---------|-------------|
| `backend-huggingface-cache` | HuggingFace model cache | Persists across restarts |

**Benefit**: After initial model download, subsequent starts are faster as models are cached.

### Environment Variables

#### Backend (.env)

```bash
# Required - Get from https://console.cerebras.ai (or Google AI from https://aistudio.google.com)
GOOGLE_API_KEY=your_google_api_key_here

# Optional
PRELOAD_EMBEDDING_MODEL=false  # Set to true to load model at container start
```

#### Backend (config.json)

Model configuration is in `backend/config.json`:

```json
{
  "embedding_model": {
    "name": "BAAI/bge-m3"
  },
  "llm_model": {
    "provider": "google",
    "name": "gemini-3.5-flash-lite",
    "fallback_name": "gemini-3.5-flash-lite"
  }
}
```

---

## Docker Compose Setup

### Prerequisites

1. **Docker** installed (version 20.10+)
2. **Docker Compose** installed (version 2.0+)
3. **Google AI API Key** from [aistudio.google.com](https://aistudio.google.com) (or Cerebras from [console.cerebras.ai](https://console.cerebras.ai))

### Quick Start

**Step 1: Clone and navigate to project**

```bash
cd /home/paarth/workspace/natural-language-classification/natural_language_clustering
```

**Step 2: Configure API Key**

Edit `backend/.env`:

```bash
CEREBRAS_API_KEY=your_actual_cerebras_api_key_here
```

**Step 3: Build and start the container**

```bash
docker compose build --no-cache
docker compose up -d
```

**Step 4: Verify the service**

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Health check
curl http://localhost:5000/health
```

**Step 5: Access the application**

Open your browser to: **http://localhost:5000**

### Docker Compose Commands

| Command | Description |
|---------|-------------|
| `docker compose up -d` | Start container in detached mode |
| `docker compose down` | Stop and remove container |
| `docker compose logs -f` | Follow logs |
| `docker compose logs -f` | Follow app logs |
| `docker compose restart` | Restart the container |
| `docker compose build --no-cache` | Rebuild without cache |
| `docker compose exec app sh` | Shell into app container |
| `docker compose ps` | Show container status |
| `docker compose top` | Show running processes |

### Troubleshooting

#### Container fails to start

```bash
# Check logs
docker compose logs

# Verify .env exists
cat backend/.env
```

#### Model download takes too long

Models are downloaded on first clustering request. To pre-download during build:

```bash
# In backend/Dockerfile, set:
ARG PRELOAD_EMBEDDING_MODEL=true
```

Or manually trigger download:
```bash
docker compose exec app python -c "from app.services.embedder import embedder; embedder.load_model()"
```

#### Port conflicts

If port 5000 is in use:

```yaml
# In docker-compose.yml, change:
ports:
  - "5001:5000"  # App now on 5001
```

#### Out of memory

If running low on memory (model is ~2GB):

```bash
# Set model to not preload
# In backend/.env:
PRELOAD_EMBEDDING_MODEL=false
```

### Production Deployment Considerations

1. **Use production-grade API keys** - Not the development key
2. **Enable CORS restrictions** - Currently allows all origins in development
3. **Add reverse proxy** (nginx) for HTTPS termination
4. **Set resource limits** in docker-compose:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G
   ```
5. **Consider GPU acceleration** for embedding (add `--gpus all` to docker compose run)

---

## Development

### Local Development (Without Docker)

**Backend:**

```bash
cd backend
pip install -r requirements.txt
export CEREBRAS_API_KEY=your_api_key
uvicorn app.main:app --reload --port 5000
```

**Frontend (for live reload):**

```bash
cd frontend
pnpm install
pnpm run dev
```

**Note**: In local dev, Vite proxies `/api` to `localhost:5000`.

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Adding New Clustering Algorithms

To add a new clustering method (e.g., DBSCAN):

1. **Update `clusterer.py`**:
   ```python
   def cluster_dbscan(self, embeddings, eps=0.5, min_samples=5):
       from sklearn.cluster import DBSCAN
       clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
       labels = clustering.fit_predict(embeddings)
       return labels
   ```

2. **Update `schemas.py`** - Add new method to `ClusterMethod` enum

3. **Update `cluster.py`** - Add case for new method in clustering endpoint

---

## API Reference

### POST /api/cluster

Cluster texts and return visualization data.

**Request:**

```json
{
  "texts": [
    "error connecting to database",
    "the cat sat on the mat",
    "database timeout issue",
    "shipping delay notification"
  ],
  "method": "kmeans",
  "n_clusters": 2,
  "min_cluster_size": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `texts` | string[] | Yes | List of texts to cluster (min: 4) |
| `method` | string | No | `"kmeans"` or `"hdbscan"` (default: kmeans) |
| `n_clusters` | number | No | Number of clusters for kmeans (5-15 auto, or 1-N manual) |
| `min_cluster_size` | number | No | Min cluster size for hdbscan (default: 5) |

**Response:**

```json
{
  "clusters": [
    {
      "id": "0",
      "name": "Database Issues",
      "size": 2,
      "color": "#3b82f6"
    },
    {
      "id": "1",
      "name": "General",
      "size": 2,
      "color": "#22c55e"
    }
  ],
  "points": [
    {
      "x": 0.25,
      "y": 0.75,
      "cluster": "0",
      "confidence": 0.92,
      "text": "error connecting to database"
    }
  ],
  "stats": {
    "total_points": 4,
    "num_clusters": 2,
    "silhouette_score": 0.85
  }
}
```

### GET /api/sample

Fetch 100 sample texts for demo.

**Response:**

```json
{
  "texts": [
    "text 1...",
    "text 2...",
    "..."
  ]
}
```

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "cerebras_available": true
}
```

---

## Environment Variables

### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CEREBRAS_API_KEY` | Yes | - | API key from console.cerebras.ai |
| `PRELOAD_EMBEDDING_MODEL` | No | `false` | Load model at startup |

### Frontend (docker-compose.yml)

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://backend:5000` | Backend API URL (Docker network) |

---

## License

MIT
