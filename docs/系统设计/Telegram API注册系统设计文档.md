# Telegram API 注册系统设计文档

## 1. 系统概述

### 1.1 系统目标
构建一个完整的网页注册系统，支持用户通过手机号码注册Telegram API，实现OTP验证、Session文件管理、防风控机制和服务器选择等功能。

### 1.2 核心功能
- 手机号注册与验证
- OTP自动接收与手动输入
- Session文件生成与管理
- 多服务器支持
- 防风控机制
- 实时状态监控

### 1.3 技术栈
- **前端**: React + TypeScript + Ant Design
- **后端**: FastAPI + Python
- **数据库**: PostgreSQL (用户数据) + SQLite (Session文件)
- **通信**: WebSocket (实时状态) + REST API
- **安全**: JWT认证 + 速率限制 + 行为监控

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  注册页面    │  │  Session管理  │  │  服务器选择  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                 │
│                    WebSocket + REST API                      │
└────────────────────────────┼─────────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────────┐
│                    API网关层 (API Gateway)                     │
├─────────────────────────────┼─────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  认证服务    │  │  速率限制    │  │  日志记录    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────┼─────────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────────┐
│                      业务逻辑层 (Backend)                       │
├─────────────────────────────┼─────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 注册服务     │  │ Session服务  │  │ 风控服务     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ OTP服务      │  │ 服务器管理   │  │ 监控服务     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────┼─────────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────────┐
│                      数据存储层 (Storage)                      │
├─────────────────────────────┼─────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │  Redis缓存   │  │ Session文件  │      │
│  │ (用户数据)   │  │ (状态缓存)   │  │ (服务器存储) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────────┐
│                      外部服务层 (External)                      │
├─────────────────────────────┼─────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Telegram API │  │ 代理服务     │  │ 监控告警     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

#### 2.2.1 前端模块
- **注册模块** (`RegisterModule`)
  - 手机号输入与验证
  - OTP接收与输入
  - 倒计时显示
  - 状态提示

- **Session管理模块** (`SessionManagementModule`)
  - Session列表展示
  - Session文件下载
  - Session状态监控
  - Session删除

- **服务器选择模块** (`ServerSelectionModule`)
  - 服务器列表
  - 服务器状态
  - 负载均衡

- **风控提示模块** (`AntiDetectionModule`)
  - 操作提示
  - 风险评估
  - 行为建议

#### 2.2.2 后端模块
- **注册服务** (`RegistrationService`)
  - 手机号验证
  - OTP发送
  - Session生成
  - 状态管理

- **Session服务** (`SessionService`)
  - Session文件管理
  - Session验证
  - Session加密存储
  - Session同步

- **风控服务** (`AntiDetectionService`)
  - 行为监控
  - 风险评估
  - 速率限制
  - 异常检测

- **服务器管理服务** (`ServerManagementService`)
  - 服务器状态监控
  - 负载均衡
  - 故障转移

## 3. 数据库设计

### 3.1 用户注册表 (user_registrations)

```sql
CREATE TABLE user_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    api_id INTEGER,
    api_hash VARCHAR(64),
    node_id VARCHAR(50) NOT NULL,
    session_name VARCHAR(100),
    session_file_path TEXT,
    status VARCHAR(20) NOT NULL, -- pending, code_sent, verified, completed, failed
    phone_code_hash VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    risk_score INTEGER DEFAULT 0, -- 0-100, 风险评分
    user_agent TEXT,
    ip_address INET,
    CONSTRAINT unique_phone_node UNIQUE (phone, node_id)
);

CREATE INDEX idx_user_registrations_phone ON user_registrations(phone);
CREATE INDEX idx_user_registrations_status ON user_registrations(status);
CREATE INDEX idx_user_registrations_node_id ON user_registrations(node_id);
CREATE INDEX idx_user_registrations_created_at ON user_registrations(created_at);
```

### 3.2 Session文件表 (session_files)

```sql
CREATE TABLE session_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_id UUID REFERENCES user_registrations(id),
    session_name VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64), -- SHA256 hash
    server_node_id VARCHAR(50) NOT NULL,
    is_encrypted BOOLEAN DEFAULT FALSE,
    encryption_key_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP,
    is_valid BOOLEAN DEFAULT TRUE,
    metadata JSONB -- 存储额外信息
);

CREATE INDEX idx_session_files_registration_id ON session_files(registration_id);
CREATE INDEX idx_session_files_server_node_id ON session_files(server_node_id);
CREATE INDEX idx_session_files_is_valid ON session_files(is_valid);
```

