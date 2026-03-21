import os
import sys
import shutil
import subprocess
from pathlib import Path
from time import sleep as wait

def run_command(cmd, shell=False, check=False):
    try:
        subprocess.run(cmd, shell=shell, check=check)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Command failed: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    print("|========================================================================================================")
    print("|")
    print("|")
    print("|                                 DuckLLM Universal Installer")
    print("|                                         By Duck Inc.")
    print("|")
    print("|")
    print("|========================================================================================================\n")

def append_to_bashrc(content):
    bashrc = Path.home() / ".bashrc"
    try:
        with open(bashrc, "a") as f:
            f.write(f"\n{content}\n")
        return True
    except Exception as e:
        print(f"Failed to update .bashrc: {e}")
        return False

def move_project_files(target_dir):
    """Moves project files to the specified directory."""
    print("=== Moving Files === ")
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    files_to_move = ["DuckLLM.py", "Attachment.png", "Web.png", "Unfiltered.png", "duckllm_settings.json", "duckllm_chat.json"]
    for file in files_to_move:
        if Path(file).exists():
            try:
                shutil.move(str(file), str(target_dir / file))
            except Exception as e:
                print(f"Warning: Could not move {file}: {e}")

def setup_ollama_models(model_choice):
    print(f"=== Setting Up LLM Models ({model_choice.capitalize()}) === ")
    
    suffix = "" if model_choice == "full" else "_Light"
    modelfile = Path("Variants") / f"Modelfile{suffix}"
    unfiltered_file = Path("Variants") / f"Modelfile_Unfiltered{suffix}"

    if modelfile.exists():
        run_command(f"ollama create DuckLLM -f {modelfile}", shell=True)
    else:
        print(f"Warning: {modelfile} not found.")
        
    if unfiltered_file.exists():
        run_command(f"ollama create DuckLLM_Unfiltered -f {unfiltered_file}", shell=True)
    else:
        print(f"Warning: {unfiltered_file} not found.")

def main():
    clear_screen()
    print_banner()
    
    distro = False
    
    ask_install = input("Would You Like To Install DuckLLM? [Type Anything Or Close The Window]\n (You Should Read README.txt First) \n ====> ")
    if not ask_install:
        print("Installation cancelled.")
        return 

    model_choice = ""
    while model_choice not in ["full", "light"]:
        model_choice = input("What Model Do You Want To Use? [Full/Light] : ").strip().lower()

    while not distro:
        ask_distro = input("Which Operating System Are You Using? [Windows/macOS/Ubuntu/Debian/Arch/Other] :  ").strip().lower()

        if ask_distro in ["ubuntu", "debian", "arch", "other"]:
            distro = True
            print("=== Installing Dependencies ===\n")
            if ask_distro == "ubuntu":
                run_command("sudo apt update", shell=True)
                run_command("sudo apt install -y python3-pip curl", shell=True)
                run_command("sudo snap install ollama", shell=True) 
            elif ask_distro == "debian":
                run_command("sudo apt update", shell=True)
                run_command("sudo apt install -y python3-pip curl", shell=True)
                run_command("curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.4.0 sh", shell=True)
            elif ask_distro == "arch":
                run_command("sudo python -Sy --noconfirm", shell=True)
                run_command("sudo python -S --noconfirm curl python-pip pipx", shell=True)
                run_command("curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.4.0 sh", shell=True)
            elif ask_distro == "other":
                wait(5)
                run_command("curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.4.0 sh", shell=True)

            print("=== Installing Python Libraries ===\n")
            run_command("pip install PySide6 requests --break-system-packages", shell=True)

            print("=== Enabling Systemd Services For Ollama === ")
            run_command("sudo systemctl enable ollama", shell=True)
            run_command("sudo systemctl start ollama", shell=True)
            append_to_bashrc("export OLLAMA_KEEP_ALIVE=-1")

            setup_ollama_models(model_choice)
            move_project_files(Path.home() / "DuckLLM")

            print("=== Installation Complete === ")
            print(f"Run: python {Path.home() / 'DuckLLM'}/DuckLLM.py")

        elif ask_distro == "windows":
            distro = True
            print("=== Installing Dependencies ===\n")
            run_command('winget install -e --id Ollama.Ollama --version 0.4.0 --accept-package-agreements -h', shell=True)
            run_command("pip install PySide6 requests", shell=True)
            
            subprocess.Popen("ollama serve", shell=True)
            os.environ["OLLAMA_KEEP_ALIVE"] = "-1"
            run_command('setx OLLAMA_KEEP_ALIVE "-1"', shell=True)
            
            setup_ollama_models(model_choice)
            
            duckllm_path = Path.home() / "Desktop" / "DuckLLM"
            move_project_files(duckllm_path)

            print("=== Installation Complete === ")
            print(f"Location: {duckllm_path}")

        elif ask_distro == "macos":
            distro = True
            print("=== Installing Dependencies (macOS) ===\n")
            run_command("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
            run_command("pip3 install PySide6 requests", shell=True)
            
            subprocess.Popen("ollama serve", shell=True)
            
            target_dir = Path.home() / "Documents" / "DuckLLM"
            move_project_files(target_dir)

            print("=== Installation Complete === ")
            print(f"Location: {target_dir}")
            print(f"Run: python3 {target_dir}/DuckLLM.py")

        else:
            clear_screen()
            print("Unsupported Operating System.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
