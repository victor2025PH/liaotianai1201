import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import { detectUserLanguage } from '../utils/aiConfig';
import { sendChatRequest, sendStreamChatRequest, ChatMessage } from '../utils/aiProxy';
import { loadMessages, saveMessages, clearStoredMessages } from '../utils/messageStorage';
import { getSessionId, updateSessionActivity } from '../utils/sessionManager';

// Message Type
export interface Message {
  id: string;
  role: 'system' | 'user' | 'ai';
  content: string;
  timestamp: number;
}

export interface TriggerRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

interface AIChatContextType {
  isOpen: boolean;
  messages: Message[];
  isTyping: boolean;
  triggerRect: TriggerRect | null;
  suggestions: string[];
  openChat: (context?: string, triggerMessage?: string, element?: HTMLElement) => void;
  closeChat: () => void;
  sendMessage: (text: string) => void;
  clearChat: () => void;
}

const AIChatContext = createContext<AIChatContextType | undefined>(undefined);

const FALLBACK_RESPONSES: Record<string, string> = {
  default: "欢迎来到 RedEnvelope.fi！\n\n我是您的游戏顾问，专门帮助您了解 Telegram Web3 红包病毒式游戏解决方案。\n\n我可以为您介绍游戏机制、技术架构、变现模式等。|||了解游戏机制|查看技术架构|了解变现模式",
  mechanic: "红包游戏核心机制：\n\n1. **病毒式传播**：用户邀请好友获得红包\n2. **Web3 支付**：TON/USDT 即时到账\n3. **智能分配**：AI 算法优化红包分配\n4. **防作弊系统**：区块链验证确保公平\n\n您想了解哪个方面？|||技术实现细节|变现模式|部署方案",
  revenue: "变现模式分析：\n\n- **用户充值**：游戏内购买道具\n- **广告收入**：原生广告集成\n- **手续费**：每笔交易收取 2-5%\n- **NFT 销售**：限量道具 NFT 化\n\n预计 ROI：300-500%|||查看详细数据|了解部署成本|联系商务合作",
};

