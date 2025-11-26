/**
 * 使用 React Query 管理賬號數據
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getAccounts,
  createAccount,
  startAccount,
  stopAccount,
  type Account,
  type AccountCreateRequest,
} from '@/lib/api/group-ai';

import { getGroupAiApiBaseUrl } from "@/lib/api/config";
import { fetchWithAuth } from "@/lib/api/client";

// 刪除賬號函數（如果API不存在，創建一個）
async function deleteAccount(accountId: string): Promise<void> {
  const API_BASE = getGroupAiApiBaseUrl();
  const response = await fetchWithAuth(`${API_BASE}/accounts/${accountId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
}
import { useToast } from '@/hooks/use-toast';

export function useAccounts() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // 查詢賬號列表
  const {
    data: accounts = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => {
      try {
        const data = await getAccounts();
        return data;
      } catch (error) {
        // 如果發生錯誤，記錄但不拋出，返回空數組
        console.error('[useAccounts] 獲取帳號列表失敗:', error);
        toast({
          title: "獲取帳號列表失敗",
          description: error instanceof Error ? error.message : "未知錯誤",
          variant: "destructive",
        });
        return []; // 返回空數組，避免 UI 崩潰
      }
    },
    staleTime: 30 * 1000,  // 30 秒
    retry: 1, // 只重試一次
    retryDelay: 1000, // 重試延遲 1 秒
  });

  // 創建賬號
  const createAccountMutation = useMutation({
    mutationFn: createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast({
        title: '成功',
        description: '賬號創建成功',
      });
    },
    onError: (error: Error) => {
      toast({
        title: '創建失敗',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // 啟動賬號
  const startAccountMutation = useMutation({
    mutationFn: startAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast({
        title: '成功',
        description: '賬號已啟動',
      });
    },
    onError: (error: Error) => {
      toast({
        title: '啟動失敗',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // 停止賬號
  const stopAccountMutation = useMutation({
    mutationFn: stopAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast({
        title: '成功',
        description: '賬號已停止',
      });
    },
    onError: (error: Error) => {
      toast({
        title: '停止失敗',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // 刪除賬號
  const deleteAccountMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      toast({
        title: '成功',
        description: '賬號已刪除',
      });
    },
    onError: (error: Error) => {
      toast({
        title: '刪除失敗',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  return {
    accounts,
    isLoading,
    error,
    refetch,
    createAccount: createAccountMutation.mutate,
    startAccount: startAccountMutation.mutate,
    stopAccount: stopAccountMutation.mutate,
    deleteAccount: deleteAccountMutation.mutate,
    isCreating: createAccountMutation.isPending,
    isStarting: startAccountMutation.isPending,
    isStopping: stopAccountMutation.isPending,
    isDeleting: deleteAccountMutation.isPending,
  };
}

