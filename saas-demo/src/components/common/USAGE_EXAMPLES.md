# 通用组件使用示例

## useCrud Hook 使用示例

```typescript
import { useCrud } from "@/hooks/useCrud"
import { getAgents, createAgent, updateAgent, deleteAgent } from "@/lib/api/agents"
import type { Agent } from "@/lib/api/agents"

export default function AgentsPage() {
  const crud = useCrud<Agent, AgentCreateRequest, AgentUpdateRequest>({
    listApi: getAgents,
    createApi: createAgent,
    updateApi: updateAgent,
    deleteApi: deleteAgent,
    initialFilters: {
      search: "",
      status: "all"
    }
  })
  
  // 现在可以直接使用 crud.items, crud.loading, crud.handleCreate 等
  return (
    <div>
      <button onClick={crud.handleCreate}>创建</button>
      {crud.items.map(item => (
        <div key={item.agent_id}>{item.agent_id}</div>
      ))}
    </div>
  )
}
```

## DataTable 使用示例

```typescript
import { DataTable, Column } from "@/components/common"
import { useCrud } from "@/hooks/useCrud"
import { getAgents } from "@/lib/api/agents"
import type { Agent } from "@/lib/api/agents"

const columns: Column<Agent>[] = [
  {
    key: "agent_id",
    header: "Agent ID",
    accessor: (item) => <code>{item.agent_id}</code>
  },
  {
    key: "status",
    header: "状态",
    accessor: (item) => (
      <Badge variant={item.status === "online" ? "default" : "secondary"}>
        {item.status}
      </Badge>
    )
  },
  {
    key: "latency",
    header: "延迟",
    accessor: (item) => item.latency ? `${item.latency}ms` : "-"
  }
]

export default function AgentsPage() {
  const crud = useCrud({
    listApi: getAgents,
    // ...
  })
  
  return (
    <DataTable
      data={crud.items}
      columns={columns}
      loading={crud.loading}
      error={crud.error}
      pagination={crud.pagination}
      onPaginationChange={(page, pageSize) => {
        crud.setPagination({ page, pageSize })
      }}
      onEdit={crud.handleEdit}
      onDelete={crud.handleDelete}
      searchable
      searchValue={crud.filters.search}
      onSearchChange={(value) => crud.setFilters({ search: value })}
    />
  )
}
```

## CrudDialog 使用示例

```typescript
import { CrudDialog, FormField } from "@/components/common"
import { useCrud } from "@/hooks/useCrud"

const fields: FormField[] = [
  {
    name: "name",
    label: "名称",
    type: "text",
    required: true,
    placeholder: "请输入名称"
  },
  {
    name: "description",
    label: "描述",
    type: "textarea",
    placeholder: "请输入描述"
  },
  {
    name: "status",
    label: "状态",
    type: "select",
    required: true,
    options: [
      { label: "启用", value: "active" },
      { label: "禁用", value: "inactive" }
    ]
  }
]

export default function AgentsPage() {
  const crud = useCrud({
    // ...
  })
  
  return (
    <>
      <CrudDialog
        open={crud.dialogOpen}
        onOpenChange={crud.setDialogOpen}
        mode={crud.editingItem ? "edit" : "create"}
        title={crud.editingItem ? "编辑 Agent" : "创建 Agent"}
        fields={fields}
        initialData={crud.editingItem}
        onSubmit={crud.handleSave}
        loading={crud.loading}
      />
    </>
  )
}
```

## 完整示例：节点管理页面（简化版）

```typescript
"use client"

import { useCrud } from "@/hooks/useCrud"
import { useAgentStatus } from "@/hooks/useWebSocket"
import { DataTable, CrudDialog, Column, FormField } from "@/components/common"
import { getAgents, createAgent, updateAgent, deleteAgent } from "@/lib/api/agents"
import type { Agent } from "@/lib/api/agents"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

const columns: Column<Agent>[] = [
  {
    key: "agent_id",
    header: "Agent ID"
  },
  {
    key: "status",
    header: "状态",
    accessor: (item) => {
      const { isOnline } = useAgentStatus(item.agent_id)
      return (
        <Badge variant={isOnline ? "default" : "secondary"}>
          {isOnline ? "在线" : "离线"}
        </Badge>
      )
    }
  },
  {
    key: "latency",
    header: "延迟",
    accessor: (item) => {
      const { agent } = useAgentStatus(item.agent_id)
      return agent?.latency ? `${agent.latency}ms` : "-"
    }
  }
]

const fields: FormField[] = [
  {
    name: "agent_id",
    label: "Agent ID",
    type: "text",
    required: true
  }
]

export default function NodesPage() {
  const crud = useCrud<Agent, any, any>({
    listApi: getAgents,
    createApi: createAgent,
    updateApi: updateAgent,
    deleteApi: deleteAgent
  })
  
  return (
    <div className="container mx-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">节点管理</h1>
        <Button onClick={crud.handleCreate}>创建节点</Button>
      </div>
      
      <DataTable
        data={crud.items}
        columns={columns}
        loading={crud.loading}
        error={crud.error}
        pagination={crud.pagination}
        onPaginationChange={(page, pageSize) => {
          crud.setPagination({ page, pageSize })
        }}
        onEdit={crud.handleEdit}
        onDelete={crud.handleDelete}
        searchable
      />
      
      <CrudDialog
        open={crud.dialogOpen}
        onOpenChange={crud.setDialogOpen}
        mode={crud.editingItem ? "edit" : "create"}
        title={crud.editingItem ? "编辑节点" : "创建节点"}
        fields={fields}
        initialData={crud.editingItem}
        onSubmit={crud.handleSave}
        loading={crud.loading}
      />
    </div>
  )
}
```

**代码量对比**：
- 使用通用组件：~80 行
- 不使用通用组件：~300-500 行
- **减少 70-80% 代码量**
