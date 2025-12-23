/**
 * AI 代理工具
 * 使用后端代理 API，避免在前端暴露 API Keys
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://aiadmin.usdt2026.cc';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean; // 是否使用流式响应
  session_id?: string; // 会话 ID
}

export interface ChatResponse {
  content: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  suggestions?: string[];
}

/**
 * 通过代理 API 发送聊天请求（普通响应）
 */
export async function sendChatRequest(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/ai-proxy/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...request, stream: false }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`AI 代理请求失败: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('AI 代理请求失败:', error);
    throw error;
  }
}

/**
 * 通过代理 API 发送流式聊天请求
 */
export async function sendStreamChatRequest(
  request: ChatRequest,
  onChunk?: (chunk: string) => void
): Promise<string> {
  try {
    const sessionId = request.session_id || (() => {
      try {
        const sessionData = localStorage.getItem('ai_chat_session_id_tgmini');
        if (sessionData) {
          const parsed = JSON.parse(sessionData);
          return parsed.sessionId;
        }
      } catch (e) {}
      return undefined;
    })();

    const response = await fetch(`${API_BASE_URL}/api/v1/ai-proxy/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(sessionId ? { 'X-Session-Id': sessionId } : {}),
      },
      body: JSON.stringify({ ...request, stream: true, session_id: sessionId }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`AI 代理请求失败: ${response.status} - ${errorText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    if (!reader) {
      throw new Error('无法读取响应流');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.error) {
              throw new Error(data.error);
            }
            if (data.done) {
              return data.full_content || fullContent;
            }
            if (data.content) {
              fullContent += data.content;
              onChunk?.(data.content);
            }
          } catch (e) {
            console.warn('解析 SSE 数据失败:', e);
          }
        }
      }
    }

    return fullContent;
  } catch (error) {
    console.error('AI 流式请求失败:', error);
    throw error;
  }
}

