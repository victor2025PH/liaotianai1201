/**
 * 会话管理工具
 * 管理用户会话 ID，支持多设备同步（可选）
 */

const SESSION_KEY = 'ai_chat_session_id_tgmini';
const SESSION_VERSION = '1.0';

interface SessionData {
  sessionId: string;
  createdAt: number;
  lastActiveAt: number;
  version: string;
}

function generateSessionId(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `session_${timestamp}_${random}`;
}

export function getSessionId(): string {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    if (stored) {
      const sessionData: SessionData = JSON.parse(stored);
      if (sessionData.version !== SESSION_VERSION) {
        return createNewSession();
      }
      const THIRTY_DAYS = 30 * 24 * 60 * 60 * 1000;
      if (Date.now() - sessionData.createdAt > THIRTY_DAYS) {
        return createNewSession();
      }
      sessionData.lastActiveAt = Date.now();
      localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
      return sessionData.sessionId;
    }
    return createNewSession();
  } catch (error) {
    console.warn('获取会话 ID 失败:', error);
    return createNewSession();
  }
}

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

export function clearSession(): void {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (error) {
    console.warn('清除会话失败:', error);
  }
}

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

