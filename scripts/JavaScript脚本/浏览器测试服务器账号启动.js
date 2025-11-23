// 在浏览器控制台中运行此脚本来测试服务器账号启动功能
(async function() {
    console.log("=== 测试服务器账号启动功能 ===");
    
    // 1. 获取token
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error("❌ 未找到token，请先登录");
        return;
    }
    console.log("✅ Token已获取");
    
    const baseUrl = "http://localhost:8000/api/v1";
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    
    // 2. 获取账号列表
    try {
        console.log("\n获取账号列表...");
        const accountsResponse = await fetch(`${baseUrl}/group-ai/accounts?page=1&page_size=100`, {
            headers: headers
        });
        
        if (!accountsResponse.ok) {
            throw new Error(`HTTP ${accountsResponse.status}`);
        }
        
        const accountsData = await accountsResponse.json();
        const accounts = accountsData.items || accountsData;
        console.log(`✅ 获取到 ${accounts.length} 个账号`);
        
        // 查找已分配到服务器的账号
        const serverAccounts = accounts.filter(acc => acc.server_id && acc.server_id !== "");
        console.log(`\n已分配到服务器的账号: ${serverAccounts.length} 个`);
        
        if (serverAccounts.length === 0) {
            console.warn("⚠️  没有已分配到服务器的账号");
            console.log("建议：使用前端界面批量创建账号，系统会自动分配服务器");
            return;
        }
        
        // 显示已分配的账号
        console.log("\n已分配的账号列表：");
        serverAccounts.forEach(acc => {
            console.log(`  - ${acc.account_id}: 服务器=${acc.server_id}, 状态=${acc.status}`);
        });
        
        // 选择第一个账号进行测试
        const testAccount = serverAccounts[0];
        console.log(`\n选择测试账号: ${testAccount.account_id}`);
        console.log(`服务器: ${testAccount.server_id}`);
        console.log(`当前状态: ${testAccount.status}`);
        
        // 3. 测试启动账号
        console.log("\n发送启动请求...");
        const startResponse = await fetch(`${baseUrl}/group-ai/accounts/${testAccount.account_id}/start`, {
            method: 'POST',
            headers: headers
        });
        
        if (!startResponse.ok) {
            const error = await startResponse.json();
            console.error(`❌ 启动失败: ${error.detail}`);
            return;
        }
        
        const startResult = await startResponse.json();
        console.log(`✅ 启动请求成功`);
        console.log(`消息: ${startResult.message}`);
        
        if (startResult.server_id) {
            console.log(`✅ 账号在服务器 ${startResult.server_id} 上启动`);
        } else {
            console.warn(`⚠️  账号在本地启动（未指定服务器）`);
        }
        
        // 等待几秒
        console.log("\n等待5秒让账号启动...");
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // 4. 检查账号状态
        console.log("\n检查账号状态...");
        const accountResponse = await fetch(`${baseUrl}/group-ai/accounts/${testAccount.account_id}`, {
            headers: headers
        });
        
        if (!accountResponse.ok) {
            console.error(`❌ 获取账号状态失败: HTTP ${accountResponse.status}`);
            return;
        }
        
        const account = await accountResponse.json();
        console.log(`账号状态: ${account.status}`);
        console.log(`服务器ID: ${account.server_id}`);
        
        if (account.status === "online") {
            console.log("✅ 账号启动成功并在线");
        } else if (account.status === "error") {
            console.error("❌ 账号启动失败（状态: error）");
            console.log("可能原因：");
            console.log("  - Telegram连接失败");
            console.log("  - Session文件无效或已过期");
            console.log("  - 服务器上的启动命令执行失败");
        } else {
            console.warn(`⚠️  账号状态: ${account.status}`);
        }
        
        // 5. 测试结果汇总
        console.log("\n=== 测试结果汇总 ===");
        console.log(`测试账号: ${testAccount.account_id}`);
        console.log(`服务器分配: ${account.server_id}`);
        console.log(`账号状态: ${account.status}`);
        console.log("\n✅ 测试完成");
        
    } catch (err) {
        console.error(`❌ 错误: ${err.message}`);
    }
})();

