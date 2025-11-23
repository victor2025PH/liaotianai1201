/**
 * 服務器管理 API
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export interface ServerStatus {
  node_id: string;
  host: string;
  port: number;
  status: "online" | "offline" | "error";
  accounts_count: number;
  max_accounts: number;
  cpu_usage?: number;
  memory_usage?: number;
  disk_usage?: number;
  last_heartbeat?: string;
  service_status?: string;
}

export interface ServerLogEntry {
  timestamp: string;
  level: string;
  message: string;
}

/**
 * 獲取所有服務器列表
 */
export async function getServers(): Promise<ServerStatus[]> {
  const { fetchWithAuth } = await import("./client");
  const response = await fetchWithAuth(`${API_BASE}/group-ai/servers/`);
  if (!response.ok) {
    if (response.status === 401) {
      // 401 错误，可能需要重新登录
      const { logout } = await import("./auth");
      logout(false); // 不立即重定向，让调用者处理
      throw new Error("认证失败，请重新登录");
    }
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}: 加载服务器列表失败`);
  }
  return response.json();
}

/**
 * 獲取單個服務器狀態
 */
export async function getServer(nodeId: string): Promise<ServerStatus> {
  const { fetchWithAuth } = await import("./client");
  const response = await fetchWithAuth(`${API_BASE}/group-ai/servers/${nodeId}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * 獲取服務器日誌
 */
export async function getServerLogs(nodeId: string, lines: number = 100): Promise<ServerLogEntry[]> {
  const { fetchWithAuth } = await import("./client");
  const response = await fetchWithAuth(`${API_BASE}/group-ai/servers/${nodeId}/logs?lines=${lines}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * 執行服務器操作
 */
export async function serverAction(nodeId: string, action: "start" | "stop" | "restart" | "status"): Promise<{ success: boolean; message: string }> {
  const { fetchWithAuth } = await import("./client");
  const response = await fetchWithAuth(`${API_BASE}/group-ai/servers/${nodeId}/action`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ action, node_id: nodeId }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * 服務器賬號管理相關接口
 */
export interface ServerAccount {
  account_id: string;
  session_file: string;
  server_id: string;
  file_size: number;
  modified_time?: string;
}

export interface ScanServerAccountsResponse {
  server_id: string;
  accounts: ServerAccount[];
  total_count: number;
}

/**
 * 掃描服務器上的賬號
 */
export async function scanServerAccounts(serverId?: string): Promise<ScanServerAccountsResponse[]> {
  const { fetchWithAuth } = await import("./client");
  const url = serverId 
    ? `${API_BASE}/group-ai/account-management/scan-server-accounts?server_id=${serverId}`
    : `${API_BASE}/group-ai/account-management/scan-server-accounts`;
  const response = await fetchWithAuth(url);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

/**
 * 刪除服務器上的賬號
 */
export async function deleteServerAccount(serverId: string, accountId: string): Promise<{ success: boolean; message: string; deleted_file?: string }> {
  const { fetchWithAuth } = await import("./client");
  const response = await fetchWithAuth(`${API_BASE}/group-ai/account-management/server-account`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      server_id: serverId,
      account_id: accountId,
      confirm: true,
    }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * 批量刪除服務器上的賬號
 */
export async function batchDeleteServerAccounts(serverId: string, accountIds: string[]): Promise<{ success: boolean; message: string; deleted: string[]; failed: Array<{ account_id: string; error: string }>; not_found: string[] }> {
  const { fetchWithAuth } = await import("./client");
  const response = await fetchWithAuth(`${API_BASE}/group-ai/account-management/batch-delete-server-accounts?server_id=${serverId}&confirm=true`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(accountIds),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * 分配賬號到服務器
 */
export async function allocateAccountToServer(accountId: string, sessionFile: string, serverId: string, scriptId?: string): Promise<{ success: boolean; server_id?: string; remote_path?: string; load_score?: number; message: string }> {
  const { fetchWithAuth } = await import("./client");
  const response = await fetchWithAuth(`${API_BASE}/group-ai/allocation/allocate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      account_id: accountId,
      session_file: sessionFile,
      script_id: scriptId,
      strategy: "load_balance",
    }),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