export const AIChatProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // 从 localStorage 加载保存的消息
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const savedMessages = loadMessages();
      return savedMessages || [];
    } catch (error) {
      console.warn('加载保存的消息失败:', error);
      return [];
    }
  });
  
  const [isOpen, setIsOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionContext, setSessionContext] = useState<string>('');
  const [triggerRect, setTriggerRect] = useState<TriggerRect | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>(['了解游戏机制', '查看技术架构', '了解变现模式']);
  
  // 获取会话 ID
  const sessionId = getSessionId();
  
  // 当消息更新时，自动保存到 localStorage
  useEffect(() => {
    if (messages.length > 0) {
      saveMessages(messages);
      updateSessionActivity();
    }
  }, [messages]);

  // 使用代理 API，不再需要直接初始化 AI 客户端

  const addMessage = (role: 'user' | 'ai' | 'system', content: string) => {
    const newMessage: Message = {
      id: Math.random().toString(36).substring(7),
      role,
      content,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const openChat = (context: string = '', triggerMessage: string = '', element?: HTMLElement) => {
    setIsOpen(true);
    setSessionContext(context);
    
    if (element) {
      const rect = element.getBoundingClientRect();
      setTriggerRect({
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height
      });
    } else {
      setTriggerRect(null);
    }
    
    if (triggerMessage) {
        setIsTyping(true);
        setTimeout(() => {
            setIsTyping(false);
            const parts = triggerMessage.split('|||');
            addMessage('ai', parts[0]);
            if (parts.length > 1) {
                setSuggestions(parts[1].split('|'));
            } else {
                setSuggestions(['了解游戏机制', '查看技术架构', '了解变现模式']);
            }
        }, 800);
    } else if (messages.length === 0) {
        setIsTyping(true);
        setTimeout(() => {
            setIsTyping(false);
            addMessage('ai', "欢迎来到 RedEnvelope.fi！\n\n我是您的游戏顾问，专门帮助您了解 Telegram Web3 红包病毒式游戏解决方案。\n\n我可以为您介绍游戏机制、技术架构、变现模式等。");
            setSuggestions(['了解游戏机制', '查看技术架构', '了解变现模式']);
        }, 800);
    }
  };

  const closeChat = () => setIsOpen(false);
  const clearChat = () => {
      setMessages([]);
      setSuggestions(['了解游戏机制', '查看技术架构', '了解变现模式']);
      clearStoredMessages(); // 清除保存的消息
  };

  const sendMessage = async (text: string) => {
    addMessage('user', text);
    setIsTyping(true);
    setSuggestions([]);

    try {
      // --- 使用代理 API 模式 ---
      // 构建历史消息上下文
      const historyMessages: ChatMessage[] = messages.slice(-6).map(m => ({
        role: m.role === 'user' ? 'user' : (m.role === 'ai' ? 'assistant' : 'system'),
        content: m.content
      }));
      
      // 检测用户输入的语言
      const userLang = detectUserLanguage(text);
      const shouldUseChinese = userLang === 'zh-CN';
      
      const systemPrompt = `你是一个名为 "RedEnvelope.fi" 的高级游戏顾问和技术专家。
你的产品是一个 Telegram Web3 红包病毒式游戏解决方案。

人设要求:
1. 语气：专业、热情、技术导向。了解 Web3 和游戏化营销。
2. 目标：帮助客户理解红包游戏的价值，推动合作。
3. 语言规则（重要）：
   - **默认使用中文回复**，无论用户使用什么语言
   - 只有当用户明确使用英文提问（且问题完全是英文）时，才可以使用英文回复
   - 如果用户输入包含中文、日文、韩文等非英文内容，必须使用中文回复
   - 如果无法确定用户语言，优先使用中文
   - 当前用户输入语言检测：${shouldUseChinese ? '中文' : '英文'}，请${shouldUseChinese ? '使用中文' : '可以使用英文'}回复

核心产品特点:
- **病毒式传播机制**：用户邀请好友获得红包，形成裂变
- **Web3 支付集成**：TON/USDT 即时到账，无需第三方
- **智能红包分配**：AI 算法优化分配策略，提高用户留存
- **防作弊系统**：区块链验证确保公平性
- **多游戏模式**：支持多种红包玩法（抢红包、拆红包、红包雨等）

技术架构:
- 前端：Telegram Mini App (React + Vite)
- 后端：Node.js + WebSocket 实时通信
- 区块链：TON 网络集成
- 数据库：PostgreSQL + Redis 缓存
- 部署：Docker + Kubernetes

变现模式:
1. **用户充值**：游戏内购买道具、皮肤
2. **广告收入**：原生广告集成（不影响体验）
3. **交易手续费**：每笔红包交易收取 2-5%
4. **NFT 销售**：限量道具、皮肤 NFT 化
5. **会员订阅**：VIP 会员享受特殊权益

常见问题回答:
- "如何开始？" → 提供部署流程和技术支持
- "需要多少成本？" → 根据规模定制报价
- "技术难度如何？" → 我们提供完整解决方案，包括代码和部署
- "如何保证安全？" → 区块链验证 + 多重加密

重要协议 - 快捷指令生成:
在你的回复末尾，必须生成 3 个简短的后续行动建议。
格式：回复内容...|||建议1|建议2|建议3

当前上下文: ${sessionContext}`;

      // 构建完整的消息列表
      const chatMessages: ChatMessage[] = [
        { role: 'system', content: systemPrompt },
        ...historyMessages,
        { role: 'user', content: text }
      ];

      // 先创建一个空的 AI 消息，用于流式更新
      const aiMessageId = Math.random().toString(36).substring(7);
      const tempAiMessage: Message = {
        id: aiMessageId,
        role: 'ai',
        content: '',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, tempAiMessage]);
      setIsTyping(true);

      // 使用流式响应（优先使用 Gemini）
      let fullContent = '';
      try {
        fullContent = await sendStreamChatRequest(
          {
            messages: chatMessages,
            model: 'gemini-2.5-flash-latest', // 优先使用 Gemini
            temperature: 0.7,
            max_tokens: 1000,
            session_id: sessionId, // 发送会话 ID
          },
          (chunk: string) => {
            // 实时更新消息内容
            fullContent += chunk;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === aiMessageId
                  ? { ...msg, content: fullContent }
                  : msg
              )
            );
          }
        );

        // 解析建议（如果存在）
        let aiMessage = fullContent;
        let newSuggestions = ['了解游戏机制', '查看技术架构', '了解变现模式'];
        
        if (fullContent.includes('|||')) {
          const parts = fullContent.split('|||');
          aiMessage = parts[0].trim();
          if (parts.length > 1) {
            newSuggestions = parts[1]
              .split('|')
              .map((s) => s.trim())
              .filter((s) => s.length > 0);
          }
        }

        // 更新最终消息内容
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId
              ? { ...msg, content: aiMessage }
              : msg
          )
        );
        setSuggestions(newSuggestions);
      } catch (streamError) {
        // 如果流式响应失败，尝试普通响应
        console.warn('流式响应失败，降级到普通响应:', streamError);
        const response = await sendChatRequest({
          messages: chatMessages,
          model: 'gemini-2.5-flash-latest',
          temperature: 0.7,
          max_tokens: 1000,
          session_id: sessionId, // 发送会话 ID
        });
        
        const aiMessage = response.content;
        const newSuggestions = response.suggestions || ['了解游戏机制', '查看技术架构', '了解变现模式'];

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === aiMessageId
              ? { ...msg, content: aiMessage }
              : msg
          )
        );
        setSuggestions(newSuggestions);
      }

      setIsTyping(false);
    } catch (error) {
      console.error("AI Error:", error);
      setIsTyping(false);
      
      // 如果代理 API 失败，降级到模拟模式
      let rawResponse = FALLBACK_RESPONSES.default;
      const lowerText = text.toLowerCase();
      
      if (lowerText.includes('mechanic') || lowerText.includes('机制') || lowerText.includes('玩法')) {
        rawResponse = FALLBACK_RESPONSES.mechanic;
      } else if (lowerText.includes('revenue') || lowerText.includes('变现') || lowerText.includes('收入')) {
        rawResponse = FALLBACK_RESPONSES.revenue;
      }

      // Parse simulator response
      const parts = rawResponse.split('|||');
      const aiMessage = parts[0];
      const newSuggestions = parts.length > 1 ? parts[1].split('|') : ['了解游戏机制', '查看技术架构', '了解变现模式'];

      addMessage('ai', aiMessage);
      setSuggestions(newSuggestions);
    }
  };

  return (
    <AIChatContext.Provider value={{ isOpen, messages, isTyping, triggerRect, suggestions, openChat, closeChat, sendMessage, clearChat }}>
      {children}
    </AIChatContext.Provider>
  );
};

export const useAIChat = () => {
  const context = useContext(AIChatContext);
  if (context === undefined) {
    throw new Error('useAIChat must be used within an AIChatProvider');
  }
  return context;
};

