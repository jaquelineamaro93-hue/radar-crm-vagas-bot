// Busca token do Vercel CLI via keychain do Windows
const path = require('path');
const appData = process.env.APPDATA;

// Vercel CLI v39+ usa @vercel/client que por sua vez usa o 'keytar'
// O keytar.node fica dentro do pacote instalado globalmente
// Caminho alternativo: vercel usa o módulo 'conf' para armazenar config

// Tentativa 1: conf module (versões mais antigas)
const confPaths = [
  path.join(require('os').homedir(), '.vercel', 'auth.json'),
  path.join(appData, 'vercel', 'auth.json'),
  path.join(require('os').homedir(), '.config', 'vercel', 'auth.json'),
];

const fs = require('fs');
for (const p of confPaths) {
  if (fs.existsSync(p)) {
    console.log('FOUND FILE:', p);
    console.log(fs.readFileSync(p, 'utf8'));
    process.exit(0);
  }
}

// Tentativa 2: node-keytar via Windows Credential Manager
try {
  // Procura o keytar dentro dos módulos do vercel
  const vercelPath = path.join(appData, 'npm', 'node_modules', 'vercel');
  const nodeModulesPath = path.join(vercelPath, 'node_modules');

  // Lista todos os módulos para achar keytar
  if (fs.existsSync(nodeModulesPath)) {
    const mods = fs.readdirSync(nodeModulesPath);
    const keytarMod = mods.find(m => m === 'keytar');
    if (keytarMod) {
      const keytar = require(path.join(nodeModulesPath, keytarMod));
      keytar.getPassword('Vercel CLI', 'token').then(token => {
        console.log('TOKEN:', token);
      });
      return;
    }
  }
  console.log('keytar not found in node_modules');
} catch(e) {
  console.log('Error:', e.message);
}

// Tentativa 3: via @vercel/client ou similar
try {
  const vercelClient = require(path.join(appData, 'npm', 'node_modules', 'vercel', 'dist', 'vc.js'));
  console.log('vercel client loaded');
} catch(e) {
  console.log('client err:', e.message.substring(0, 80));
}
