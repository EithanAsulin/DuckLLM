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

# **Windows**

For **Windows Users** You Can Download **DuckLLM.zip** From The Releases and Double Click `installer.py`.

# **Linux**

For **Linux Users** Download **DuckLLM.zip** And Run
```bash
python3 installer.py
```

# **MacOS**
For **MacOS Users** Of Both M Series CPUs and Intel CPUs Download `DuckLLM Installer.dmg` From The Releases, Open The File and Drag **DuckLLM** Into the **Applications** Folder.

# **Android**
For **Android Users** Open The Play Store and **Search `DuckLLM`.**

# Adding a Shortcut
**To Add a Shortcut** For **DuckLLM** You Can Use :
# Windows
For **Windows Users** It's Recommended To Use **One Quick** With The Shortcut To
```Windows
python3 ~\Desktop\DuckLLM\DuckLLM.py
```
Or **Create a .bat File Shortcut.**


> Press `Esc` To Close It.

# Linux
For **Linux Users** It's Mostly The Same Across Environments **(Wayland)**

```Navigate
Open Settings > Keyboard > Shortcuts > Add Custom Shortcut
```
In The Shortcut Type :
```Bash
python3 ~/DuckLLM/DuckLLM.py
```

> Press `Esc` To Close It.

# MacOS
Simply Open The App Once And It'll Appear In The Dock!

> Press `Esc` To Close It.

# Key Features
- **Privacy First**: Fully local execution - no data is sent to external servers.
- **Ultra Quick**: **With DuckLLM's App You'll Experience Highly Impressive Speeds With Well Made Features.
- **Smooth UI**: With **DuckLLM's Dynamic Island-like UI** You Experience High Responsiveness & Smooth Animations

# DuckLLM Mobile
> Mobile installation currently uses Wllama & Ollama for on-device inference.

1. Download DuckLLM from the Google Play Store.
2. Open the app, complete or skip the username setup, and navigate to **Download Center**.
3. Choose one of the available models:
   - **DuckLLM Light (0.6B)** - Recommended for most devices
   - **DuckLLM Base (1.6B)**
   - **DuckLLM Pro (3.1B)**

# Known Issues 
# Windows
**In Some Window Installations** The UI Hitboxes May Be Inaccurate

# Linux
***None!***

# MacOS
**Due To Apple's Aggressive Memory Management** on Heavy Workflows **DuckLLM** Might Be Closed By **MacOS,** To Prevent This **DuckLLM Uses a 3.1b Model Only** To Manage Memory Better.

# Commercial Use
For inquiries regarding commercial licensing, please reach out via:
- **Email**: duckinc68@gmail.com
- **Discord**: https://discord.com/invite/DkNt6FXf7J

# Relationship to Qwen
DuckLLM is built on **Qwen 2.5** as its base model and extends it through fine-tuning aimed at improving performance in specific areas where the base model underperforms. Training a large language model from scratch was outside the scope of this project; the additional training is focused on targeted improvements rather than architectural changes.

# Source Code
DuckLLM's source code is available in the **/src** folder of this repository and is also included in the official releases.
**(Note : MacOS's Source Code Differs Only In The File Handling To Allow Compiling To a `.dmg`)**

# Contributors
- **[psale](https://github.com/psale)**

# License
- **DuckLLM Proprietary License**: Covers the DuckLLM model weights. Free for personal use; a commercial license is required for business use.
- **Apache 2.0**: Covers the Qwen 2.5 base model.