### 3.3 风控日志表 (anti_detection_logs)

```sql
CREATE TABLE anti_detection_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_id UUID REFERENCES user_registrations(id),
    event_type VARCHAR(50) NOT NULL, -- registration_start, code_sent, code_verified, etc.
    risk_level VARCHAR(20), -- low, medium, high, critical
    risk_score INTEGER,
    ip_address INET,
    user_agent TEXT,
    device_fingerprint VARCHAR(100),
    behavior_pattern JSONB,
    action_taken VARCHAR(100), -- allowed, blocked, rate_limited
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_anti_detection_logs_registration_id ON anti_detection_logs(registration_id);
CREATE INDEX idx_anti_detection_logs_event_type ON anti_detection_logs(event_type);
CREATE INDEX idx_anti_detection_logs_risk_level ON anti_detection_logs(risk_level);
CREATE INDEX idx_anti_detection_logs_created_at ON anti_detection_logs(created_at);
```

### 3.4 服务器状态表 (server_status)

```sql
CREATE TABLE server_status (
    node_id VARCHAR(50) PRIMARY KEY,
    host VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL, -- online, offline, maintenance
    current_registrations INTEGER DEFAULT 0,
    max_registrations INTEGER DEFAULT 10,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    disk_usage DECIMAL(5,2),
    last_heartbeat TIMESTAMP,
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 4. API接口设计

### 4.1 注册相关接口

#### 4.1.1 开始注册
```http
POST /api/v1/telegram-registration/start
Content-Type: application/json
Authorization: Bearer {token}

Request Body:
{
  "phone": "+1234567890",
  "country_code": "+1",
  "node_id": "worker-01",
  "api_id": 12345678,  // 可选
  "api_hash": "abc123...",  // 可选
  "session_name": "my_session",  // 可选
  "use_proxy": false,
  "proxy_url": "socks5://127.0.0.1:1080"  // 可选
}

Response 200:
{
  "registration_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "code_sent",
  "message": "验证码已发送",
  "phone_code_hash": "abc123...",
  "expires_in": 300,  // 秒
  "retry_after": 60  // 秒，如果被限流
}
```

#### 4.1.2 验证OTP
```http
POST /api/v1/telegram-registration/verify
Content-Type: application/json
Authorization: Bearer {token}

Request Body:
{
  "registration_id": "550e8400-e29b-41d4-a716-446655440000",
  "code": "12345",
  "password": "2fa_password"  // 可选，如果需要两步验证
}

