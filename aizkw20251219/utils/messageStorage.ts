/**
 * 消息持久化工具
 * 使用 localStorage 保存聊天消息，刷新页面后恢复
 */

import { Message } from '../contexts/AIChatContext';

const STORAGE_KEY = 'ai_chat_messages';
const MAX_MESSAGES = 50; // 最多保存 50 条消息
const STORAGE_VERSION = '1.0';

interface StoredMessages {
  version: string;
  messages: Message[];
  lastUpdated: number;
}

/**
 * 保存消息到 localStorage
 */
export function saveMessages(messages: Message[]): void {
  try {
    // 只保存最近的消息
    const messagesToSave = messages.slice(-MAX_MESSAGES);
    
    const data: StoredMessages = {
      version: STORAGE_VERSION,
      messages: messagesToSave,
      lastUpdated: Date.now(),
    };
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.warn('保存消息失败:', error);
    // localStorage 可能已满或不可用，忽略错误
  }
}

/**
 * 从 localStorage 加载消息
 */
export function loadMessages(): Message[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return [];
    }
    
    const data: StoredMessages = JSON.parse(stored);
    
    // 检查版本兼容性
    if (data.version !== STORAGE_VERSION) {
      // 版本不兼容，清除旧数据
      localStorage.removeItem(STORAGE_KEY);
      return [];
    }
    
    // 检查数据是否过期（7天）
    const SEVEN_DAYS = 7 * 24 * 60 * 60 * 1000;
    if (Date.now() - data.lastUpdated > SEVEN_DAYS) {
      localStorage.removeItem(STORAGE_KEY);
      return [];
    }
    
    return data.messages || [];
  } catch (error) {
    console.warn('加载消息失败:', error);
    return [];
  }
}

/**
 * 清除保存的消息
 */
export function clearStoredMessages(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.warn('清除消息失败:', error);
  }
}

/**
 * 获取存储的消息数量
 */
export function getStoredMessageCount(): number {
  try {
    const messages = loadMessages();
    return messages.length;
  } catch (error) {
    return 0;
  }
}

