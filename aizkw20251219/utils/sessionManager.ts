/**
 * 会话管理工具
 * 管理用户会话 ID，支持多设备同步（可选）
 */

const SESSION_KEY = 'ai_chat_session_id';
const SESSION_VERSION = '1.0';

interface SessionData {
  sessionId: string;
  createdAt: number;
  lastActiveAt: number;
  version: string;
}

/**
 * 生成新的会话 ID
 */
function generateSessionId(): string {
  // 使用时间戳 + 随机字符串生成唯一 ID
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `session_${timestamp}_${random}`;
}

/**
 * 获取或创建会话 ID
 */
export function getSessionId(): string {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      const sessionData: SessionData = JSON.parse(stored);
      
      // 检查版本兼容性
      if (sessionData.version !== SESSION_VERSION) {
        // 版本不兼容，创建新会话
        return createNewSession();
      }
      
      // 检查会话是否过期（30天）
      const THIRTY_DAYS = 30 * 24 * 60 * 60 * 1000;
      if (Date.now() - sessionData.createdAt > THIRTY_DAYS) {
        // 会话过期，创建新会话
        return createNewSession();
      }
      
      // 更新最后活跃时间
      sessionData.lastActiveAt = Date.now();
      localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
      
      return sessionData.sessionId;
    }
    
    // 没有存储的会话，创建新会话
    return createNewSession();
  } catch (error) {
    console.warn('获取会话 ID 失败:', error);
    return createNewSession();
  }
}

/**
 * 创建新会话
 */
function createNewSession(): string {
  const sessionId = generateSessionId();
  const sessionData: SessionData = {
    sessionId,
    createdAt: Date.now(),
    lastActiveAt: Date.now(),
    version: SESSION_VERSION,
  };
  
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
  } catch (error) {
    console.warn('保存会话 ID 失败:', error);
  }
  
  return sessionId;
}

/**
 * 更新会话活跃时间
 */
export function updateSessionActivity(): void {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      const sessionData: SessionData = JSON.parse(stored);
      sessionData.lastActiveAt = Date.now();
      localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
    }
  } catch (error) {
    console.warn('更新会话活跃时间失败:', error);
  }
}

/**
 * 清除会话（用于登出或重置）
 */
export function clearSession(): void {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (error) {
    console.warn('清除会话失败:', error);
  }
}

/**
 * 获取会话信息
 */
export function getSessionInfo(): SessionData | null {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
    return null;
  } catch (error) {
    console.warn('获取会话信息失败:', error);
    return null;
  }
}

