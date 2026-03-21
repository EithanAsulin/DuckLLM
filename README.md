[![DuckLLM Model License](https://img.shields.io/badge/License-DuckLLM%20Proprietary-blue)](DuckLLM.license)
[![DuckLLM](https://img.shields.io/badge/Version-DuckLLM%20%201.0-red)](src/README.txt)
[![Base Model](https://img.shields.io/badge/Base-Qwen2.5%20Apache%202.0-green)](Apache-2.0.license)

# Official Homepage
https://eithanasulin.github.io/DuckLLM/

# Supported Systems
- Windows
- macOS
- Linux
- Android

# What is DuckLLM?
DuckLLM is a free, locally-run LLM designed with a strong focus on privacy and security, without compromising on performance or functionality. It simplifies the process of self-hosting an AI model on your own device - for both desktop and mobile - with a privacy-first architecture that ensures your data never leaves your machine.

# Getting Started

## For End Users (Standalone)
1. **Download**: Get the latest release for your platform - `DuckLLM.exe` (Windows), `.dmg` (macOS), or `.AppImage` (Linux).
2. **Run the Setup Wizard**: The wizard will automatically handle **Ollama** and **Python** installation if they are not already present.
3. **Select a Model**: Choose between **Full** (7.6B) or **Light** (3.1B) depending on your hardware.

## For Developers (Source Setup)
1. **Clone the repository** and navigate to the project directory.
2. **Install dependencies**: `npm install`
3. **Launch the app**: `npm start` - performs background dependency checks and starts immediately.
4. **Run the setup wizard manually**: `npm run setup` - useful for maintenance or reinstallation.
5. **Build a portable executable**: `npm run dist` - output will be placed in the `/dist` folder.

## Alternative: Python Manual Installer
You can also run the installer directly from source:
```bash
python src/installer.py
```

# Key Features
- **Privacy First**: Fully local execution - no data is sent to external servers.
- **Fast Boot**: Background dependency checks enable near-instant startup.
- **RTL Support**: Improved Right-to-Left (Hebrew) text alignment and caret handling, optimized for both Windows and Linux.

# DuckLLM Mobile
> Mobile installation currently uses Wllama for on-device inference.

1. Download DuckLLM from the Google Play Store.
2. Open the app, complete or skip the username setup, and navigate to **Download Center**.
3. Choose one of the available models:
   - **DuckLLM Light (0.6B)** - Recommended for most devices
   - **DuckLLM Base (1.6B)**
   - **DuckLLM Pro (3.1B)**

# Keyboard Shortcuts (Desktop)
To launch DuckLLM via a keyboard shortcut:

- **Linux**: Add a custom shortcut in System Settings pointing to: `python ~/DuckLLM/DuckLLM.py`
- **Windows**: Use PowerToys or a desktop shortcut pointing to: `python ~/Desktop/DuckLLM/DuckLLM.py`

> Press `Del` to show the window and your configured key to hide it.

# Relationship to Qwen
DuckLLM is built on **Qwen 2.5** as its base model and extends it through fine-tuning aimed at improving performance in specific areas where the base model underperforms. Training a large language model from scratch was outside the scope of this project; the additional training is focused on targeted improvements rather than architectural changes.

# Commercial Use
For inquiries regarding commercial licensing, please reach out via:
- **Email**: duckinc68@gmail.com
- **Discord**: https://discord.com/invite/DkNt6FXf7J

# Source Code
DuckLLM's source code is available in the **/src** folder of this repository and is also included in the official releases.

# Contributors
- **[psale](https://github.com/psale)**

# License
- **DuckLLM Proprietary License**: Covers the DuckLLM model weights. Free for personal use; a commercial license is required for business use.
- **Apache 2.0**: Covers the Qwen 2.5 base model.