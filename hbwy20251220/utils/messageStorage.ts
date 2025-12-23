/**
 * 消息持久化工具
 * 使用 localStorage 保存聊天消息，刷新页面后恢复
 */

import { Message } from '../contexts/AIChatContext';

const STORAGE_KEY = 'ai_chat_messages_hbwy';
const MAX_MESSAGES = 50;
const STORAGE_VERSION = '1.0';

interface StoredMessages {
  version: string;
  messages: Message[];
  lastUpdated: number;
}

export function saveMessages(messages: Message[]): void {
  try {
    const messagesToSave = messages.slice(-MAX_MESSAGES);
    const data: StoredMessages = {
      version: STORAGE_VERSION,
      messages: messagesToSave,
      lastUpdated: Date.now(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.warn('保存消息失败:', error);
  }
}

export function loadMessages(): Message[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    
    const data: StoredMessages = JSON.parse(stored);
    if (data.version !== STORAGE_VERSION) {
      localStorage.removeItem(STORAGE_KEY);
      return [];
    }
    
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

export function clearStoredMessages(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.warn('清除消息失败:', error);
  }
}

