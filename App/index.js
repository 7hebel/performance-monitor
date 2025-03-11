const { app, BrowserWindow } = require('electron');

app.on('ready', () => {
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: __dirname + '/preload.js'
        }
    });
    
    mainWindow.setMenu(null);
    mainWindow.loadFile('index.html');
    mainWindow.webContents.openDevTools();
});
