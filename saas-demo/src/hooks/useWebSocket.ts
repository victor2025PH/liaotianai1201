/**
 * WebSocket Hook - 管理 Agent 连接状态
 * 提供全局 WebSocket 连接管理和状态订阅
 */

"use client"

import { createContext, useContext, useEffect, useState, useCallback, useRef, ReactNode } from "react"
import { getApiBaseUrl } from "@/lib/api/config"
import { getToken } from "@/lib/api/auth"

// WebSocket 连接状态
export interface WebSocketState {
  isConnected: boolean
  latency: number | null
  onlineAgents: string[]
  agents: Record<string, AgentInfo>
  error: string | null
  connect: () => void
  disconnect: () => void
  subscribe: (topic: string, callback: (data: any) => void) => () => void
  sendMessage: (message: any) => void
}

// Agent 信息
export interface AgentInfo {
  agent_id: string
  status: "online" | "offline" | "busy" | "error"
  connected_at: string
  last_heartbeat: string
  latency?: number
  metadata?: Record<string, any>
}

// WebSocket Context
const WebSocketContext = createContext<WebSocketState | null>(null)

// WebSocket Provider Props
interface WebSocketProviderProps {
  children: ReactNode
  url?: string
}

/**
 * WebSocket Provider - 提供全局 WebSocket 连接
 */
