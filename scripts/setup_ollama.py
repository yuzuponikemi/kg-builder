#!/usr/bin/env python3
"""
Ollama Setup Script for KG Builder

This script helps you set up Ollama with the recommended models
for knowledge graph construction from research papers.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx"], check=True)
    import httpx


class Colors:
    """Terminal colors for pretty output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(text: str) -> None:
    """Print a colored header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def check_ollama_installed() -> bool:
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0:
            print_success(f"Ollama is installed: {result.stdout.strip()}")
            return True
        else:
            print_error("Ollama is not installed")
            return False
    except FileNotFoundError:
        print_error("Ollama is not installed")
        return False


def check_ollama_running() -> bool:
    """Check if Ollama service is running."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print_success("Ollama service is running")
            return True
        else:
            print_error("Ollama service is not responding correctly")
            return False
    except Exception as e:
        print_error(f"Ollama service is not running: {e}")
        return False


def get_installed_models() -> list[str]:
    """Get list of installed Ollama models."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
        return []
    except Exception:
        return []


def pull_model(model: str) -> bool:
    """Pull an Ollama model."""
    print_info(f"Pulling model: {model}")
    print("This may take a few minutes depending on your internet connection...")

    try:
        # Use ollama pull command
        process = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Stream output
        if process.stdout:
            for line in process.stdout:
                print(f"  {line.strip()}")

        process.wait()

        if process.returncode == 0:
            print_success(f"Successfully pulled {model}")
            return True
        else:
            print_error(f"Failed to pull {model}")
            return False
    except Exception as e:
        print_error(f"Error pulling {model}: {e}")
        return False


def test_model(model: str) -> bool:
    """Test if a model works correctly."""
    print_info(f"Testing model: {model}")

    try:
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": "Say 'test successful' and nothing else.",
                "stream": False,
            },
            timeout=60,
        )

        if response.status_code == 200:
            result = response.json()
            output = result.get("response", "").strip().lower()
            if "test successful" in output or "successful" in output:
                print_success(f"Model {model} is working correctly")
                return True
            else:
                print_warning(f"Model {model} responded but output was unexpected: {output}")
                return True  # Still working, just different output
        else:
            print_error(f"Model {model} test failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error testing {model}: {e}")
        return False


def get_system_info() -> dict[str, Any]:
    """Get system information for recommendations."""
    info: dict[str, Any] = {"gpu": None, "vram": 0, "ram": 0, "cpu_cores": 0}

    # Try to detect NVIDIA GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            vram = int(result.stdout.strip().split("\n")[0])
            info["gpu"] = "NVIDIA"
            info["vram"] = vram
    except FileNotFoundError:
        pass

    # Get RAM (Linux/Mac)
    try:
        if sys.platform == "linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        info["ram"] = int(line.split()[1]) // 1024  # Convert to MB
                        break
        elif sys.platform == "darwin":
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True
            )
            info["ram"] = int(result.stdout.strip()) // (1024 * 1024)  # Convert to MB
    except Exception:
        pass

    # Get CPU cores
    try:
        import multiprocessing

        info["cpu_cores"] = multiprocessing.cpu_count()
    except Exception:
        pass

    return info


def recommend_models(system_info: dict[str, Any]) -> list[tuple[str, str]]:
    """Recommend models based on system capabilities."""
    recommendations = []

    vram_gb = system_info["vram"] / 1024 if system_info["vram"] > 0 else 0
    ram_gb = system_info["ram"] / 1024 if system_info["ram"] > 0 else 0

    print_info("System Information:")
    if system_info["gpu"]:
        print(f"  GPU: {system_info['gpu']} with {vram_gb:.1f}GB VRAM")
    else:
        print("  GPU: Not detected (will use CPU)")
    print(f"  RAM: {ram_gb:.1f}GB")
    print(f"  CPU Cores: {system_info['cpu_cores']}")

    print("\n" + Colors.BOLD + "Recommended Models:" + Colors.ENDC)

    if vram_gb >= 40:
        recommendations.append(
            ("llama3.1:70b", "🏆 Best quality - You have the hardware for it!")
        )
        recommendations.append(("mixtral:8x7b", "⭐ Excellent alternative"))
    elif vram_gb >= 24:
        recommendations.append(("mixtral:8x7b", "🏆 Best for your hardware"))
        recommendations.append(("llama3.1:8b", "⚡ Faster alternative"))
    elif vram_gb >= 8:
        recommendations.append(("llama3.1:8b", "🏆 Perfect for your hardware (Recommended)"))
        recommendations.append(("qwen2.5:7b", "📚 Great for technical papers"))
        recommendations.append(("deepseek-coder:6.7b", "💻 Best for CS papers"))
    elif vram_gb >= 6:
        recommendations.append(("mistral:7b", "🏆 Best for your hardware"))
        recommendations.append(("deepseek-coder:6.7b", "💻 For technical content"))
    else:
        recommendations.append(("mistral:7b", "💻 CPU-friendly model"))
        recommendations.append(
            ("llama3.1:8b-q4_0", "⚡ Quantized version for limited resources")
        )

    # Always recommend embedding model
    recommendations.append(("nomic-embed-text", "🔍 For embeddings (Required)"))

    return recommendations


def create_env_file() -> None:
    """Create or update .env file with Ollama configuration."""
    env_example = Path(".env.example")
    env_file = Path(".env")

    if env_file.exists():
        print_warning(".env file already exists. Skipping creation.")
        print_info("Please manually update LLM_PROVIDER=ollama in .env")
        return

    if env_example.exists():
        print_info("Creating .env file from .env.example")
        with open(env_example) as f:
            content = f.read()

        # Ensure Ollama is set as default
        if "LLM_PROVIDER=" in content:
            content = content.replace("LLM_PROVIDER=openai", "LLM_PROVIDER=ollama")
            content = content.replace("LLM_PROVIDER=anthropic", "LLM_PROVIDER=ollama")

        with open(env_file, "w") as f:
            f.write(content)

        print_success("Created .env file with Ollama as default provider")
    else:
        print_error(".env.example not found")


def main() -> None:
    """Main setup function."""
    print_header("KG Builder - Ollama Setup")

    # Step 1: Check if Ollama is installed
    print_header("Step 1: Checking Ollama Installation")
    if not check_ollama_installed():
        print_error("Please install Ollama first:")
        print("  Linux: curl -fsSL https://ollama.com/install.sh | sh")
        print("  macOS: brew install ollama")
        print("  Windows: https://ollama.com/download/windows")
        sys.exit(1)

    # Step 2: Check if Ollama service is running
    print_header("Step 2: Checking Ollama Service")
    if not check_ollama_running():
        print_warning("Starting Ollama service...")
        print_info("Run in another terminal: ollama serve")
        print_info("Or wait for automatic startup...")
        input("Press Enter when Ollama is running...")

        if not check_ollama_running():
            print_error("Ollama service still not running. Please start it manually.")
            sys.exit(1)

    # Step 3: Get system info and recommendations
    print_header("Step 3: Analyzing Your System")
    system_info = get_system_info()
    recommended_models = recommend_models(system_info)

    # Step 4: Check installed models
    print_header("Step 4: Checking Installed Models")
    installed = get_installed_models()
    if installed:
        print_success(f"Found {len(installed)} installed model(s):")
        for model in installed:
            print(f"  • {model}")
    else:
        print_info("No models installed yet")

    # Step 5: Offer to install recommended models
    print_header("Step 5: Installing Recommended Models")
    print("\nRecommended models for your system:\n")
    for i, (model, desc) in enumerate(recommended_models, 1):
        status = "✓ Installed" if model in installed else "⬇ Not installed"
        print(f"{i}. {model} - {desc} [{status}]")

    print("\nOptions:")
    print("  1. Install all recommended models")
    print("  2. Install specific models")
    print("  3. Skip installation")

    choice = input("\nYour choice (1/2/3): ").strip()

    models_to_install = []
    if choice == "1":
        models_to_install = [m for m, _ in recommended_models if m not in installed]
    elif choice == "2":
        print("\nEnter model numbers to install (comma-separated):")
        numbers = input("Models: ").strip().split(",")
        for num in numbers:
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(recommended_models):
                    model = recommended_models[idx][0]
                    if model not in installed:
                        models_to_install.append(model)
            except ValueError:
                pass

    # Install selected models
    if models_to_install:
        print_header(f"Installing {len(models_to_install)} Model(s)")
        for model in models_to_install:
            if pull_model(model):
                test_model(model)
    else:
        print_info("Skipping model installation")

    # Step 6: Test configuration
    print_header("Step 6: Testing Configuration")
    final_installed = get_installed_models()

    # Find best available model for LLM
    llm_model = None
    for model, _ in recommended_models:
        if model in final_installed and "embed" not in model:
            llm_model = model
            break

    # Find embedding model
    embed_model = None
    for model in final_installed:
        if "embed" in model:
            embed_model = model
            break

    if llm_model:
        print_success(f"LLM Model available: {llm_model}")
    else:
        print_warning("No LLM model installed yet")

    if embed_model:
        print_success(f"Embedding Model available: {embed_model}")
    else:
        print_warning("No embedding model installed")

    # Step 7: Create .env file
    print_header("Step 7: Configuration File")
    create_env_file()

    # Step 8: Summary
    print_header("Setup Complete! 🎉")
    print_success("Ollama is ready for KG Builder\n")

    print(Colors.BOLD + "Next Steps:" + Colors.ENDC)
    print("1. Update .env file:")
    if llm_model:
        print(f"   OLLAMA_MODEL={llm_model}")
    if embed_model:
        print(f"   OLLAMA_EMBEDDING_MODEL={embed_model}")
    print("\n2. Start the API server:")
    print("   uvicorn kg_builder.api.main:app --reload")
    print("\n3. Start processing papers:")
    print("   python examples/process_paper.py")

    print("\n" + Colors.BOLD + "Resources:" + Colors.ENDC)
    print("📖 Ollama Guide: docs/OLLAMA_GUIDE.md")
    print("🌐 Ollama Models: https://ollama.com/library")
    print("❓ Get Help: https://github.com/yourusername/kg-builder/issues")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
