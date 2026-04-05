# DuckLLM Documentation
DuckLLM's Source Code Is Accessible Via **git**, To Clone The Source Code Run :
```bash
git clone https://github.com/EithanAsulin/DuckLLM.git
```

### Note:
This Source Code Is an Exact Match Of The Current Local Code, Theres No Hidden Files Or Removed One.

# How To Compile

# Pre-Compile Instructions
**If You've Compiled Before Please Run**
```bash
chmod +x commit_prepare.sh
./commit_prepare.sh
```

### deb.sh
```bash
chmod +x deb.sh
./deb.sh
```

### dmg.sh
***MUST BE RAN ON MAC DEVICES***
```zsh
chmod +x dmg.sh
./dmg.sh
```

### exe.bat
***MUST BE RAN ON WINDOWS DEVICES***
```cmd
./exe.bat
```

### Snapcraft (Snaps)
**You Must Have DuckLLM.deb Installed First***
```bash
cd snap
snapcraft pack --destructive
snap install duckllm-1.0-{architecture}.snap --dangerous
```

### bootstrap.iss
**Bootstrap.iss Is a Development Script Used To Create a Small Installer To Upload To The Microsoft Store**
```cmd
cd microsoft
```
# 
```md
Instructions on .iss Files
.iss Files Are Used With Inno Setup (Recommended 6.1+)
```

# Files Explained

# DuckLLM.py
- **DuckLLM.py:** The Main File That Includes The Backend **Powered By Llama.cpp** And The Frontend **Powered By PySide6**

# Fullscreen.html
- **Fullscreen.html:** As The Name States **Fullscreen Mode.**

# Assets
- **Web.png:** Web Search Icon
- **Unfiltered.png:** The Unfiltered Mode (Also Known as 18+/Grok Mode) Icon
- **Attachment.png:** The File Attach Icon
- **Unfiltered_Instructions.txt:** a Set Of Instructions For Unfiltered Mode

# GGUF
- **DuckLLM.gguf:** The Main GGUF Using DuckLLM 1.0 3.1b

# Scripts
- **dmg.sh:** The Compiling Script For MacOS Systems
- **deb.sh:** The Compiling Script For a Deb Package
- **exe.bat:** The Compiling Script For Windows 10/11 **(Only Creates The Base Files You Need Tools like [Inno Setup](https://jrsoftware.org/isinfo.php) For The Installer)**

# Folders 
- **outputs:** Where The Final Compiled Files Should Be After Compiling
- **data:** Chat History
- **models:** Where Models From The Download Center End Up

# Contact For Assistance 
If You've Encountered Bugs With The Files Or Have Found a Bug/Added Feature You Want In Future Mainline DuckLLM Releases Contact :
- **Email:** duckinc68@gmail.com
- **Discord:** https://discord.com/invite/DkNt6FXf7J

**[GO BACK TO MAIN PAGE](https://github.com/EithanAsulin/DuckLLM/blob/master/README.md)**