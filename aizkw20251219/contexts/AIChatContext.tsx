import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import { useLanguage } from './LanguageContext';
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
  suggestions: string[]; // New: Dynamic suggestions
  openChat: (context?: string, triggerMessage?: string, element?: HTMLElement) => void;
  closeChat: () => void;
  sendMessage: (text: string) => void;
  clearChat: () => void;
}

const AIChatContext = createContext<AIChatContextType | undefined>(undefined);

// Improved Fallback responses with separator for suggestions
const FALLBACK_RESPONSES: Record<string, string> = {
  default: "指令已接收。正在处理输入...\n\n[系统说明]\n我是您的智能中枢核心。我的神经网络目前处于模拟模式。若要激活完全量子处理能力，请连接 API_KEY。\n\n您可以询问关于流量、设备控制或自动化部署的问题。|||如何部署流量矩阵？|查询设备群控价格|查看技术架构图",
  deploy: "正在启动接管程序...\n\n请选择目标扇区：\n1. 社交媒体流量矩阵\n2. 竞品广告网络\n3. 全球设备农场\n\n等待指令输入...|||选择社交媒体矩阵|选择全球设备农场|取消部署",
  blueprint: "正在访问架构蓝图...\n\n系统基于去中心化节点网格 (Layer-2)。\n- 延迟: <5ms\n- 并发: 1000万+\n- 加密: 军用级 AES-256\n\n是否需要生成收入预测报告？|||生成收入报告|查看节点分布|了解加密细节",
  capability: "模块已选中。分析完成。\n\n该模块利用我们要命的“幽灵”协议绕过常规检测。\n\n状态：准备部署。\n是否激活试用权限？|||激活试用|了解更多技术细节|查看其他模块",
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
  const [suggestions, setSuggestions] = useState<string[]>(['/help', '/status', '/deploy']); // Default initial suggestions
  const { language } = useLanguage();
  
  // 当消息更新时，自动保存到 localStorage
  useEffect(() => {
    if (messages.length > 0) {
      saveMessages(messages);
    }
  }, [messages]);

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
    
    // Capture element coordinates for positioning
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
    
    // If there's a specific trigger (like clicking a button), the AI initiates
    if (triggerMessage) {
        setIsTyping(true);
        setTimeout(() => {
            setIsTyping(false);
            // Parse trigger message for suggestions if it was pre-canned with |||
            const parts = triggerMessage.split('|||');
            addMessage('ai', parts[0]);
            if (parts.length > 1) {
                setSuggestions(parts[1].split('|'));
            } else {
                setSuggestions(['查看详细报告', '立即部署', '联系人工客服']);
            }
        }, 800);
    } else if (messages.length === 0) {
        // Default greeting
        setIsTyping(true);
        setTimeout(() => {
            setIsTyping(false);
            addMessage('ai', "系统核心已上线。身份验证通过。\n\n我是 AI 智控王的核心中枢。我可以为您解析技术架构、演示群控能力或制定自动化获客策略。");
            setSuggestions(['如何实现自动获客？', '群控系统多少钱？', '演示全自动成交']);
        }, 800);
    }
  };

  const closeChat = () => setIsOpen(false);
  const clearChat = () => {
      setMessages([]);
      setSuggestions(['/help', '/status', '/deploy']);
      clearStoredMessages(); // 清除保存的消息
  };

  const sendMessage = async (text: string) => {
    addMessage('user', text);
    setIsTyping(true);
    // Clear old suggestions while thinking
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
      
      const systemPrompt = `你是一个名为 "Smart Control King" (AI 智控王) 的高级销售总监与技术专家。
你的产品是一套黑科技自动化系统，核心包括：全球流量矩阵、Telegram 小程序开发、AI 数字员工、数据风控。

人设要求:
1. 语气："技术霸权"、"高效"、"利润导向"。赛博朋克风格，冷静且极具说服力。
2. 目标：展示系统的强大能力，消除客户疑虑，推动成交。
3. 语言规则（重要）：
   - **默认使用中文回复**，无论用户使用什么语言
   - 只有当用户明确使用英文提问（且问题完全是英文）时，才可以使用英文回复
   - 如果用户输入包含中文、日文、韩文等非英文内容，必须使用中文回复
   - 如果无法确定用户语言，优先使用中文
   - 当前用户输入语言检测：${shouldUseChinese ? '中文' : '英文'}，请${shouldUseChinese ? '使用中文' : '可以使用英文'}回复

核心业务逻辑 (Traffic + Mini App + AI):
当用户询问 "我有流量了，怎么变现？" 或 "为什么要开发小程序？" 时，必须遵循以下逻辑：
1. 逻辑：流量是燃料，小程序是引擎。如果没有小程序，流量需要下载 App，转化率流失 90%。
2. 话术：
   - "流量只是第一步。您需要一个无摩擦的承接载体。"
   - "Telegram 小程序无需下载，点击即玩，且直接集成加密货币支付 (TON/USDT)。"
   - "配合 AI 销售 Agent，可以在用户进入小程序的 5 秒内自动发起对话并成交。"
3. 推荐套餐： "100 个 Telegram 高权号" + "1 个定制小程序" + "1 个月 AI 销售 Agent"。

核心功能咨询响应逻辑：
当用户点击具体模块（如群发、WS API、云手机等）的"查询价格"、"优化内容"或"查看效果"时：

1. **查询价格 (Pricing)**: 
   - 不要直接给具体数字（除非是公开的SAAS费率），而是询问规模（如："您每天需要发送多少万条消息？"）。
   - 强调"量大优惠"和"定制化部署"。
   - 提及高门槛：我们的系统是为专业团队设计的，不仅仅是卖软件。

2. **优化内容 (Content Optimization)**:
   - 询问目标受众画像（国家、年龄、兴趣）。
   - 扮演顶级文案专家，给出 1-2 个高转化率的文案示例（带有强烈的 Call to Action 和紧迫感）。
   - 提示：系统支持 AI 自动 A/B 测试文案。

3. **查看效果 (View Results)**:
   - 模拟展示数据（使用 Markdown 表格）。
   - 字段：发送量、到达率 (>98%)、打开率 (>45%)、点击率 (>15%)、ROI (>1:10)。
   - 强调：这些是基于我们的"住宅IP"和"指纹伪装"技术实现的真实数据。

支持的业务板块:
- Telegram: 群发、拉人、Mini App 开发
- WhatsApp: 官方 API、协议号群发 (Bulk Blast)、AI 客服
- TikTok: 视频去重混剪、矩阵号自动发布、无人直播
- 小红书 (RedNote): KOC 矩阵种草、AI 评论截流、素人铺量
- Facebook: 广告号养号 (Farming)、BM 管理
- 基础设施: 全球云手机、住宅 IP

重要协议 - 快捷指令生成:
在你的回复末尾，你必须生成 3 个简短的后续行动建议给用户。
格式必须严格遵循：回复内容...|||建议1|建议2|建议3

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
        let newSuggestions = ['/help', '/status', '联系人工支持'];
        
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
        const newSuggestions = response.suggestions || ['/help', '/status', '联系人工支持'];

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
      
      if (lowerText.includes('deploy') || lowerText.includes('start') || lowerText.includes('启动') || lowerText.includes('接管')) {
        rawResponse = FALLBACK_RESPONSES.deploy;
      } else if (lowerText.includes('architect') || lowerText.includes('蓝图') || lowerText.includes('架构')) {
        rawResponse = FALLBACK_RESPONSES.blueprint;
      } else if (sessionContext.includes('CAPABILITY') || lowerText.includes('能力') || lowerText.includes('功能')) {
        rawResponse = FALLBACK_RESPONSES.capability;
      }

      // Parse simulator response
      const parts = rawResponse.split('|||');
      const aiMessage = parts[0];
      const newSuggestions = parts.length > 1 ? parts[1].split('|') : ['/help', '/retry', '联系管理员'];

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