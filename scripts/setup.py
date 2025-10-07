#!/usr/bin/env python3
"""
Setup script for ChemTutor
Automates initial setup and configuration
"""
import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def run_command(cmd, description="", encoding='utf-8'):
    """Run a shell command and handle errors"""
    if description:
        print(f"-> {description}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, encoding=encoding, errors='replace')
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def check_python_version():
    """Check if Python version is compatible"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("[ERROR] Python 3.10+ is required")
        return False
    
    print("[OK] Python version is compatible")
    return True


def check_ollama():
    """Check if Ollama is installed"""
    print_header("Checking Ollama")
    
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            print("[ERROR] Ollama is not installed")
            print("  Please install from: https://ollama.ai")
            return False
        
        print(f"[OK] Ollama installed: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"[ERROR] Error checking Ollama: {e}")
        return False


def setup_virtual_environment():
    """Create and activate virtual environment"""
    print_header("Setting Up Virtual Environment")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("[OK] Virtual environment already exists")
        return True
    
    if not run_command(f"{sys.executable} -m venv venv", "Creating virtual environment"):
        return False
    
    print("[OK] Virtual environment created")
    print("\nTo activate:")
    print("  Windows: venv\\Scripts\\activate")
    print("  Linux/Mac: source venv/bin/activate")
    return True


def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    # Use python -m pip instead of direct pip call to avoid path issues
    python_cmd = "venv/bin/python" if os.name != "nt" else "venv\\Scripts\\python"
    
    if not run_command(f"{python_cmd} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{python_cmd} -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    print("[OK] Dependencies installed")
    return True


def setup_environment_file():
    """Create .env file from template"""
    print_header("Setting Up Environment File")
    
    env_path = Path(".env")
    template_path = Path(".env.template")
    
    if env_path.exists():
        print("[OK] .env file already exists")
        try:
            response = input("  Overwrite? (y/N): ")
            if response.lower() != 'y':
                return True
        except EOFError:
            # Handle non-interactive execution
            print("  Keeping existing .env file (non-interactive mode)")
            return True
    
    if not template_path.exists():
        print("[ERROR] .env.template not found")
        return False
    
    # Copy template
    with open(template_path) as f_in:
        with open(env_path, 'w') as f_out:
            f_out.write(f_in.read())
    
    print("[OK] Created .env file")
    print("\n[WARNING] IMPORTANT: Edit .env and add your OPENAI_API_KEY")
    return True


def pull_ollama_models():
    """Pull required Ollama models"""
    print_header("Pulling Ollama Models")
    
    models = [
        ("qwen2.5:14b", "Main LLM (large, ~8GB)"),
        ("nomic-embed-text", "Embedding model"),
    ]
    
    print("This may take a while depending on your internet connection...\n")
    
    for model, description in models:
        print(f"-> Pulling {model} ({description})")
        # Use encoding='utf-8' and errors='replace' to handle Unicode issues
        if not run_command(f"ollama pull {model}", encoding='utf-8'):
            print(f"  [WARNING] Failed to pull {model}")
            if model == "qwen2.5:14b":
                print("  You can use 'mistral' as a lighter alternative")
    
    print("\n[OK] Ollama models ready")
    return True


def create_directories():
    """Create necessary directories"""
    print_header("Creating Directories")
    
    directories = [
        "rag-system/data",
        "rag-system/vectorstore",
        "logs",
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created: {directory}")
    
    return True


def show_next_steps():
    """Display next steps for the user"""
    print_header("Setup Complete!")
    
    print("Next steps:")
    print("\n1. Configure your API key:")
    print("   Edit .env and add your OPENAI_API_KEY")
    
    print("\n2. Add chemistry PDFs:")
    print("   Place PDF textbooks in: rag-system/data/")
    
    print("\n3. Build the knowledge base:")
    print("   cd rag-system")
    print("   python indexer.py data/ --directory")
    
    print("\n4. Start the server:")
    print("   python run.py")
    print("   (Note: Use run.py instead of backend/app.py to avoid import issues)")
    
    print("\n5. Open your browser:")
    print("   http://localhost:8000")
    
    print("\n" + "=" * 60)
    print("  Happy tutoring!")
    print("=" * 60 + "\n")


def main():
    """Main setup routine"""
    print("\nChemTutor Setup Script")
    print("This script will set up your ChemTutor environment\n")
    
    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    steps = [
        ("Python Version", check_python_version),
        ("Ollama", check_ollama),
        ("Virtual Environment", setup_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Environment File", setup_environment_file),
        ("Directories", create_directories),
        ("Ollama Models", pull_ollama_models),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"[ERROR] Unexpected error in {step_name}: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        print("\n[WARNING] Setup completed with issues in:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease resolve these issues manually.")
    else:
        show_next_steps()
    
    return 0 if not failed_steps else 1


if __name__ == "__main__":
    sys.exit(main())

