FROM mambaorg/micromamba:1.5.10

WORKDIR /app

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /home/$MAMBA_USER/.cache/huggingface /home/$MAMBA_USER/.cache/pip \
    && chown -R $MAMBA_USER:$MAMBA_USER /home/$MAMBA_USER/.cache

USER $MAMBA_USER
ENV PIP_CACHE_DIR=/home/$MAMBA_USER/.cache/pip

COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt .

# HDBSCAN is installed from conda-forge to avoid slow source builds.
RUN --mount=type=cache,target=/opt/conda/pkgs,uid=57439,gid=57439 \
    micromamba install -y -n base -c conda-forge \
      python=3.11 \
      pip \
      numpy=1.26.3 \
      scikit-learn=1.4.0 \
      hdbscan \
    && micromamba clean --all --yes

RUN --mount=type=cache,target=/home/$MAMBA_USER/.cache/pip,uid=57439,gid=57439 \
    /opt/conda/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.1.2+cpu \
    && grep -Ev '^(hdbscan|numpy|scikit-learn)==' requirements.txt > /tmp/requirements-docker.txt \
    && /opt/conda/bin/pip install -r /tmp/requirements-docker.txt

ENV PATH=/opt/conda/bin:$PATH \
    LD_LIBRARY_PATH=/opt/conda/lib \
    HF_HOME=/home/$MAMBA_USER/.cache/huggingface

# Keep image rebuilds fast by default. Enable this only when you explicitly want
# the large embedding model baked into the image:
# docker compose build --build-arg PRELOAD_MODEL=true backend
ARG PRELOAD_MODEL=false
ARG EMBEDDING_MODEL=BAAI/bge-m3
RUN --mount=type=cache,target=/home/$MAMBA_USER/.cache/huggingface,uid=57439,gid=57439 \
    if [ "$PRELOAD_MODEL" = "true" ]; then \
      /opt/conda/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('$EMBEDDING_MODEL', device='cpu')"; \
    fi

COPY --chown=$MAMBA_USER:$MAMBA_USER . .

EXPOSE 5000

CMD ["/opt/conda/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--timeout-keep-alive", "300"]
