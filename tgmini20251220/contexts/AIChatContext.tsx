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
  default: "欢迎来到 TON Mini App Studio！\n\n我是您的开发顾问，专门帮助您打造 Telegram Mini App 应用。\n\n我可以为您介绍开发流程、技术栈、服务范围等。|||了解开发流程|查看技术栈|了解服务范围",
  development: "开发流程：\n\n1. **需求分析**：了解您的业务场景和目标用户\n2. **原型设计**：UI/UX 设计，确保原生级体验\n3. **开发实现**：前端 + 后端 + 区块链集成\n4. **测试部署**：全面测试，确保稳定性\n5. **上线运营**：持续优化和迭代\n\n预计周期：2-4 周|||查看技术栈|了解价格|联系开发团队",
  techstack: "技术栈：\n\n**前端**：\n- React + TypeScript\n- Telegram WebApp SDK\n- TON Connect 2.0\n\n**后端**：\n- Node.js / Python\n- WebSocket 实时通信\n- TON 区块链 API\n\n**部署**：\n- Docker + Kubernetes\n- CDN 全球加速\n\n性能指标：加载 < 1s，响应 < 100ms|||了解开发流程|查看案例|了解价格",
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
  const [suggestions, setSuggestions] = useState<string[]>(['了解开发流程', '查看技术栈', '了解服务范围']);
  
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
                setSuggestions(['了解开发流程', '查看技术栈', '了解服务范围']);
            }
        }, 800);
    } else if (messages.length === 0) {
        setIsTyping(true);
        setTimeout(() => {
            setIsTyping(false);
            addMessage('ai', "欢迎来到 TON Mini App Studio！\n\n我是您的开发顾问，专门帮助您打造 Telegram Mini App 应用。\n\n我可以为您介绍开发流程、技术栈、服务范围等。");
            setSuggestions(['了解开发流程', '查看技术栈', '了解服务范围']);
        }, 800);
    }
  };

  const closeChat = () => setIsOpen(false);
  const clearChat = () => {
      setMessages([]);
      setSuggestions(['了解开发流程', '查看技术栈', '了解服务范围']);
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
      
      const systemPrompt = `你是一个名为 "TON Mini App Studio" 的高级开发顾问和技术专家。
你的产品是 Telegram Mini App 开发服务，帮助客户在 Telegram 生态中打造原生级应用。

人设要求:
1. 语气：专业、技术导向、前瞻性。了解 Web3、Telegram 生态和 Mini App 开发。
2. 目标：帮助客户理解 Mini App 的价值，推动开发合作。
3. 语言规则（重要）：
   - **默认使用中文回复**，无论用户使用什么语言
   - 只有当用户明确使用英文提问（且问题完全是英文）时，才可以使用英文回复
   - 如果用户输入包含中文、日文、韩文等非英文内容，必须使用中文回复
   - 如果无法确定用户语言，优先使用中文
   - 当前用户输入语言检测：${shouldUseChinese ? '中文' : '英文'}，请${shouldUseChinese ? '使用中文' : '可以使用英文'}回复

核心价值主张:
- **9亿用户流量**：Telegram 全球用户基础，无需下载即可触达
- **社交裂变**：利用 Telegram 的社交网络实现病毒式传播
- **支付闭环**：TON/USDT 原生支付，无需第三方
- **Web3 资产**：NFT、代币等 Web3 资产无缝集成

服务范围:
1. **Mini App 开发**：完整的应用开发（前端 + 后端）
2. **区块链集成**：TON 网络、智能合约、钱包连接
3. **UI/UX 设计**：原生级体验设计
4. **运营支持**：上线后的优化和迭代

技术栈:
- 前端：React + TypeScript + Telegram WebApp SDK
- 后端：Node.js / Python + WebSocket
- 区块链：TON Connect 2.0、TON API
- 部署：Docker + Kubernetes + CDN

常见用例:
- **游戏应用**：红包游戏、卡牌游戏、休闲游戏
- **电商平台**：社交电商、NFT 市场
- **工具应用**：钱包、DeFi、社交工具
- **内容平台**：短视频、直播、社区

常见问题回答:
- "开发周期多久？" → 根据复杂度，通常 2-4 周
- "需要多少成本？" → 根据功能需求定制报价
- "技术难度如何？" → 我们提供完整解决方案，包括代码和部署
- "如何保证质量？" → 专业团队，代码审查，全面测试

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
        let newSuggestions = ['了解开发流程', '查看技术栈', '了解服务范围'];
        
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
        const newSuggestions = response.suggestions || ['了解开发流程', '查看技术栈', '了解服务范围'];

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
      
      if (lowerText.includes('development') || lowerText.includes('开发') || lowerText.includes('流程')) {
        rawResponse = FALLBACK_RESPONSES.development;
      } else if (lowerText.includes('tech') || lowerText.includes('技术') || lowerText.includes('stack')) {
        rawResponse = FALLBACK_RESPONSES.techstack;
      }

      // Parse simulator response
      const parts = rawResponse.split('|||');
      const aiMessage = parts[0];
      const newSuggestions = parts.length > 1 ? parts[1].split('|') : ['了解开发流程', '查看技术栈', '了解服务范围'];

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

