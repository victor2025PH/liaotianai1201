/**
 * 健康检查 API 客户端
 */
import axios from "axios";
import { getApiBaseUrl } from "./config";

const API_BASE = getApiBaseUrl();

export interface ComponentHealth {
  name: string;
  status: "healthy" | "degraded" | "unhealthy" | "unknown";
  message?: string;
  response_time_ms?: number;
  details?: Record<string, any>;
  timestamp: string;
}

export interface HealthCheckResponse {
  status: "healthy" | "degraded" | "unhealthy";
  components: ComponentHealth[];
  timestamp: string;
  summary?: {
    healthy: number;
    degraded: number;
    unhealthy: number;
    unknown: number;
  };
}

/**
 * 获取健康检查数据
 * @param detailed 是否返回详细健康信息
 */
export async function getHealthCheck(
  detailed: boolean = true
): Promise<HealthCheckResponse> {
  const response = await axios.get<HealthCheckResponse>(`${API_BASE}/health`, {
    params: { detailed },
  });
  return response.data;
}

/**
 * 快速健康检查（仅检查数据库）
 */
export async function quickHealthCheck(): Promise<{ status: string }> {
  const response = await axios.get<{ status: string }>(`${API_BASE}/health`, {
    params: { detailed: false },
  });
  return response.data;
}

