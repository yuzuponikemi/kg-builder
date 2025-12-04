# Ollama Setup and Usage Guide

Complete guide for using Ollama with KG Builder for local, private knowledge graph construction from research papers.

## Table of Contents

1. [Why Ollama?](#why-ollama)
2. [Installation](#installation)
3. [Recommended Models](#recommended-models)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [Performance Tuning](#performance-tuning)
7. [Troubleshooting](#troubleshooting)

---

## Why Ollama?

### Benefits of Using Ollama

1. **100% Local & Private**: All processing happens on your PC - no data leaves your machine
2. **No API Costs**: No per-token charges, unlimited usage
3. **Offline Capable**: Works without internet connection
4. **Customizable**: Full control over models and parameters
5. **Fast**: With GPU acceleration, comparable speed to cloud APIs
6. **Open Source**: Transparent, auditable, community-driven

### Hardware Requirements

**Minimum:**
- CPU: 4+ cores
- RAM: 8GB
- Storage: 10GB for models
- GPU: Optional (CPU-only works but slower)

**Recommended:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 50GB+ for multiple models
- GPU: NVIDIA GPU with 8GB+ VRAM (for CUDA acceleration)
- AMD GPU: ROCm support (limited)

---

## Installation

### Step 1: Install Ollama

#### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### macOS
```bash
brew install ollama
```

Or download from: https://ollama.com/download/mac

#### Windows
Download installer from: https://ollama.com/download/windows

### Step 2: Verify Installation

```bash
ollama --version
```

### Step 3: Start Ollama Service

The Ollama service should start automatically. To verify:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it manually
ollama serve
```

---

## Recommended Models

### For Knowledge Graph Construction

#### 1. **Llama 3.1 8B** (Recommended for most users)
- **Best for**: Balanced performance and quality
- **VRAM Required**: ~8GB
- **Speed**: Fast
- **Quality**: Excellent

```bash
ollama pull llama3.1:8b
```

#### 2. **Llama 3.1 70B** (Best quality)
- **Best for**: Maximum extraction accuracy
- **VRAM Required**: ~40GB
- **Speed**: Slower
- **Quality**: Best

```bash
ollama pull llama3.1:70b
```

#### 3. **Mistral 7B** (Fast alternative)
- **Best for**: Quick processing, lower VRAM
- **VRAM Required**: ~6GB
- **Speed**: Very fast
- **Quality**: Good

```bash
ollama pull mistral:7b
```

#### 4. **Mixtral 8x7B** (High quality)
- **Best for**: Advanced reasoning
- **VRAM Required**: ~26GB
- **Speed**: Moderate
- **Quality**: Excellent

```bash
ollama pull mixtral:8x7b
```

#### 5. **Qwen2.5 7B** (Technical content)
- **Best for**: Scientific/technical papers
- **VRAM Required**: ~7GB
- **Speed**: Fast
- **Quality**: Very good for technical content

```bash
ollama pull qwen2.5:7b
```

#### 6. **DeepSeek Coder 6.7B** (Code-heavy papers)
- **Best for**: Computer science papers, code analysis
- **VRAM Required**: ~7GB
- **Speed**: Fast
- **Quality**: Excellent for technical/code content

```bash
ollama pull deepseek-coder:6.7b
```

### For Embeddings

#### Nomic Embed Text (Recommended)
```bash
ollama pull nomic-embed-text
```
- **Best for**: Semantic search and similarity
- **Dimension**: 768
- **Speed**: Very fast
- **Quality**: Excellent

---

## Configuration

### Step 1: Configure Environment Variables

Copy and edit `.env.example`:

```bash
cp .env.example .env
nano .env  # or use your preferred editor
```

### Step 2: Set Ollama as Primary Provider

```bash
# LLM Provider Configuration
LLM_PROVIDER=ollama

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b  # Change based on your hardware
OLLAMA_TIMEOUT=300
OLLAMA_NUM_CTX=8192  # Context window (adjust based on RAM)
OLLAMA_NUM_GPU=1  # Number of GPUs (0 for CPU only)
OLLAMA_NUM_THREAD=8  # CPU threads

# Embedding Configuration
EMBEDDING_PROVIDER=local  # or ollama
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5  # For local
OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # For Ollama
EMBEDDING_DEVICE=cuda  # or cpu
```

### Step 3: Test Configuration

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test model
ollama run llama3.1:8b "Hello, test message"
```

---

## Usage Examples

### Basic Usage

```python
from kg_builder import KGClient

# Initialize with Ollama (automatic from .env)
client = KGClient(api_url="http://localhost:8000")

# Process a paper
paper = client.papers.add(
    pdf_path="path/to/paper.pdf",
    auto_extract=True
)

# The system will use Ollama automatically
print(f"Extracted {len(paper.concepts)} concepts")
```

### Advanced: Switching Models

```python
from kg_builder.config import get_settings

settings = get_settings()

# Check current model
print(f"Using model: {settings.current_llm_model}")

# To switch models, update .env and restart API server
```

### Using Different Models for Different Tasks

Edit your `.env`:

```bash
# Use fast model for initial extraction
OLLAMA_MODEL=mistral:7b

# Or use high-quality model for important papers
OLLAMA_MODEL=llama3.1:70b
```

---

## Performance Tuning

### GPU Acceleration (NVIDIA)

1. **Check CUDA availability:**
```bash
nvidia-smi
```

2. **Set GPU in config:**
```bash
OLLAMA_NUM_GPU=1  # Use 1 GPU
EMBEDDING_DEVICE=cuda
```

3. **For multiple GPUs:**
```bash
OLLAMA_NUM_GPU=2  # Use 2 GPUs
```

### CPU-Only Configuration

If you don't have a GPU or have limited VRAM:

```bash
OLLAMA_NUM_GPU=0  # Disable GPU
OLLAMA_NUM_THREAD=16  # Increase CPU threads
OLLAMA_MODEL=mistral:7b  # Use smaller model
OLLAMA_NUM_CTX=4096  # Reduce context window
```

### Memory Optimization

For systems with limited RAM:

```bash
# Reduce context window
OLLAMA_NUM_CTX=4096  # Default is 8192

# Use smaller models
OLLAMA_MODEL=mistral:7b

# Reduce batch size
EMBEDDING_BATCH_SIZE=16  # Default is 32

# Process fewer papers concurrently
MAX_CONCURRENT_EXTRACTIONS=2  # Default is 5
```

### Speed Optimization

For maximum speed:

```bash
# Use fastest model
OLLAMA_MODEL=mistral:7b

# Reduce quality for speed
DEFAULT_TEMPERATURE=0.1  # Slightly increase for faster generation

# Enable GPU
OLLAMA_NUM_GPU=1

# Increase GPU layers (if you have VRAM)
# Set via Ollama model parameters
```

---

## Troubleshooting

### Issue: Ollama Not Found

**Error:** `Connection refused to localhost:11434`

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve

# Or restart service (Linux)
sudo systemctl restart ollama
```

### Issue: Model Not Found

**Error:** `model 'llama3.1:8b' not found`

**Solution:**
```bash
# Pull the model
ollama pull llama3.1:8b

# List available models
ollama list
```

### Issue: Out of Memory (OOM)

**Error:** `CUDA out of memory` or system freezes

**Solution:**

1. **Use smaller model:**
```bash
OLLAMA_MODEL=mistral:7b  # Instead of llama3.1:70b
```

2. **Reduce context window:**
```bash
OLLAMA_NUM_CTX=4096  # Instead of 8192
```

3. **Use quantized models:**
```bash
# Pull quantized version
ollama pull llama3.1:8b-q4_0  # 4-bit quantization
```

4. **Offload to CPU:**
```bash
OLLAMA_NUM_GPU=0  # Disable GPU, use CPU
```

### Issue: Slow Performance

**Symptoms:** Extraction takes too long

**Solutions:**

1. **Check GPU usage:**
```bash
nvidia-smi  # Should show Ollama using GPU
```

2. **Use faster model:**
```bash
OLLAMA_MODEL=mistral:7b  # Fast model
```

3. **Increase GPU allocation:**
```bash
OLLAMA_NUM_GPU=1  # Ensure GPU is enabled
```

4. **Reduce concurrent extractions:**
```bash
MAX_CONCURRENT_EXTRACTIONS=2  # Reduce from 5
```

### Issue: Connection Timeout

**Error:** `Request timeout after 300 seconds`

**Solution:**
```bash
# Increase timeout
OLLAMA_TIMEOUT=600  # 10 minutes

# Or reduce context size
OLLAMA_NUM_CTX=4096
```

### Issue: Poor Extraction Quality

**Symptoms:** Missing concepts, incorrect relationships

**Solutions:**

1. **Use better model:**
```bash
OLLAMA_MODEL=llama3.1:70b  # Best quality
# or
OLLAMA_MODEL=mixtral:8x7b  # Good balance
```

2. **Increase context window:**
```bash
OLLAMA_NUM_CTX=16384  # If you have enough RAM
```

3. **Adjust temperature:**
```bash
DEFAULT_TEMPERATURE=0.0  # More deterministic
```

4. **Check prompts:** Review and improve extraction prompts in `src/kg_builder/extractor/prompts/`

---

## Model Comparison

| Model | VRAM | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| mistral:7b | 6GB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | Quick processing |
| llama3.1:8b | 8GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | General use (Recommended) |
| qwen2.5:7b | 7GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Technical papers |
| deepseek-coder:6.7b | 7GB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | CS papers |
| mixtral:8x7b | 26GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | High quality |
| llama3.1:70b | 40GB+ | ⚡⚡ | ⭐⭐⭐⭐⭐ | Best quality |

---

## Quick Start Script

Use the provided setup script:

```bash
# Run Ollama setup
uv run python scripts/setup_ollama.py

# This will:
# 1. Check if Ollama is installed
# 2. Pull recommended models
# 3. Test configuration
# 4. Provide recommendations based on your hardware
```

---

## Tips for Best Results

1. **Start with recommended model:** llama3.1:8b is the sweet spot
2. **Use GPU if available:** Dramatically faster than CPU
3. **Monitor resources:** Use `nvidia-smi` or `htop` to check usage
4. **Keep models updated:** `ollama pull <model>` to update
5. **Test before bulk processing:** Process one paper first to verify quality
6. **Consider paper type:** Use specialized models (e.g., deepseek-coder for CS papers)
7. **Adjust context window:** Larger for long papers, smaller for faster processing

---

## Switching Between Ollama and Cloud APIs

You can easily switch between Ollama and cloud APIs:

### Use Ollama (Local)
```bash
LLM_PROVIDER=ollama
```

### Use OpenAI
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
```

### Use Anthropic
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

Just update `.env` and restart the API server. No code changes needed!

---

## Next Steps

1. **Install Ollama:** Follow installation steps above
2. **Pull a model:** Start with `ollama pull llama3.1:8b`
3. **Configure:** Set `LLM_PROVIDER=ollama` in `.env`
4. **Test:** Run `python scripts/setup_ollama.py`
5. **Process papers:** Start building your knowledge graph!

For more help, see:
- Ollama documentation: https://ollama.com/docs
- Model library: https://ollama.com/library
- GitHub issues: https://github.com/yourusername/kg-builder/issues
