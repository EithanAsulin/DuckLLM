[![DuckLLM Model License](https://img.shields.io/badge/License-DuckLLM%20Proprietary-blue)](DuckLLM.license)
[![DuckLLM](https://img.shields.io/badge/Version-DuckLLM%20%201.0-red)](src/README.txt)
[![Base Model](https://img.shields.io/badge/Base-Qwen2.5%20Apache%202.0-green)](Apache-2.0.license)

# Official Homepage
https://eithanasulin.github.io/DuckLLM/

# Supported Systems
- Windows
- macOS (New!)
- Linux
- Android

# What's DuckLLM?
DuckLLM is a Free Local LLM (AI) which excels in privacy and security while maintaining impressive performance and functionality. It makes it easy to locally host a model on your device for both Desktop & Mobile with a privacy-focused design.

# Getting Started (Desktop)

## For Developers (Source Setup)
If you have cloned this repository:
1. **Install Dependencies**: `npm install`
2. **Launch Setup Wizard**: `npm start`
3. **Build Portable Executable**: `npm run dist` (Output will be in `/dist`)

## For End Users (Standalone)
1. **Download & Run**: Launch the `DuckLLM.exe` (Windows), `.dmg` (macOS), or `.AppImage` (Linux) from the releases.
2. **Setup Wizard**: The wizard will automatically handle **Ollama** and **Python** installation if they are missing.
3. **Select Model**: Choose between **Full** (7.6B) or **Light** (3.1B) modes.

## Alternative: Python Manual Installer
Run the installer directly from the source:
```bash
python src/installer.py
```

# DuckLLM Mobile
> This installation only covers Wllama

- Download DuckLLM Mobile from the Google Play Store.
- Enter the App, skip or enter username, and select **Download Center**.
- Download one of these 3 models:
  - **DuckLLM Light (0.6b)** (Recommended for average use)
  - **DuckLLM Base (1.6b)**
  - **DuckLLM Pro (3.1b)**

# How To Add a Shortcut
- **Linux**: Add a keyboard shortcut in Settings to run: `python ~/DuckLLM/DuckLLM.py`
- **Windows**: Use PowerToys or a desktop shortcut to run: `python ~/Desktop/DuckLLM/DuckLLM.py`
- **Note**: Click `Del` to Show and your chosen key to Hide.

# DuckLLM For Commercial Use
If you're interested in commercial use of the DuckLLM model, contact:
- **Email**: duckinc68@gmail.com
- **Discord**: https://discord.com/invite/DkNt6FXf7J

# Relations To Qwen
i Want To Clarify This, You Should Be aware This Model is Kind Of a Fine Tune Due To Just Being Unable To Train From Scratch, The Purpose Of The Additional Training Is To Improve On Parts Where Alibaba Missed With Qwen2.5. 

# Source Code (Open Source)
DuckLLM's source code can be found in the **/src** folder in this GitHub repository or in the **Releases**.

# Contributors 
- **[psale](https://github.com/psale)**

# License Info
- **DuckLLM Proprietary License**: For proprietary models (Personal use only; Commercial license required for business).
- **Qwen Apache 2.0**: For the DuckLLM base model (Qwen 2.5).