Response 200:
{
  "registration_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "message": "注册成功",
  "session_file": {
    "session_name": "my_session",
    "file_path": "/home/ubuntu/sessions/my_session.session",
    "server_node_id": "worker-01",
    "file_size": 28672,
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### 4.1.3 查询注册状态
```http
GET /api/v1/telegram-registration/status/{registration_id}
Authorization: Bearer {token}

Response 200:
{
  "registration_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "code_sent",
  "message": "等待验证码输入",
  "phone": "+1234567890",
  "node_id": "worker-01",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:05Z",
  "expires_at": "2024-01-01T12:05:00Z",
  "risk_score": 25
}
```

#### 4.1.4 取消注册
```http
POST /api/v1/telegram-registration/cancel
Content-Type: application/json
Authorization: Bearer {token}

Request Body:
{
  "registration_id": "550e8400-e29b-41d4-a716-446655440000"
}

Response 200:
{
  "message": "注册已取消"
}
```

### 4.2 Session管理接口

#### 4.2.1 获取Session列表
```http
GET /api/v1/sessions?node_id={node_id}&page=1&page_size=20
Authorization: Bearer {token}

Response 200:
{
  "items": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "session_name": "my_session",
      "phone": "+1234567890",
      "node_id": "worker-01",
      "file_path": "/home/ubuntu/sessions/my_session.session",
      "file_size": 28672,
      "is_valid": true,
      "created_at": "2024-01-01T12:00:00Z",
      "last_verified_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

#### 4.2.2 下载Session文件
```http
GET /api/v1/sessions/{session_id}/download
Authorization: Bearer {token}

Response 200:
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="my_session.session"
[Binary Session File Data]
```

#### 4.2.3 删除Session
```http
DELETE /api/v1/sessions/{session_id}
Authorization: Bearer {token}

Response 200:
{
  "message": "Session已删除"
}
```

#### 4.2.4 验证Session
```http
POST /api/v1/sessions/{session_id}/verify
Authorization: Bearer {token}

Response 200:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_valid": true,
  "user_info": {
    "user_id": 123456789,
    "username": "my_username",
    "first_name": "John",
    "last_name": "Doe"
  },
  "verified_at": "2024-01-01T12:00:00Z"
}
```

### 4.3 服务器管理接口

#### 4.3.1 获取服务器列表
```http
GET /api/v1/servers
Authorization: Bearer {token}

Response 200:
{
  "servers": [
    {
      "node_id": "worker-01",
      "host": "165.154.254.99",
      "status": "online",
      "current_registrations": 5,
      "max_registrations": 10,
      "cpu_usage": 45.2,
      "memory_usage": 62.8,
      "disk_usage": 35.1,
      "last_heartbeat": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### 4.3.2 获取服务器推荐
```http
GET /api/v1/servers/recommend?phone={phone}
Authorization: Bearer {token}

Response 200:
{
  "recommended_node_id": "worker-01",
  "reason": "负载最低",
  "alternatives": [
    {
      "node_id": "los-angeles",
      "reason": "地理位置接近"
    }
  ]
}
```

### 4.4 风控相关接口

#### 4.4.1 获取风控提示
```http
GET /api/v1/anti-detection/tips?phone={phone}
Authorization: Bearer {token}

Response 200:
{
  "tips": [
    {
      "type": "rate_limit",
      "message": "建议等待60秒后再试",
      "priority": "high"
    },
    {
      "type": "device_info",
      "message": "建议使用不同的设备信息",
      "priority": "medium"
    }
  ],
  "risk_score": 35,
  "recommendations": [
    "使用代理服务器",
    "增加操作间隔时间"
  ]
}
```

#### 4.4.2 获取注册历史
```http
GET /api/v1/telegram-registration/history?phone={phone}&days=7
Authorization: Bearer {token}

Response 200:
{
  "phone": "+1234567890",
  "total_registrations": 3,
  "successful": 2,
  "failed": 1,
  "last_registration": "2024-01-01T12:00:00Z",
  "registrations": [
    {
      "registration_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "node_id": "worker-01",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

## 5. 前端界面设计

### 5.1 注册页面组件结构

```
RegisterPage
├── PhoneInputStep
│   ├── PhoneNumberInput
│   ├── CountryCodeSelector
│   ├── ServerSelector
│   ├── AdvancedOptions (Collapsible)
│   │   ├── ApiCredentialsInput
│   │   ├── ProxySettings
│   │   └── SessionNameInput
│   └── AntiDetectionTips
├── OTPVerificationStep
│   ├── OTPInput
│   ├── CountdownTimer
│   ├── ResendCodeButton
│   ├── TwoFactorPasswordInput (Conditional)
│   └── StatusIndicator
└── CompletionStep
    ├── SuccessMessage
    ├── SessionInfo
    ├── DownloadButton
    └── CreateAnotherButton
```

### 5.2 状态管理

```typescript
interface RegistrationState {
  currentStep: 'phone' | 'otp' | 'complete';
  registrationId: string | null;
  phone: string;
  countryCode: string;
  nodeId: string;
  status: 'idle' | 'sending' | 'code_sent' | 'verifying' | 'completed' | 'failed';
  phoneCodeHash: string | null;
  expiresAt: Date | null;
  countdown: number;
  error: string | null;
  sessionFile: SessionFile | null;
  riskScore: number;
  tips: AntiDetectionTip[];
}
```

### 5.3 关键组件实现

#### 5.3.1 倒计时组件
```typescript
interface CountdownTimerProps {
  expiresAt: Date;
  onExpire: () => void;
}

const CountdownTimer: React.FC<CountdownTimerProps> = ({ expiresAt, onExpire }) => {
  const [remaining, setRemaining] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      const diff = Math.max(0, Math.floor((expiresAt.getTime() - Date.now()) / 1000));
      setRemaining(diff);
      if (diff === 0) {
        onExpire();
        clearInterval(interval);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [expiresAt, onExpire]);
  
  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;
  
  return (
    <div className="countdown-timer">
      {remaining > 0 ? (
        <span>{String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}</span>
      ) : (
        <span>已过期</span>
      )}
    </div>
  );
};
```

#### 5.3.2 OTP输入组件
```typescript
interface OTPInputProps {
  length: number;
  onComplete: (code: string) => void;
  autoFocus?: boolean;
}

const OTPInput: React.FC<OTPInputProps> = ({ length, onComplete, autoFocus }) => {
  const [values, setValues] = useState<string[]>(Array(length).fill(''));
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);
  
  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    
    const newValues = [...values];
    newValues[index] = value.slice(-1);
    setValues(newValues);
    
    if (value && index < length - 1) {
      inputRefs.current[index + 1]?.focus();
    }
    
    if (newValues.every(v => v)) {
      onComplete(newValues.join(''));
    }
  };
  
  // ... 渲染逻辑
};
```

## 6. 防风控机制

### 6.1 风险评估模型

```python
class RiskAssessmentModel:
    """风险评估模型"""
    
    def calculate_risk_score(self, registration_data: dict) -> int:
        """
        计算风险评分 (0-100)
        0-25: 低风险
        26-50: 中风险
        51-75: 高风险
        76-100: 极高风险
        """
        score = 0
        
        # 1. 频率检查 (0-30分)
        recent_count = self.get_recent_registrations(registration_data['phone'], hours=24)
        score += min(30, recent_count * 10)
        
        # 2. IP检查 (0-25分)
        ip_count = self.get_registrations_by_ip(registration_data['ip_address'], hours=1)
        score += min(25, ip_count * 8)
        
        # 3. 设备指纹检查 (0-20分)
        device_count = self.get_registrations_by_device(registration_data['device_fingerprint'], hours=24)
        score += min(20, device_count * 5)
        
        # 4. 行为模式检查 (0-15分)
        behavior_score = self.analyze_behavior_pattern(registration_data)
        score += behavior_score
        
        # 5. 代理检查 (0-10分)
        if not registration_data.get('use_proxy'):
            score += 5  # 未使用代理增加风险
        
        return min(100, score)
    
    def should_block(self, risk_score: int) -> bool:
        """判断是否应该阻止注册"""
        return risk_score >= 75
```

### 6.2 速率限制策略

```python
class RateLimiter:
    """速率限制器"""
    
    RATE_LIMITS = {
        'per_phone_per_hour': 3,      # 每个手机号每小时最多3次
        'per_phone_per_day': 10,       # 每个手机号每天最多10次
        'per_ip_per_hour': 5,          # 每个IP每小时最多5次
        'per_ip_per_day': 20,          # 每个IP每天最多20次
        'per_device_per_day': 15,      # 每个设备每天最多15次
        'global_per_minute': 30,       # 全局每分钟最多30次
    }
    
    def check_rate_limit(self, registration_data: dict) -> tuple[bool, str, int]:
        """
        检查速率限制
        返回: (是否允许, 错误消息, 重试等待时间(秒))
        """
        phone = registration_data['phone']
        ip_address = registration_data['ip_address']
        device_fingerprint = registration_data.get('device_fingerprint')
        
        # 检查手机号限制
        phone_hourly = self.get_count('phone', phone, hours=1)
        if phone_hourly >= self.RATE_LIMITS['per_phone_per_hour']:
            return False, f"手机号 {phone} 已达到每小时限制", 3600
        
        phone_daily = self.get_count('phone', phone, hours=24)
        if phone_daily >= self.RATE_LIMITS['per_phone_per_day']:
            return False, f"手机号 {phone} 已达到每天限制", 86400
        
        # 检查IP限制
        ip_hourly = self.get_count('ip', ip_address, hours=1)
        if ip_hourly >= self.RATE_LIMITS['per_ip_per_hour']:
            return False, f"IP地址已达到每小时限制", 3600
        
        # 检查全局限制
        global_minute = self.get_global_count(minutes=1)
        if global_minute >= self.RATE_LIMITS['global_per_minute']:
            return False, "系统繁忙，请稍后重试", 60
        
        return True, "", 0
```

### 6.3 行为监控

```python
class BehaviorMonitor:
    """行为监控器"""
    
    def monitor_registration(self, registration_data: dict):
        """监控注册行为"""
        behaviors = []
        
        # 1. 输入速度分析
        input_times = registration_data.get('input_times', [])
        if len(input_times) > 1:
            avg_time = sum(input_times[i+1] - input_times[i] for i in range(len(input_times)-1)) / (len(input_times)-1)
            if avg_time < 0.5:  # 平均输入间隔小于0.5秒
                behaviors.append({
                    'type': 'suspicious_input_speed',
                    'severity': 'medium',
                    'message': '输入速度异常快，可能是自动化工具'
                })
        
        # 2. 鼠标移动轨迹
        mouse_trajectory = registration_data.get('mouse_trajectory', [])
        if mouse_trajectory:
            if self.is_linear_trajectory(mouse_trajectory):
                behaviors.append({
                    'type': 'suspicious_mouse_movement',
                    'severity': 'high',
                    'message': '鼠标移动轨迹过于线性，可能是自动化工具'
                })
        
        # 3. 键盘事件分析
        key_events = registration_data.get('key_events', [])
        if key_events:
            if self.has_uniform_timing(key_events):
                behaviors.append({
                    'type': 'suspicious_key_timing',
                    'severity': 'medium',
                    'message': '按键时间间隔过于均匀'
                })
        
        return behaviors
```

### 6.4 用户提示系统

```typescript
interface AntiDetectionTip {
  type: 'rate_limit' | 'device_info' | 'proxy' | 'timing' | 'behavior';
  priority: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  action?: string;
  icon?: string;
}

const getAntiDetectionTips = (riskScore: number, registrationData: RegistrationData): AntiDetectionTip[] => {
  const tips: AntiDetectionTip[] = [];
  
  if (riskScore > 50) {
    tips.push({
      type: 'proxy',
      priority: 'high',
      message: '建议使用代理服务器以降低风险',
      action: '配置代理',
      icon: 'shield'
    });
  }
  
  if (riskScore > 30) {
    tips.push({
      type: 'timing',
      priority: 'medium',
      message: '建议等待60秒后再进行注册',
      action: '等待',
      icon: 'clock-circle'
    });
  }
  
  // ... 更多提示逻辑
  
  return tips;
};
```

## 7. 安全设计

### 7.1 数据加密

```python
class SessionEncryption:
    """Session文件加密"""
    
    def encrypt_session(self, session_data: bytes, key: str) -> bytes:
        """使用AES-256-GCM加密Session文件"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import os
        
        aesgcm = AESGCM(key.encode())
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, session_data, None)
        return nonce + ciphertext
    
    def decrypt_session(self, encrypted_data: bytes, key: str) -> bytes:
        """解密Session文件"""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        aesgcm = AESGCM(key.encode())
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)
```

### 7.2 访问控制

```python
class AccessControl:
    """访问控制"""
    
    PERMISSIONS = {
        'registration:create': ['user', 'admin'],
        'registration:view': ['user', 'admin'],
        'session:download': ['user', 'admin'],
        'session:delete': ['admin'],
        'server:manage': ['admin'],
    }
    
    def check_permission(self, user_role: str, permission: str) -> bool:
        """检查用户权限"""
        allowed_roles = self.PERMISSIONS.get(permission, [])
        return user_role in allowed_roles
```

### 7.3 日志审计

```python
class AuditLogger:
    """审计日志"""
    
    def log_registration_event(self, event_type: str, registration_data: dict, user_id: str):
        """记录注册事件"""
        log_entry = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'registration_id': registration_data.get('registration_id'),
            'phone': registration_data.get('phone'),
            'ip_address': registration_data.get('ip_address'),
            'user_agent': registration_data.get('user_agent'),
            'risk_score': registration_data.get('risk_score'),
            'action_taken': registration_data.get('action_taken'),
        }
        
        # 写入数据库
        self.db.insert('audit_logs', log_entry)
        
        # 高风险事件发送告警
        if registration_data.get('risk_score', 0) > 75:
            self.send_alert(log_entry)
```

## 8. 部署方案

### 8.1 容器化部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./admin-backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/telegram_reg
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  
  frontend:
    build: ./admin-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    depends_on:
      - backend
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=telegram_reg
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### 8.2 监控与告警

```python
class MonitoringService:
    """监控服务"""
    
    METRICS = {
        'registration_success_rate': Gauge('registration_success_rate', '注册成功率'),
        'registration_duration': Histogram('registration_duration_seconds', '注册耗时'),
        'active_registrations': Gauge('active_registrations', '活跃注册数'),
        'risk_score_distribution': Histogram('risk_score', '风险评分分布'),
    }
    
    def record_registration(self, success: bool, duration: float, risk_score: int):
        """记录注册指标"""
        self.METRICS['registration_success_rate'].set(1.0 if success else 0.0)
        self.METRICS['registration_duration'].observe(duration)
        self.METRICS['risk_score_distribution'].observe(risk_score)
```

## 9. 测试策略

### 9.1 单元测试

```python
class TestRegistrationService:
    """注册服务测试"""
    
    def test_phone_validation(self):
        """测试手机号验证"""
        service = RegistrationService()
        assert service.validate_phone("+1234567890") == True
        assert service.validate_phone("1234567890") == False
        assert service.validate_phone("+123") == False
    
    def test_rate_limiting(self):
        """测试速率限制"""
        limiter = RateLimiter()
        registration_data = {
            'phone': '+1234567890',
            'ip_address': '192.168.1.1',
        }
        
        # 第一次应该允许
        allowed, msg, wait = limiter.check_rate_limit(registration_data)
        assert allowed == True
        
        # 快速连续请求应该被限制
        for _ in range(5):
            limiter.record_registration(registration_data)
        
        allowed, msg, wait = limiter.check_rate_limit(registration_data)
        assert allowed == False
```

### 9.2 集成测试

```python
class TestRegistrationFlow:
    """注册流程集成测试"""
    
    async def test_complete_registration_flow(self):
        """测试完整注册流程"""
        # 1. 开始注册
        response = await client.post("/api/v1/telegram-registration/start", json={
            "phone": "+1234567890",
            "node_id": "worker-01"
        })
        assert response.status_code == 200
        registration_id = response.json()["registration_id"]
        
        # 2. 验证OTP
        response = await client.post("/api/v1/telegram-registration/verify", json={
            "registration_id": registration_id,
            "code": "12345"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
```

## 10. 性能优化

### 10.1 缓存策略

```python
class CacheManager:
    """缓存管理"""
    
    def get_server_status(self, node_id: str) -> dict:
        """获取服务器状态（带缓存）"""
        cache_key = f"server_status:{node_id}"
        cached = redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 从数据库获取
        status = self.db.get_server_status(node_id)
        
        # 缓存30秒
        redis.setex(cache_key, 30, json.dumps(status))
        return status
```

### 10.2 异步处理

```python
@router.post("/start")
async def start_registration(
    request: RegistrationRequest,
    background_tasks: BackgroundTasks
):
    """异步处理注册请求"""
    registration_id = str(uuid.uuid4())
    
    # 在后台任务中处理
    background_tasks.add_task(
        process_registration,
        registration_id,
        request
    )
    
    return {
        "registration_id": registration_id,
        "status": "pending"
    }
```

## 11. 文档与API规范

### 11.1 OpenAPI规范

系统遵循OpenAPI 3.0规范，完整的API文档可通过 `/docs` 端点访问。

### 11.2 错误码规范

```python
ERROR_CODES = {
    'PHONE_INVALID': (400, '手机号格式无效'),
    'PHONE_BANNED': (403, '手机号已被封禁'),
    'RATE_LIMIT_EXCEEDED': (429, '速率限制超出'),
    'OTP_EXPIRED': (400, '验证码已过期'),
    'OTP_INVALID': (400, '验证码无效'),
    'SESSION_GENERATION_FAILED': (500, 'Session生成失败'),
    'SERVER_UNAVAILABLE': (503, '服务器不可用'),
    'RISK_SCORE_TOO_HIGH': (403, '风险评分过高，注册被阻止'),
}
```

## 12. 总结

本系统设计文档详细描述了Telegram API注册系统的完整架构、功能模块、API接口、数据库设计、安全机制和部署方案。系统采用模块化设计，具有良好的可扩展性和可维护性，能够有效支持用户注册流程，同时通过完善的风控机制保障系统安全。

