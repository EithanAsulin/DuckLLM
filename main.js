const { ipcMain, app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn, execSync } = require('child_process');
const fs = require('fs');

// Utility to clean terminal output (strip ANSI codes)
const cleanOutput = (data) => {
    return data.toString()
        .replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '')
        .trim();
};

const parseProgress = (line) => {
    const pctMatch = line.match(/(\d+)%/);
    const speedMatch = line.match(/(\d+(?:\.\d+)?\s*[KMG]B\/s)/);
    const sizeMatch = line.match(/(\d+(?:\.\d+)?\s*[KMG]B)\/(\d+(?:\.\d+)?\s*[KMG]B)/);
    const etaMatch = line.match(/(\d+s|0s)/);
    
    if (pctMatch) {
        return {
            isProgress: true,
            percentage: parseInt(pctMatch[1]),
            speed: speedMatch ? speedMatch[1] : '',
            sizeRead: sizeMatch ? sizeMatch[1] : '',
            sizeTotal: sizeMatch ? sizeMatch[2] : '',
            eta: etaMatch ? etaMatch[1] : '',
            raw: line
        };
    }
    return line;
};

// Global handles
let mainWindow;

// Helper to perform the same checks as the IPC handler internally
function checkSystemReady() {
    const isWin = process.platform === 'win32';
    try {
        // Quick check for ollama
        const ollamaCmd = (isWin) ? 'ollama' : (fs.existsSync('/usr/local/bin/ollama') ? '/usr/local/bin/ollama' : 'ollama');
        execSync(`${ollamaCmd} --version`, { stdio: 'ignore', windowsHide: isWin });
        
        // Quick check for models
        const listOutput = execSync(`${ollamaCmd} list`, { stdio: 'pipe', windowsHide: isWin }).toString();
        const hasDuck = /duck/i.test(listOutput);
        
        return hasDuck;
    } catch (e) { return false; }
}

function launchPythonBackend() {
    const isWin = process.platform === 'win32';
    const scriptPath = path.join(__dirname, 'src', 'DuckLLM.py');
    console.log("Ready detected. Launching Backend directly...");
    
    const tryLaunch = (pyCmd) => {
        try {
            const proc = spawn(pyCmd, [scriptPath], { 
                detached: true, 
                stdio: 'ignore', 
                windowsHide: isWin,
                shell: false 
            });
            proc.unref();
            return proc;
        } catch (e) { return null; }
    };

    if (!tryLaunch(isWin ? 'pythonw' : 'python3')) tryLaunch('python');
    setTimeout(() => { app.quit(); }, 1500);
}