export function WebSocketProvider({ children, url }: WebSocketProviderProps) {
  const [isConnected, setIsConnected] = useState(false)
  const [latency, setLatency] = useState<number | null>(null)
  const [onlineAgents, setOnlineAgents] = useState<string[]>([])
  const [agents, setAgents] = useState<Record<string, AgentInfo>>({})
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const subscribersRef = useRef<Map<string, Set<(data: any) => void>>>(new Map())
  const latencyTestRef = useRef<number | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 10

  // 获取 WebSocket URL（用于接收 Agent 状态更新）
  const getWebSocketUrl = useCallback(() => {
    if (url) return url
    
    const apiBase = getApiBaseUrl()
    // 将 http:// 或 https:// 转换为 ws:// 或 wss://
    const wsProtocol = apiBase.startsWith("https") ? "wss" : "ws"
    const wsHost = apiBase.replace(/^https?:\/\//, "").replace(/^wss?:\/\//, "")
    // 注意：这里需要一个专门的前端 WebSocket 端点来接收 Agent 状态更新
    // 暂时使用 notifications WebSocket，后续可以创建专门的 agents/ws/status 端点
    return `${wsProtocol}://${wsHost}/notifications/ws/frontend`
  }, [url])

  // 订阅消息
  const subscribe = useCallback((topic: string, callback: (data: any) => void) => {
    if (!subscribersRef.current.has(topic)) {
      subscribersRef.current.set(topic, new Set())
    }
    subscribersRef.current.get(topic)!.add(callback)
    
    // 返回取消订阅函数
    return () => {
      const callbacks = subscribersRef.current.get(topic)
      if (callbacks) {
        callbacks.delete(callback)
        if (callbacks.size === 0) {
          subscribersRef.current.delete(topic)
        }
      }
    }
  }, [])

  // 发送消息
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn("[WebSocket] 未连接，无法发送消息")
    }
  }, [])

  // 连接 WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return // 已连接
    }

    const wsUrl = getWebSocketUrl()
    const token = getToken()
    
    // 如果有 token，添加到 URL 参数
    const fullUrl = token ? `${wsUrl}?token=${token}` : wsUrl
    
    try {
      setError(null)
      const ws = new WebSocket(fullUrl)
      
      ws.onopen = () => {
        console.log("[WebSocket] 连接成功")
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        
        // 开始延迟测试
        latencyTestRef.current = Date.now()
        ws.send(JSON.stringify({ type: "ping", timestamp: Date.now() }))
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // 处理 ping/pong（延迟测试）
          if (data.type === "pong" && latencyTestRef.current) {
            const newLatency = Date.now() - latencyTestRef.current
            setLatency(newLatency)
            latencyTestRef.current = null
          }
          
          // 处理 Agent 列表更新
          if (data.type === "agents_update") {
            const agentsList = data.agents || []
            const agentsMap: Record<string, AgentInfo> = {}
            const online: string[] = []
            
            agentsList.forEach((agent: any) => {
              agentsMap[agent.agent_id] = {
                agent_id: agent.agent_id,
                status: agent.status === "connected" ? "online" : "offline",
                connected_at: agent.connected_at,
                last_heartbeat: agent.last_heartbeat,
                metadata: agent.metadata
              }
              
              if (agent.status === "connected") {
                online.push(agent.agent_id)
              }
            })
            
            setAgents(agentsMap)
            setOnlineAgents(online)
          }
          
          // 处理 Agent 状态更新
          if (data.type === "agent_status") {
            const agentId = data.agent_id
            if (agentId) {
              setAgents(prev => ({
                ...prev,
                [agentId]: {
                  ...prev[agentId],
                  ...data.payload,
                  agent_id: agentId
                }
              }))
              
              // 更新在线列表
              if (data.payload?.status === "online") {
                setOnlineAgents(prev => {
                  if (!prev.includes(agentId)) {
                    return [...prev, agentId]
                  }
                  return prev
                })
              } else {
                setOnlineAgents(prev => prev.filter(id => id !== agentId))
              }
            }
          }
          
          // 通知订阅者
          if (data.type) {
            const callbacks = subscribersRef.current.get(data.type)
            if (callbacks) {
              callbacks.forEach(callback => {
                try {
                  callback(data)
                } catch (e) {
                  console.error(`[WebSocket] 订阅回调执行失败: ${e}`)
                }
              })
            }
          }
          
        } catch (e) {
          console.error("[WebSocket] 消息解析失败:", e)
        }
      }
      
      ws.onerror = (error) => {
        console.error("[WebSocket] 连接错误:", error)
        setError("WebSocket 连接错误")
        setIsConnected(false)
      }
      
      ws.onclose = () => {
        console.log("[WebSocket] 连接已关闭")
        setIsConnected(false)
        wsRef.current = null
        
        // 自动重连
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current - 1), 30000)
          console.log(`[WebSocket] ${delay}ms 后尝试重连 (${reconnectAttemptsRef.current}/${maxReconnectAttempts})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else {
          setError("达到最大重连次数，请刷新页面")
        }
      }
      
      wsRef.current = ws
    } catch (e) {
      console.error("[WebSocket] 连接失败:", e)
      setError(`连接失败: ${e}`)
      setIsConnected(false)
    }
  }, [getWebSocketUrl])

  // 断开连接
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setIsConnected(false)
    setError(null)
  }, [])

  // 初始化连接
  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  // 定期测试延迟
  useEffect(() => {
    if (!isConnected) return
    
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN && !latencyTestRef.current) {
        latencyTestRef.current = Date.now()
        wsRef.current.send(JSON.stringify({ type: "ping", timestamp: Date.now() }))
      }
    }, 30000) // 每30秒测试一次
    
    return () => clearInterval(interval)
  }, [isConnected])

  const value: WebSocketState = {
    isConnected,
    latency,
    onlineAgents,
    agents,
    error,
    connect,
    disconnect,
    subscribe,
    sendMessage
  }

  return (
    <WebSocketContext.Provider value={value as WebSocketState}>
      {children}
    </WebSocketContext.Provider>
  )
}

/**
 * 使用 WebSocket Hook
 */
export function useWebSocket(): WebSocketState {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error("useWebSocket must be used within WebSocketProvider")
  }
  return context
}

/**
 * 使用 Agent 状态 Hook
 */
export function useAgentStatus(agentId?: string) {
  const { agents, onlineAgents, isConnected } = useWebSocket()
  
  if (agentId) {
    const agent = agents[agentId]
    return {
      agent,
      isOnline: onlineAgents.includes(agentId),
      isConnected
    }
  }
  
  return {
    agents,
    onlineAgents,
    isConnected,
    onlineCount: onlineAgents.length,
    totalCount: Object.keys(agents).length
  }
}
