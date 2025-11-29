#!/usr/bin/env node
/**
 * 檢查 E2E 測試環境
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('========================================');
console.log('E2E 測試環境檢查');
console.log('========================================\n');

let allOk = true;

// 1. 檢查 package.json
console.log('1. 檢查 package.json...');
if (fs.existsSync('package.json')) {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  console.log('   ✓ package.json 存在');
  if (pkg.scripts && pkg.scripts['test:e2e']) {
    console.log('   ✓ test:e2e 腳本存在');
  } else {
    console.log('   ✗ test:e2e 腳本不存在');
    allOk = false;
  }
} else {
  console.log('   ✗ package.json 不存在');
  allOk = false;
}

console.log('');

// 2. 檢查 node_modules
console.log('2. 檢查依賴...');
if (fs.existsSync('node_modules')) {
  console.log('   ✓ node_modules 目錄存在');
  if (fs.existsSync('node_modules/@playwright/test')) {
    console.log('   ✓ @playwright/test 已安裝');
  } else {
    console.log('   ✗ @playwright/test 未安裝');
    allOk = false;
  }
} else {
  console.log('   ✗ node_modules 不存在，請運行 npm install');
  allOk = false;
}

console.log('');

// 3. 檢查測試文件
console.log('3. 檢查測試文件...');
const testDir = path.join(__dirname, 'e2e');
if (fs.existsSync(testDir)) {
  const testFiles = fs.readdirSync(testDir)
    .filter(file => file.endsWith('.spec.ts'));
  console.log(`   ✓ 找到 ${testFiles.length} 個測試文件:`);
  testFiles.forEach(file => console.log(`     - ${file}`));
} else {
  console.log('   ✗ e2e 目錄不存在');
  allOk = false;
}

console.log('');

// 4. 檢查 Playwright 配置
console.log('4. 檢查 Playwright 配置...');
if (fs.existsSync('playwright.config.ts')) {
  console.log('   ✓ playwright.config.ts 存在');
} else {
  console.log('   ✗ playwright.config.ts 不存在');
  allOk = false;
}

console.log('');

// 5. 嘗試檢查 Playwright 命令
console.log('5. 檢查 Playwright 命令...');
try {
  const version = execSync('npx playwright --version', {
    encoding: 'utf8',
    cwd: __dirname,
    stdio: 'pipe'
  }).trim();
  console.log(`   ✓ Playwright 可用 (${version})`);
} catch (error) {
  console.log('   ✗ Playwright 命令不可用');
  console.log(`   錯誤: ${error.message}`);
  allOk = false;
}

console.log('');

// 總結
console.log('========================================');
if (allOk) {
  console.log('✓ 環境檢查通過，可以運行測試');
  console.log('========================================\n');
  console.log('運行測試命令:');
  console.log('  npm run test:e2e');
  console.log('  或');
  console.log('  npx playwright test');
} else {
  console.log('✗ 環境檢查未通過，請修復上述問題');
  console.log('========================================\n');
  process.exit(1);
}
