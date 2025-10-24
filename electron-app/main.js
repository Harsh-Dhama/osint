const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');
const http = require('http');

const store = new Store();
let mainWindow;
let backendProcess;

// Backend server configuration
const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = 8000;
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: 'OSINT Platform',
    backgroundColor: '#1a1a2e'
  });

  // Load the app
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle navigation
  mainWindow.webContents.on('will-navigate', (event, url) => {
    // Allow navigation to backend API
    if (!url.startsWith(BACKEND_URL) && !url.startsWith('file://')) {
      event.preventDefault();
    }
  });
}

function startBackend() {
  return new Promise((resolve, reject) => {
    console.log('Starting backend server...');
    
    // Start Python backend by executing the backend main script
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    backendProcess = spawn(pythonPath, [
      path.join(__dirname, '..', 'backend', 'main.py')
    ], {
      windowsHide: false,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
      if (data.toString().includes('Uvicorn running')) {
        resolve();
      }
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    backendProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });

    // Wait max 10 seconds for backend to start
    setTimeout(() => {
      resolve(); // Continue even if backend doesn't confirm startup
    }, 10000);
  });
}

/**
 * Check whether the backend health endpoint responds.
 * Returns a Promise that resolves to true if backend is running.
 */
function isBackendRunning() {
  return new Promise((resolve) => {
    const url = `${BACKEND_URL}/api/health`;
    const req = http.get(url, { timeout: 3000 }, (res) => {
      const { statusCode } = res;
      let raw = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => { raw += chunk; });
      res.on('end', () => {
        try {
          const body = JSON.parse(raw || '{}');
          if (statusCode === 200 && body.status && body.status === 'healthy') {
            resolve(true);
            return;
          }
        } catch (err) {
          // ignore JSON parse
        }
        resolve(false);
      });
    });

    req.on('error', () => resolve(false));
    req.on('timeout', () => {
      req.destroy();
      resolve(false);
    });
  });
}

function stopBackend() {
  if (backendProcess) {
    console.log('Stopping backend server...');
    backendProcess.kill();
    backendProcess = null;
  }
}

// IPC Handlers
ipcMain.handle('get-backend-url', () => {
  return BACKEND_URL;
});

ipcMain.handle('get-store-value', (event, key) => {
  return store.get(key);
});

ipcMain.handle('set-store-value', (event, key, value) => {
  store.set(key, value);
  return true;
});

ipcMain.handle('delete-store-value', (event, key) => {
  store.delete(key);
  return true;
});

ipcMain.handle('clear-store', () => {
  store.clear();
  return true;
});

// App lifecycle
app.whenReady().then(async () => {
  try {
    // Only start backend if it's not already running (prevents port-in-use errors)
    const running = await isBackendRunning();
    if (!running) {
      await startBackend();
    } else {
      console.log('Backend already running, skipping spawn.');
    }

    // Create window
    createWindow();
  } catch (error) {
    console.error('Error starting app:', error);
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

app.on('will-quit', () => {
  stopBackend();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
