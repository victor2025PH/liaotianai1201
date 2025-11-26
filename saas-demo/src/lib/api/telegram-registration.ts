/**
 * Telegram 注册和 Session 生成 API 客户端
 */

import { apiClient, apiGet, apiPost } from "../api-client";
import { getApiBaseUrl } from "./config";

const API_BASE = getApiBaseUrl();

// ========== Telegram 注册相关接口 ==========

export interface TelegramRegistrationStartRequest {
  phone: string;
  country_code: string;
  node_id: string;
  api_id?: number;
  api_hash?: string;
  session_name?: string;
  use_proxy?: boolean;
  proxy_url?: string;
}

export interface TelegramRegistrationStatus {
  registration_id: string;
  status: string;
  message: string;
  phone_code_hash?: string;
  expires_in?: number;
  risk_score?: number;
  error_message?: string;
  expires_at?: string;
  mock_mode?: boolean;
  mock_code?: string;
  session_file?: {
    session_name: string;
    file_path: string;
    server_node_id: string;
    file_size: number;
    created_at: string;
  };
}

export interface TelegramRegistrationVerifyRequest {
  registration_id: string;
  code: string;
  password?: string;
}

/**
 * 启动 Telegram 注册
 */
export async function startTelegramRegistration(
  payload: TelegramRegistrationStartRequest
): Promise<TelegramRegistrationStatus> {
  const result = await apiPost<TelegramRegistrationStatus>(
    "/telegram-registration/start",
    payload,
    {
      showSuccessToast: true,
      successMessage: "验证码已发送，请查收",
    }
  );
  
  if (!result.ok || !result.data) {
    throw new Error(result.error?.message || "启动注册失败");
  }
  
  return result.data;
}

/**
 * 验证 Telegram 验证码
 */
export async function verifyTelegramCode(
  payload: TelegramRegistrationVerifyRequest
): Promise<TelegramRegistrationStatus> {
  const result = await apiPost<TelegramRegistrationStatus>(
    "/telegram-registration/verify",
    payload
  );
  
  if (!result.ok || !result.data) {
    throw new Error(result.error?.message || "验证失败");
  }
  
  return result.data;
}

/**
 * 获取注册状态
 */
export async function getTelegramRegistrationStatus(
  registrationId: string
): Promise<TelegramRegistrationStatus> {
  const result = await apiGet<TelegramRegistrationStatus>(
    `/telegram-registration/status/${registrationId}`
  );
  
  if (!result.ok || !result.data) {
    throw new Error(result.error?.message || "获取状态失败");
  }
  
  return result.data;
}

/**
 * 取消注册
 */
export async function cancelTelegramRegistration(
  registrationId: string
): Promise<{ message: string }> {
  const result = await apiPost<{ message: string }>(
    "/telegram-registration/cancel",
    { registration_id: registrationId },
    {
      showSuccessToast: true,
      successMessage: "已取消注册",
    }
  );
  
  if (!result.ok || !result.data) {
    throw new Error(result.error?.message || "取消注册失败");
  }
  
  return result.data;
}

// ========== Session 生成功能已合并到 Telegram 注册 ==========
// 请使用 startTelegramRegistration, verifyTelegramCode, getTelegramRegistrationStatus 代替
// Session 生成功能的所有特性（数据库记录、风控、速率限制等）都已包含在 Telegram 注册功能中

