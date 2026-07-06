// Script to install native module for the current architecture
const { execSync } = require('child_process');
const os = require('os');

const arch = os.arch();
let targetArch;
if (arch === 'arm64') {
  targetArch = 'arm64';
} else if (arch === 'x64') {
  targetArch = 'x64';
} else {
  console.error('Unsupported architecture:', arch);
  process.exit(1);
}

console.log(`Installing native module for ${targetArch}...`);
execSync(`npm rebuild --arch=${targetArch} --target_arch=${targetArch}`, { stdio: 'inherit' });
console.log('Native module installation complete.');