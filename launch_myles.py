import os
import sys
import subprocess
import shutil

def get_python_executable():
    """Determine the correct Python executable path, prioritizing the virtual environment."""
    # Check if we are in a virtual environment
    venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts' if sys.platform == 'win32' else 'bin')
    
    if os.path.exists(venv_path):
        py_executable = os.path.join(venv_path, 'python.exe' if sys.platform == 'win32' else 'python')
        if os.path.isfile(py_executable):
            return py_executable
    
    # Fallback to system Python or the one used to run this script
    return sys.executable

def launch_myles():
    """Launch the MylesAI terminal application."""
    target_script = r"C:\Users\Joshu\AppData\Local\MylesAI\myles_terminal.py"
    
    if not os.path.exists(target_script):
        print(f"Error: Target script not found at {target_script}")
        return
    
    python_executable = get_python_executable()
    
    try:
        subprocess.run([python_executable, target_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to launch MylesAI: {e}")
    except FileNotFoundError:
        print(f"Error: Python executable not found at {python_executable}")

if __name__ == "__main__":
    launch_myles()