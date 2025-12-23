# admin-backend 性能分析指南

## 快速开始

### 1. 查看 PM2 实时日志

```bash
# 查看所有日志（最后 100 行）
pm2 logs --lines 100

# 查看特定应用的日志
pm2 logs admin-backend --lines 100

# 只看错误日志
pm2 logs admin-backend --err --lines 100

# 实时监控（类似 htop）
pm2 monit

# 查看特定进程的详细信息
pm2 describe admin-backend

# 查看进程的 CPU/内存使用
pm2 list
```

### 2. 检查日志文件

```bash
cd /home/ubuntu/telegram-ai-system/admin-backend

# 查看 logs 目录
ls -lh logs/

# 查看最新的错误日志
tail -100 logs/*.log | grep -i "error\|exception\|traceback"

# 查找死循环或重复错误
tail -500 logs/*.log | grep -i "error" | sort | uniq -c | sort -rn | head -20
```

### 3. 运行性能分析脚本

将以下文件上传到服务器，或直接在服务器上创建：

#### 方法 A: 使用 Shell 脚本

```bash
# 上传 analyze_admin_backend.sh 到服务器后
chmod +x analyze_admin_backend.sh
./analyze_admin_backend.sh
```

#### 方法 B: 使用 Python 脚本

```bash
# 上传 analyze_code_performance.py 到服务器后
chmod +x analyze_code_performance.py
python3 analyze_code_performance.py
```

## 常见性能问题检查清单

### ✅ 1. 检查死循环

**症状：**
- CPU 持续 100%
- 日志中重复出现相同错误
- 应用无响应

**检查方法：**
```bash
# 查看日志中的重复错误
pm2 logs admin-backend --err --lines 500 | grep -i "error" | sort | uniq -c | sort -rn

# 检查是否有无限循环
grep -rn "while True" /home/ubuntu/telegram-ai-system/admin-backend/app/
grep -rn "for.*in.*range.*:" /home/ubuntu/telegram-ai-system/admin-backend/app/
```

### ✅ 2. 检查同步阻塞操作

**症状：**
- 请求响应慢
- 并发请求时性能下降
- CPU 使用率低但响应慢

**检查方法：**
```bash
# 查找同步路由
grep -rn "@app\.\(get\|post\|put\|delete\)" /home/ubuntu/telegram-ai-system/admin-backend/app/ | grep -v "async def"

# 查找同步数据库操作
grep -rn "\.query\|\.get\|\.all()\|\.first()" /home/ubuntu/telegram-ai-system/admin-backend/app/ | grep -v "await"
```

**修复建议：**
- 将所有路由改为 `async def`
- 数据库操作使用 `await`
- 重计算任务放入 Celery 队列

### ✅ 3. 检查数据库连接池

**症状：**
- 数据库连接数过多
- 连接超时错误
- 内存泄漏

**检查方法：**
```bash
# 查看数据库配置文件
grep -A 10 "create_engine" /home/ubuntu/telegram-ai-system/admin-backend/app/*.py

# 检查是否有连接池配置
grep -i "pool_size\|max_overflow\|pool_pre_ping\|pool_recycle" /home/ubuntu/telegram-ai-system/admin-backend/app/*.py
```

**正确的配置示例：**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_size=10,              # 连接池大小
    max_overflow=20,           # 最大溢出连接数
    pool_pre_ping=True,        # 检测断开的连接
    pool_recycle=3600,         # 连接回收时间（秒）
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

**检查 Session 是否正确关闭：**
```bash
# 查找 Session 使用
grep -rn "SessionLocal\|sessionmaker" /home/ubuntu/telegram-ai-system/admin-backend/app/

# 检查是否有正确的上下文管理
grep -rn "with.*Session\|Depends.*Session" /home/ubuntu/telegram-ai-system/admin-backend/app/
```

### ✅ 4. 检查高计算量任务

**症状：**
- 某些请求特别慢
- CPU 在特定操作时飙升
- 请求超时

**检查方法：**
```bash
# 查找可能的重计算操作
grep -rn "for.*in.*range\|while.*True\|\.map\|\.filter\|sorted" /home/ubuntu/telegram-ai-system/admin-backend/app/

# 检查是否使用了异步队列
ls -la /home/ubuntu/telegram-ai-system/admin-backend/*celery*.py
ls -la /home/ubuntu/telegram-ai-system/admin-backend/tasks.py
```

**修复建议：**
- 将重计算任务放入 Celery 队列
- 使用异步处理
- 添加缓存机制

## 实时监控命令

### 监控 CPU 和内存

```bash
# 查看特定进程的资源使用
top -p $(pgrep -f "uvicorn.*admin-backend")

# 或使用 htop
htop -p $(pgrep -f "uvicorn.*admin-backend")

# PM2 监控
pm2 monit
```

### 监控数据库连接

```bash
# PostgreSQL
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity WHERE datname='your_database';"

# MySQL
mysql -u root -p -e "SHOW PROCESSLIST;"
```

### 监控网络连接

```bash
# 查看应用监听的端口
netstat -tlnp | grep uvicorn

# 查看连接数
netstat -an | grep ESTABLISHED | wc -l
```

## 性能优化建议

### 1. 使用异步路由

**错误示例：**
```python
@app.get("/users")
def get_users():
    users = db.query(User).all()  # 同步操作，阻塞
    return users
```

**正确示例：**
```python
@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = await db.execute(select(User))  # 异步操作
    return users.scalars().all()
```

### 2. 使用连接池

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 3. 使用 Celery 处理重任务

```python
# tasks.py
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def heavy_computation(data):
    # 重计算任务
    result = process_data(data)
    return result

# main.py
from tasks import heavy_computation

@app.post("/process")
async def process_data(data: dict):
    # 将任务放入队列，立即返回
    task = heavy_computation.delay(data)
    return {"task_id": task.id, "status": "processing"}
```

### 4. 正确关闭 Session

```python
# 使用依赖注入（推荐）
@app.get("/users")
async def get_users(db: Session = Depends(get_db)):
    users = await db.execute(select(User))
    return users.scalars().all()  # FastAPI 会自动关闭 Session

# 或使用上下文管理器
async def get_users():
    async with SessionLocal() as db:
        users = await db.execute(select(User))
        return users.scalars().all()
```

## 故障排查步骤

1. **查看 PM2 日志** - 检查是否有错误或异常
2. **检查 CPU 使用** - 确认是否有进程占用过高
3. **检查数据库连接** - 确认连接池配置正确
4. **检查代码** - 运行分析脚本查找问题
5. **测试修复** - 应用修复后重新测试

## 联系支持

如果问题持续存在，请提供：
- PM2 日志输出
- 分析脚本的输出
- 系统资源使用情况（top/htop 截图）
- 数据库连接数


