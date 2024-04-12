const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.loadFile('index.html');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.on('upload-file', (event, { filePath, url }) => {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));

  const boundary = formData.getBoundary();

  axios.post(url, formData, {
    headers: {
      ...formData.getHeaders(),
      'Content-Type': `multipart/form-data; boundary=${boundary}`,
    },
  })
    .then((response) => {
      console.log('File uploaded successfully:', response.data);
      event.reply('upload-success');
    })
    .catch((error) => {
      console.error('Error uploading file:', error);
      event.reply('upload-error');
    });
});