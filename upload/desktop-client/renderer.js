const { ipcRenderer } = require('electron');

const dropzone = document.getElementById('dropzone');
const urlBar = document.getElementById('url-bar');

dropzone.addEventListener('dragover', (event) => {
  event.preventDefault();
  event.stopPropagation();
});

dropzone.addEventListener('drop', (event) => {
  event.preventDefault();
  event.stopPropagation();

  const filePath = event.dataTransfer.files[0].path;
  const url = urlBar.value;

  ipcRenderer.send('upload-file', { filePath, url });
});

ipcRenderer.on('upload-success', () => {
  alert('File uploaded successfully!');
});

ipcRenderer.on('upload-error', () => {
  alert('Error uploading file!');
});