# 检查Standalone模式

Next.js配置中使用了 `output: "standalone"`，这意味着：
- 构建输出在 `.next/standalone` 目录
- 服务应该从 `.next/standalone` 目录运行

请在服务器上执行以下命令：

## 1. 检查standalone目录中的路由文件

```bash
cd /home/ubuntu/liaotian/saas-demo
ls -la .next/standalone/liaotian/saas-demo/.next/server/app/group-ai/accounts/page.js
```

## 2. 检查服务配置

```bash
cat /etc/systemd/system/liaotian-frontend.service
```

查看 `WorkingDirectory` 和 `ExecStart` 是否正确指向standalone目录。

## 3. 如果服务从standalone目录运行

需要确保standalone目录中的文件是最新的。standalone模式需要：
- 从 `.next/standalone` 目录运行
- 或者从项目根目录运行，但Next.js会自动使用standalone目录

## 4. 重新构建standalone输出

如果standalone目录中的文件不是最新的，需要重新构建：

```bash
cd /home/ubuntu/liaotian/saas-demo
rm -rf .next/standalone
npm run build
```

## 5. 检查服务日志

```bash
sudo journalctl -u liaotian-frontend -n 50 --no-pager
```

查看是否有路由相关的错误信息。

