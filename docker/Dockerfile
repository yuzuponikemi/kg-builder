FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy dependency files
COPY requirements.txt requirements.in pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install package in development mode
RUN pip install -e .

# Create directories
RUN mkdir -p /app/data/papers /app/data/embeddings /app/data/exports /app/logs

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "kg_builder.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
