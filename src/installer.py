import os
import sys
import shutil
import subprocess
from pathlib import Path
from time import sleep as wait

def run_command(cmd, shell=False, check=False):
    try:
        result = subprocess.run(cmd, shell=shell, check=check)
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

def main():
    clear_screen()
    print_banner()
    
    distro = False
    
    ask_install = input("Would You Like To Install DuckLLM? [Type Anything Or Close The Window]\n (You Should Read README.txt First) \n ====> ")
    if not ask_install:
        print("Installation cancelled.")
        return 

    while not distro:
        ask_distro = input("Which Operating System Are You Using? [Windows/Ubuntu/Debian/Arch/Other] :  ").strip().lower()

        if ask_distro == "ubuntu":
            distro = True
            print("=== Installing Dependencies ===\n")
            run_command("sudo apt update", shell=True)
            run_command("sudo apt install -y python3-pip curl", shell=True)
            run_command("sudo snap install ollama", shell=True) 
            
            print("=== Installing Python Libraries! Please Do Not Close The Installation. ===\n")
            run_command("pip install PySide6 requests --break-system-packages", shell=True)

            print("=== Enabling Systemd Services For Ollama === ")
            run_command("sudo systemctl enable ollama", shell=True)
            run_command("sudo systemctl start ollama", shell=True)
            append_to_bashrc("# DuckLLM Ollama Addon\nexport OLLAMA_KEEP_ALIVE=-1")

            print("=== Setting Up LLM Models === ")
            if Path("Modelfile").exists():
                run_command("ollama create DuckLLM -f Modelfile", shell=True)
            else:
                print("Warning: Modelfile not found, skipping DuckLLM model creation.")
            
            if Path("Modelfile_Unfiltered").exists():
                run_command("ollama create DuckLLM_Unfiltered -f Modelfile_Unfiltered", shell=True)
            else:
                print("Warning: Modelfile_Unfiltered not found, skipping Unfiltered model creation.")

            print("=== Moving Files === ")
            target_dir = Path.home() / "DuckLLM"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            files_to_move = ["DuckLLM.py", "Attachment.png", "Web.png", "Unfiltered.png", "duckllm_settings.json", "duckllm_chat.json", "fullscreen.html"]
            for file in files_to_move:
                if Path(file).exists():
                    shutil.move(file, target_dir / file)
                else:
                    print(f"Warning: {file} not found to move.")

            print("=== Installation Complete === ")
            print(f"Please Make a Shortcut To {target_dir}/DuckLLM.py To Run The Program\n (python DuckLLM.py) ")

        elif ask_distro == "debian":
            distro = True
            print("=== Installing Dependencies ===\n")
            run_command("sudo apt update", shell=True)
            run_command("sudo apt install -y python3-pip curl", shell=True)
            run_command("curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.4.0 sh", shell=True)

            print("=== Installing Python Libraries! Please Do Not Close The Installation. ===\n")
            run_command("pip install PySide6 requests --break-system-packages", shell=True)

            print("=== Enabling Systemd Services For Ollama === ")
            run_command("sudo systemctl enable ollama", shell=True)
            run_command("sudo systemctl start ollama", shell=True)
            append_to_bashrc("# DuckLLM Ollama Addon\nexport OLLAMA_KEEP_ALIVE=-1")

            print("=== Setting Up LLM Models === ")
            if Path("Modelfile").exists():
                run_command("ollama create DuckLLM -f Modelfile", shell=True)
            if Path("Modelfile_Unfiltered").exists():
                run_command("ollama create DuckLLM_Unfiltered -f Modelfile_Unfiltered", shell=True)

            print("=== Moving Files === ")
            target_dir = Path.home() / "DuckLLM"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            files_to_move = ["DuckLLM.py", "Attachment.png", "Web.png", "Unfiltered.png", "duckllm_settings.json", "duckllm_chat.json", "fullscreen.html"]
            for file in files_to_move:
                if Path(file).exists():
                    shutil.move(file, target_dir / file)

            print("=== Installation Complete === ")
            print(f"Please Make a Shortcut To {target_dir}/DuckLLM.py To Run The Program\n (python DuckLLM.py) ")

        elif ask_distro == "arch":
            distro = True
            print("=== Installing Dependencies ===\n")
            run_command("sudo pacman -Sy --noconfirm", shell=True)
            run_command("sudo pacman -S --noconfirm curl python-pip pipx", shell=True)
            run_command("curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.4.0 sh", shell=True)

            print("=== Installing Python Libraries! Please Do Not Close The Installation. ===\n")
            run_command("pip install PySide6 requests --break-system-packages", shell=True)

            print("=== Enabling Systemd Services For Ollama === ")
            run_command("sudo systemctl enable ollama", shell=True)
            run_command("sudo systemctl start ollama", shell=True)
            append_to_bashrc("# DuckLLM Ollama Addon\nexport OLLAMA_KEEP_ALIVE=-1")

            print("=== Setting Up LLM Models === ")
            if Path("Modelfile").exists():
                run_command("ollama create DuckLLM -f Modelfile", shell=True)
            if Path("Modelfile_Unfiltered").exists():
                run_command("ollama create DuckLLM_Unfiltered -f Modelfile_Unfiltered", shell=True)

            print("=== Moving Files === ")
            target_dir = Path.home() / "DuckLLM"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            files_to_move = ["DuckLLM.py", "Attachment.png", "Web.png", "Unfiltered.png", "duckllm_settings.json", "duckllm_chat.json", "fullscreen.html"]
            for file in files_to_move:
                if Path(file).exists():
                    shutil.move(file, target_dir / file)

            print("=== Installation Complete === ")
            print(f"Please Make a Shortcut To {target_dir}/DuckLLM.py To Run The Program\n (python DuckLLM.py) ")

        elif ask_distro == "windows":
            distro = True
            print("=== Installing Dependencies ===\n")
            
            run_command('winget install -e --id Ollama.Ollama --version 0.4.0 --accept-package-agreements -h', shell=True)
            
            print("Installing Python Libraries...\n")
            run_command("pip install PySide6 requests", shell=True)
            
            os.environ["OLLAMA_KEEP_ALIVE"] = "-1"
            run_command('setx OLLAMA_KEEP_ALIVE "-1"', shell=True)
            
            
            script_dir = Path(__file__).parent.absolute()
            desktop = Path.home() / "Desktop"
            duckllm_path = desktop / "DuckLLM"
            duckllm_path.mkdir(parents=True, exist_ok=True)
            
            print("=== Setting Up LLM Models === ")
            if (script_dir / "Modelfile").exists():
                run_command(f"ollama create DuckLLM -f \"{script_dir / 'Modelfile'}\"", shell=True)
            if (script_dir / "Modelfile_Unfiltered").exists():
                run_command(f"ollama create DuckLLM_Unfiltered -f \"{script_dir / 'Modelfile_Unfiltered'}\"", shell=True)

            print("=== Moving Files to Desktop ===")
            source_script = "DuckLLM.py"
            files_to_move = [
                source_script, "Attachment.png", "Web.png", "Unfiltered.png", 
                "duckllm_settings.json", "duckllm_chat.json", "fullscreen.html"
            ]
            
            for file in files_to_move:
                src = script_dir / file
                dst = duckllm_path / file
                
                if src.exists():
                    try:
                        
                        shutil.move(str(src), str(dst))
                        print(f"Successfully moved: {file}")
                    except Exception as e:
                        print(f"Error moving {file}: {e}")
                else:
                    print(f"File not found: {src}")

            print("\n=== Installation Complete === ")
            print(f"All files are now in: {duckllm_path}")

        elif ask_distro == "other":
            distro = True
            print("You've Selected Other. If You Haven't Installed Python Pip Please Restart The Installation Within 10 Seconds!\nAttempting Generic Linux Installation.\n(Beware The Installer Requires Python Pip To Be Manually Installed)")
            wait(10)

            print("=== Installing Ollama ===\n")
            run_command("curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.4.0 sh", shell=True)

            print("=== Installing Python Libraries! Please Do Not Close The Installation. ===\n")
            run_command("pip install PySide6 requests --break-system-packages", shell=True)

            print("=== Enabling Systemd Services For Ollama === ")
            run_command("sudo systemctl enable ollama", shell=True)
            run_command("sudo systemctl start ollama", shell=True)
            append_to_bashrc("# DuckLLM Ollama Addon\nexport OLLAMA_KEEP_ALIVE=-1")

            print("=== Setting Up LLM Models === ")
            if Path("Modelfile").exists():
                run_command("ollama create DuckLLM -f Modelfile", shell=True)
            if Path("Modelfile_Unfiltered").exists():
                run_command("ollama create DuckLLM_Unfiltered -f Modelfile_Unfiltered", shell=True)

            print("=== Moving Files === ")
            target_dir = Path.home() / "DuckLLM"
            target_dir.mkdir(parents=True, exist_ok=True)
            
            files_to_move = ["DuckLLM.py", "Attachment.png", "Web.png", "Unfiltered.png", "duckllm_settings.json", "duckllm_chat.json"]
            for file in files_to_move:
                if Path(file).exists():
                    shutil.move(file, target_dir / file)

            print("=== Installation Complete === ")
            print(f"Please Make a Shortcut To {target_dir}/DuckLLM.py To Run The Program\n (python DuckLLM.py) ")

        else:
            clear_screen()
            print("Unsupported Operating System.\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation interrupted by user.")
        sys.exit(1)