function createWindow() {
    // Check if user explicitly wants to go to setup (for maintenance/uninstall)
    const forceSetup = process.argv.includes('--setup') || process.argv.includes('--uninstall') || process.argv.includes('-s');
    const ready = checkSystemReady();
    
    if (ready && !forceSetup) {
        launchPythonBackend();
        return; // Jump directly to the app
    }

    mainWindow = new BrowserWindow({
        width: 1000,
        height: 750,
        frame: false,
        backgroundColor: '#08080a',
        icon: path.join(__dirname, 'src', 'logo.png'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
        },
    });
    mainWindow.loadFile('setup.html');
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('install-ollama', async (event, mode) => {
    const isWin = process.platform === 'win32';
    if (!isWin) return false; 
    
    return new Promise((resolve) => {
        const cmd = 'winget';
        const args = ['install', '-e', '--id', 'Ollama.Ollama', '--version', '0.4.0', '--accept-package-agreements', '-h'];
        const proc = spawn(cmd, args, { windowsHide: true });
        proc.on('close', (code) => {
            resolve(code === 0);
        });
    });
});

ipcMain.handle('check-dependencies', async () => {
    const isWin = process.platform === 'win32';
    const results = { ollama: false, python: false, admin: false, winget: false, hasModels: false };

    const getVersion = (cmd) => {
        try {
            const output = execSync(`${cmd} --version`, { stdio: 'pipe', windowsHide: isWin }).toString().trim();
            const match = output.match(/(\d+\.\d+\.\d+)/);
            return match ? match[1] : true;
        } catch (e) { return false; }
    };

    results.ollama = getVersion('ollama');
    if (!results.ollama && !isWin) {
        results.ollama = getVersion('/usr/local/bin/ollama');
    }

    results.python = getVersion(isWin ? 'python' : 'python3');
    if (!results.python) results.python = getVersion('python');
    
    if (isWin) {
        results.winget = getVersion('winget');
        try {
            execSync('net session', { stdio: 'ignore' });
            results.admin = true;
        } catch (e) { results.admin = false; }
    } else {
        results.admin = true; 
        results.winget = true;
    }

    try {
        const cmd = (!isWin && !getVersion('ollama')) ? '/usr/local/bin/ollama' : 'ollama';
        const listOutput = execSync(`${cmd} list`, { stdio: 'pipe', windowsHide: isWin }).toString();
        results.hasModels = /duck/i.test(listOutput);
    } catch (e) {}

    return results;
});

ipcMain.handle('check-gpu', async () => {
    const isWin = process.platform === 'win32';
    if (!isWin) return { name: 'Unified Graphics', vram: 8 };

    try {
        // Try nvidia-smi first for precise VRAM
        const nSmi = execSync('nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits', { stdio: 'pipe' }).toString().trim();
        const parts = nSmi.split('\n')[0].split(', ');
        const name = parts[0];
        const vram = Math.round(parseInt(parts[1]) / 1024);
        return { name, vram };
    } catch (e) {
        try {
            // Fallback to wmic
            const wmic = execSync('wmic path win32_VideoController get name', { stdio: 'pipe' }).toString().trim();
            const lines = wmic.split('\n');
            const name = lines[1] ? lines[1].trim() : 'Unknown GPU';
            return { name, vram: 4 }; 
        } catch (e2) {
            return { name: 'Standard VGA Graphics', vram: 2 };
        }
    }
});

ipcMain.handle('get-ollama-models', async () => {
    try {
        const isWin = process.platform === 'win32';
        const cmd = (!isWin && !execSync('ollama --version', {stdio:'ignore'})) ? '/usr/local/bin/ollama' : 'ollama';
        const list = execSync(`${cmd} list`, { stdio: 'pipe', windowsHide: true }).toString();
        const lines = list.trim().split('\n');
        return lines.slice(1).map(line => {
            const parts = line.split(/\s+/);
            return { name: parts[0], size: parts[2] + ' ' + parts[3] };
        }).filter(m => m.name);
    } catch (e) { return []; }
});

ipcMain.handle('create-model', async (event, modelSelection) => {
    const win = BrowserWindow.getFocusedWindow();
    const isWin = process.platform === 'win32';
    
    let cmd = 'ollama';
    if (!isWin) {
        try { execSync('ollama --version', { stdio: 'ignore' }); }
        catch (e) { cmd = '/usr/local/bin/ollama'; }
    }

    const run = (args) => new Promise((resolve, reject) => {
        const proc = spawn(cmd, args, { windowsHide: isWin });
        
        proc.stdout.on('data', (data) => {
            const line = cleanOutput(data);
            if (!line) return;
            const update = parseProgress(line);
            win.webContents.send('setup-progress', update);
        });

        proc.stderr.on('data', (data) => {
            const line = cleanOutput(data);
            if (!line) return;
            const update = parseProgress(line);
            win.webContents.send('setup-progress', update);
        });

        proc.on('close', (code) => {
            if (code === 0) resolve();
            else reject(new Error(`Process exited with code ${code}`));
        });
    });

    try {
        const suffix = modelSelection === 'full' ? '' : '_Light';
        const variantsDir = path.join(__dirname, 'src', 'Variants');
        
        const modelsToCreate = [
            { name: 'DuckLLM', file: `Modelfile${suffix}` },
            { name: 'DuckLLM_Unfiltered', file: `Modelfile_Unfiltered${suffix}` }
        ];

        for (const m of modelsToCreate) {
            const modelfilePath = path.join(variantsDir, m.file);
            if (!fs.existsSync(modelfilePath)) {
                console.warn(`Skipping ${m.name}, file not found: ${modelfilePath}`);
                continue;
            }
            
            win.webContents.send('setup-progress', `Building ${m.name}...`);
            await run(['create', m.name, '-f', modelfilePath]);
        }

        win.webContents.send('setup-progress', { finalized: true });
        return { success: true };
    } catch (e) {
        win.webContents.send('setup-progress', `Error: ${e.message}`);
        return { success: false, error: e.message };
    }
});

ipcMain.on('launch-app', () => {
    const isWin = process.platform === 'win32';
    const scriptPath = path.join(__dirname, 'src', 'DuckLLM.py');
    
    const tryLaunch = (pyCmd) => {
        try {
            const proc = spawn(pyCmd, [scriptPath], { 
                detached: true, 
                stdio: 'ignore', 
                windowsHide: isWin,
                shell: false 
            });
            proc.unref();
            return proc;
        } catch (e) { return null; }
    };

    const p = tryLaunch(isWin ? 'pythonw' : 'python3');
    if (!p) tryLaunch('python');

    setTimeout(() => { app.quit(); }, 1000);
});

ipcMain.on('close-app', () => app.quit());

ipcMain.handle('kill-existing', async () => {
    if (process.platform === 'win32') {
        try {
            execSync('taskkill /F /IM python.exe /T', { stdio: 'ignore', windowsHide: true });
            execSync('taskkill /F /IM pythonw.exe /T', { stdio: 'ignore', windowsHide: true });
        } catch (e) {}
    }
    return true;
});

ipcMain.handle('uninstall-app', async (event, modelsToRemove = []) => {
    const win = BrowserWindow.getFocusedWindow();
    const isWin = process.platform === 'win32';
    let cmd = 'ollama';
    if (!isWin) {
        try { execSync('ollama --version', { stdio: 'ignore' }); }
        catch (e) { cmd = '/usr/local/bin/ollama'; }
    }

    try {
        for (const model of modelsToRemove) {
            win.webContents.send('setup-progress', `Removing ${model}...`);
            await new Promise((resolve) => {
                const proc = spawn(cmd, ['rm', model], { windowsHide: true });
                proc.on('close', resolve);
            });
        }
        return { success: true };
    } catch (e) {
        return { success: false, error: e.message };
    }
});
