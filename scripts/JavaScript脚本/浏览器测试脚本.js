// 在浏览器控制台中运行此脚本来测试按剧本聊天功能
(async function() {
    console.log("=== 开始测试按剧本聊天功能 ===");
    
    // 1. 获取token
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error("❌ 未找到token，请先登录");
        return;
    }
    console.log("✅ Token已获取");
    
    // 2. 获取账号列表
    try {
        const accountsResponse = await fetch('http://localhost:8000/api/v1/group-ai/accounts?page=1&page_size=100', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!accountsResponse.ok) {
            throw new Error(`HTTP ${accountsResponse.status}`);
        }
        
        const accountsData = await accountsResponse.json();
        const accounts = accountsData.items || accountsData;
        console.log(`✅ 获取到 ${accounts.length} 个账号`);
        
        // 查找在线账号
        const onlineAccounts = accounts.filter(acc => acc.status === 'online');
        console.log(`在线账号数: ${onlineAccounts.length}`);
        
        if (onlineAccounts.length === 0) {
            console.error("❌ 没有在线账号");
            return;
        }
        
        const testAccount = onlineAccounts[0];
        console.log(`使用账号: ${testAccount.account_id}`);
        
        // 3. 检查或创建群组
        let groupId = null;
        if (testAccount.group_count > 0) {
            console.log(`账号已有 ${testAccount.group_count} 个群组`);
            console.log("⚠️ 需要群组ID，请从账号详情中获取");
        } else {
            console.log("创建测试群组...");
            const groupTitle = `测试群组-${new Date().toISOString().slice(0,19).replace(/:/g,'')}`;
            const createResponse = await fetch('http://localhost:8000/api/v1/group-ai/groups/create', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    account_id: testAccount.account_id,
                    title: groupTitle,
                    description: '用于测试按剧本聊天功能',
                    auto_reply: true
                })
            });
            
            if (createResponse.ok) {
                const groupData = await createResponse.json();
                groupId = groupData.group_id;
                console.log(`✅ 群组创建成功: ${groupData.group_title} (ID: ${groupId})`);
            } else {
                const error = await createResponse.json();
                console.error(`❌ 创建群组失败: ${error.detail}`);
                return;
            }
        }
        
        // 4. 发送测试消息
        if (groupId) {
            console.log("\n发送测试消息...");
            const testMessages = ['你好', '新人', '欢迎'];
            
            for (const message of testMessages) {
                console.log(`\n测试消息: "${message}"`);
                
                try {
                    const sendResponse = await fetch('http://localhost:8000/api/v1/group-ai/groups/send-test-message', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            account_id: testAccount.account_id,
                            group_id: groupId,
                            message: message,
                            wait_for_reply: true,
                            wait_timeout: 10
                        })
                    });
                    
                    if (sendResponse.ok) {
                        const sendData = await sendResponse.json();
                        console.log(`✅ 消息发送成功 (ID: ${sendData.message_id})`);
                        if (sendData.reply_received) {
                            console.log(`✅ 检测到自动回复！回复数: ${sendData.reply_count_before} → ${sendData.reply_count_after}`);
                        } else {
                            console.log(`⏸️ 未检测到自动回复`);
                        }
                    } else {
                        const error = await sendResponse.json();
                        if (sendResponse.status === 404) {
                            console.error(`❌ API端点未加载 (404) - 需要重启后端服务`);
                        } else {
                            console.error(`❌ 发送失败: ${error.detail}`);
                        }
                    }
                } catch (err) {
                    console.error(`❌ 错误: ${err.message}`);
                }
                
                // 等待一段时间
                await new Promise(resolve => setTimeout(resolve, 3000));
            }
        }
        
        console.log("\n=== 测试完成 ===");
    } catch (err) {
        console.error(`❌ 错误: ${err.message}`);
    }
})();
