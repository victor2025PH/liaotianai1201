#!/usr/bin/env node
/**
 * 快速運行 E2E 測試並顯示結果
 */
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('========================================');
console.log('開始運行 E2E 測試');
console.log('========================================');
console.log('');

// 列出測試文件
const testDir = path.join(__dirname, 'e2e');
const testFiles = fs.readdirSync(testDir)
  .filter(file => file.endsWith('.spec.ts'))
  .map(file => `  - ${file}`);

console.log('測試文件列表:');
testFiles.forEach(file => console.log(file));
console.log('');

// 運行測試
console.log('開始運行測試...');
console.log('注意：這可能需要幾分鐘時間');
console.log('');

try {
  const output = execSync('npx playwright test --reporter=list,html', {
    encoding: 'utf8',
    cwd: __dirname,
    stdio: 'inherit'
  });
  
  console.log('');
  console.log('========================================');
  console.log('✓ 測試完成');
  console.log('========================================');
  console.log('');
  console.log('查看 HTML 報告: npx playwright show-report');
  
} catch (error) {
  console.log('');
  console.log('========================================');
  console.log('✗ 測試執行出錯');
  console.log('========================================');
  console.log('');
  console.log('錯誤:', error.message);
  process.exit(1);
}
