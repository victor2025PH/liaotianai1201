/**
 * 會話列表 Mock 數據
 */

import { SessionListItem, SessionDetail } from "@/lib/api";

export const mockSessions: SessionListItem[] = [
  {
    id: "session-001",
    user: "user1@example.com",
    messages: 12,
    status: "completed",
    duration: "2m 34s",
    started_at: new Date(Date.now() - 3600000).toISOString(),
    token_usage: 1234,
    model: "gpt-4",
  },
  {
    id: "session-002",
    user: "user2@example.com",
    messages: 8,
    status: "active",
    duration: "1m 12s",
    started_at: new Date(Date.now() - 720000).toISOString(),
    token_usage: 567,
    model: "gpt-3.5-turbo",
  },
  {
    id: "session-003",
    user: "user3@example.com",
    messages: 5,
    status: "failed",
    duration: "0m 45s",
    started_at: new Date(Date.now() - 1800000).toISOString(),
    token_usage: 234,
    model: "gpt-4",
  },
];

export const mockSessionDetail: Record<string, SessionDetail> = {
  "session-001": {
    id: "session-001",
    user: "user1@example.com",
    status: "completed",
    duration: "2m 34s",
    started_at: new Date(Date.now() - 3600000).toISOString(),
    ended_at: new Date(Date.now() - 3330000).toISOString(),
    token_usage: 1234,
    model: "gpt-4",
    messages: [
      {
        id: "msg-001",
        role: "user",
        content: "你好，請幫我解釋一下什麼是機器學習？",
        timestamp: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: "msg-002",
        role: "assistant",
        content: "機器學習是人工智能的一個分支，它使計算機能夠從數據中學習並做出預測或決策，而無需明確編程。",
        timestamp: new Date(Date.now() - 3590000).toISOString(),
      },
    ],
  },
  "session-002": {
    id: "session-002",
    user: "user2@example.com",
    status: "active",
    duration: "1m 12s",
    started_at: new Date(Date.now() - 720000).toISOString(),
    token_usage: 567,
    model: "gpt-3.5-turbo",
    messages: [
      {
        id: "msg-003",
        role: "user",
        content: "如何學習 Python？",
        timestamp: new Date(Date.now() - 720000).toISOString(),
      },
    ],
  },
  "session-003": {
    id: "session-003",
    user: "user3@example.com",
    status: "failed",
    duration: "0m 45s",
    started_at: new Date(Date.now() - 1800000).toISOString(),
    ended_at: new Date(Date.now() - 1715000).toISOString(),
    token_usage: 234,
    model: "gpt-4",
    messages: [],
    error_message: "API 請求超時",
  },
};

