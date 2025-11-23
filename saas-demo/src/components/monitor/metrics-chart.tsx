"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from "react"

export interface MetricsChartProps {
  data: Array<{
    timestamp: string
    value: number
  }>
  title: string
  description?: string
  loading?: boolean
  error?: string | null
  metricType?: "messages" | "replies" | "errors" | "redpackets"
  chartType?: "line" | "area" | "bar"
  period?: "1h" | "24h" | "7d" | "30d"
  onPeriodChange?: (period: "1h" | "24h" | "7d" | "30d") => void
  onMetricTypeChange?: (type: "messages" | "replies" | "errors" | "redpackets") => void
}

export function MetricsChart({
  data,
  title,
  description,
  loading = false,
  error = null,
  metricType = "messages",
  chartType = "area",
  period = "24h",
  onPeriodChange,
  onMetricTypeChange,
}: MetricsChartProps) {
  // 格式化時間標籤
  const formatTimeLabel = (timestamp: string) => {
    const date = new Date(timestamp)
    if (period === "1h") {
      return date.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" })
    } else if (period === "24h") {
      return date.toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" })
    } else if (period === "7d") {
      return date.toLocaleDateString("zh-TW", { month: "2-digit", day: "2-digit" })
    } else {
      return date.toLocaleDateString("zh-TW", { month: "2-digit", day: "2-digit" })
    }
  }

  // 準備圖表數據
  const chartData = data.map((point) => ({
    time: formatTimeLabel(point.timestamp),
    timestamp: point.timestamp,
    value: point.value,
  }))

  // 獲取指標名稱
  const getMetricName = (type: string) => {
    const names: Record<string, string> = {
      messages: "消息數",
      replies: "回復數",
      errors: "錯誤數",
      redpackets: "紅包數",
    }
    return names[type] || type
  }

  // 獲取顏色
  const getColor = (type: string) => {
    const colors: Record<string, string> = {
      messages: "#3b82f6", // blue
      replies: "#10b981", // green
      errors: "#ef4444", // red
      redpackets: "#f59e0b", // amber
    }
    return colors[type] || "#3b82f6"
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          {description && <Skeleton className="h-4 w-64 mt-2" />}
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-[300px] text-muted-foreground">
            暫無數據
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="flex gap-2">
            {onMetricTypeChange && (
              <Select value={metricType} onValueChange={onMetricTypeChange}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="messages">消息數</SelectItem>
                  <SelectItem value="replies">回復數</SelectItem>
                  <SelectItem value="errors">錯誤數</SelectItem>
                  <SelectItem value="redpackets">紅包數</SelectItem>
                </SelectContent>
              </Select>
            )}
            {onPeriodChange && (
              <Select value={period} onValueChange={onPeriodChange}>
                <SelectTrigger className="w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">1小時</SelectItem>
                  <SelectItem value="24h">24小時</SelectItem>
                  <SelectItem value="7d">7天</SelectItem>
                  <SelectItem value="30d">30天</SelectItem>
                </SelectContent>
              </Select>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          {chartType === "line" ? (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="value"
                name={getMetricName(metricType)}
                stroke={getColor(metricType)}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          ) : chartType === "bar" ? (
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="value"
                name={getMetricName(metricType)}
                fill={getColor(metricType)}
              />
            </BarChart>
          ) : (
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id={`gradient-${metricType}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={getColor(metricType)} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={getColor(metricType)} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="value"
                name={getMetricName(metricType)}
                stroke={getColor(metricType)}
                fill={`url(#gradient-${metricType})`}
                strokeWidth={2}
              />
            </AreaChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}

