/**
 * 角色權限管理頁面
 */
"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { useToast } from "@/hooks/use-toast"
import {
  listRoles,
  getRole,
  createRole,
  updateRole,
  deleteRole,
  assignPermissionToRole,
  revokePermissionFromRole,
  getRolePermissions,
  type Role,
  type RoleWithPermissions,
  type RoleCreate,
  type RoleUpdate,
} from "@/lib/api/roles"
import {
  listPermissions,
  type Permission,
} from "@/lib/api/permissions"
import { usePermissions } from "@/hooks/use-permissions"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { useQueryClient } from "@tanstack/react-query"
import { Plus, Edit, Trash2, Shield, Users } from "lucide-react"

export default function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isPermissionDialogOpen, setIsPermissionDialogOpen] = useState(false)
  const [selectedRole, setSelectedRole] = useState<RoleWithPermissions | null>(null)
  const [formData, setFormData] = useState<RoleCreate>({
    name: "",
    description: "",
  })
  const { toast } = useToast()
  const { hasPermission } = usePermissions()
  const queryClient = useQueryClient()

  const loadRoles = async () => {
    try {
      setLoading(true)
      const data = await listRoles()
      setRoles(data)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "加載角色列表失敗",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadPermissions = async () => {
    try {
      const data = await listPermissions()
      setPermissions(data)
    } catch (err) {
      console.error("加載權限列表失敗:", err)
    }
  }

  useEffect(() => {
    loadRoles()
    loadPermissions()
  }, [])

  const handleCreate = async () => {
    try {
      if (!formData.name.trim()) {
        toast({
          title: "錯誤",
          description: "角色名稱不能為空",
          variant: "destructive",
        })
        return
      }

      await createRole(formData)
      toast({
        title: "成功",
        description: "角色創建成功",
      })
      setIsCreateDialogOpen(false)
      setFormData({ name: "", description: "" })
      loadRoles()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "創建角色失敗",
        variant: "destructive",
      })
    }
  }

  const handleEdit = async (role: Role) => {
    try {
      const roleDetail = await getRole(role.id)
      setSelectedRole(roleDetail)
      setFormData({
        name: role.name,
        description: role.description || "",
      })
      setIsEditDialogOpen(true)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "獲取角色詳情失敗",
        variant: "destructive",
      })
    }
  }

  const handleUpdate = async () => {
    if (!selectedRole) return

    try {
      const update: RoleUpdate = {}
      if (formData.name !== selectedRole.name) {
        update.name = formData.name
      }
      if (formData.description !== selectedRole.description) {
        update.description = formData.description
      }

      if (Object.keys(update).length === 0) {
        toast({
          title: "提示",
          description: "沒有變更",
        })
        return
      }

      await updateRole(selectedRole.id, update)
      toast({
        title: "成功",
        description: "角色更新成功",
      })
      setIsEditDialogOpen(false)
      setSelectedRole(null)
      setFormData({ name: "", description: "" })
      loadRoles()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "更新角色失敗",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async (role: Role) => {
    if (!confirm(`確定要刪除角色 "${role.name}" 嗎？`)) {
      return
    }

    try {
      await deleteRole(role.id)
      toast({
        title: "成功",
        description: "角色刪除成功",
      })
      loadRoles()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "刪除角色失敗",
        variant: "destructive",
      })
    }
  }

  const handleOpenPermissionDialog = async (role: Role) => {
    try {
      const roleDetail = await getRole(role.id)
      setSelectedRole(roleDetail)
      setIsPermissionDialogOpen(true)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "獲取角色權限失敗",
        variant: "destructive",
      })
    }
  }

  const handleTogglePermission = async (permissionCode: string) => {
    if (!selectedRole) return

    const hasPermission = selectedRole.permissions.some(
      (p) => p.code === permissionCode
    )

    try {
      if (hasPermission) {
        await revokePermissionFromRole(selectedRole.id, permissionCode)
        toast({
          title: "成功",
          description: "權限已撤銷",
        })
      } else {
        await assignPermissionToRole(selectedRole.id, {
          permission_code: permissionCode,
        })
        toast({
          title: "成功",
          description: "權限已分配",
        })
      }
      // 重新加載角色權限
      const updatedRole = await getRole(selectedRole.id)
      setSelectedRole(updatedRole)
      // 清除權限緩存（角色權限變更可能影響用戶權限）
      queryClient.invalidateQueries({ queryKey: ["permissions", "me"] })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "操作失敗",
        variant: "destructive",
      })
    }
  }

  // 按模塊分組權限
  const groupedPermissions = permissions.reduce((acc, perm) => {
    const module = perm.code.split(":")[0]
    if (!acc[module]) {
      acc[module] = []
    }
    acc[module].push(perm)
    return acc
  }, {} as Record<string, Permission[]>)

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="h-8 w-8" />
            角色管理
          </h1>
          <p className="text-muted-foreground mt-2">
            管理系統角色和權限分配
          </p>
        </div>
        <PermissionGuard permission="role:create">
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                創建角色
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>創建角色</DialogTitle>
                <DialogDescription>
                  創建一個新的角色
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="role-name">角色名稱</Label>
                  <Input
                    id="role-name"
                    value={formData.name}
                    onChange={(e) =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    placeholder="例如: editor"
                  />
                </div>
                <div>
                  <Label htmlFor="role-description">描述</Label>
                  <Textarea
                    id="role-description"
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    placeholder="角色描述"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                >
                  取消
                </Button>
                <Button onClick={handleCreate}>創建</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </PermissionGuard>
      </div>

      <PermissionGuard permission="role:view">
        {loading ? (
          <div className="text-center py-8">加載中...</div>
        ) : (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>角色名稱</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {roles.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8">
                      沒有角色數據
                    </TableCell>
                  </TableRow>
                ) : (
                  roles.map((role) => (
                    <TableRow key={role.id}>
                      <TableCell>{role.id}</TableCell>
                      <TableCell className="font-medium">{role.name}</TableCell>
                      <TableCell>{role.description || "-"}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenPermissionDialog(role)}
                          >
                            <Shield className="h-4 w-4" />
                          </Button>
                          <PermissionGuard permission="role:update">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(role)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </PermissionGuard>
                          <PermissionGuard permission="role:delete">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(role)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </PermissionGuard>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        )}

        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>編輯角色</DialogTitle>
              <DialogDescription>
                更新角色信息
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-role-name">角色名稱</Label>
                <Input
                  id="edit-role-name"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  placeholder="例如: editor"
                />
              </div>
              <div>
                <Label htmlFor="edit-role-description">描述</Label>
                <Textarea
                  id="edit-role-description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="角色描述"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setIsEditDialogOpen(false)
                  setSelectedRole(null)
                  setFormData({ name: "", description: "" })
                }}
              >
                取消
              </Button>
              <Button onClick={handleUpdate}>更新</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog
          open={isPermissionDialogOpen}
          onOpenChange={setIsPermissionDialogOpen}
        >
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                管理角色權限: {selectedRole?.name}
              </DialogTitle>
              <DialogDescription>
                為角色分配或撤銷權限
              </DialogDescription>
            </DialogHeader>
            <PermissionGuard permission="permission:assign">
              <Tabs defaultValue="all" className="w-full">
                <TabsList>
                  <TabsTrigger value="all">全部權限</TabsTrigger>
                  {Object.keys(groupedPermissions).map((module) => (
                    <TabsTrigger key={module} value={module}>
                      {module}
                    </TabsTrigger>
                  ))}
                </TabsList>
                <TabsContent value="all" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    {permissions.map((permission) => {
                      const hasPermission = selectedRole?.permissions.some(
                        (p) => p.code === permission.code
                      )
                      return (
                        <div
                          key={permission.id}
                          className="flex items-center space-x-2 p-2 border rounded"
                        >
                          <Checkbox
                            checked={hasPermission || false}
                            onCheckedChange={() =>
                              handleTogglePermission(permission.code)
                            }
                          />
                          <div className="flex-1">
                            <div className="font-mono text-sm">
                              {permission.code}
                            </div>
                            {permission.description && (
                              <div className="text-xs text-muted-foreground">
                                {permission.description}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </TabsContent>
                {Object.entries(groupedPermissions).map(([module, perms]) => (
                  <TabsContent key={module} value={module} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      {perms.map((permission) => {
                        const hasPermission = selectedRole?.permissions.some(
                          (p) => p.code === permission.code
                        )
                        return (
                          <div
                            key={permission.id}
                            className="flex items-center space-x-2 p-2 border rounded"
                          >
                            <Checkbox
                              checked={hasPermission || false}
                              onCheckedChange={() =>
                                handleTogglePermission(permission.code)
                              }
                            />
                            <div className="flex-1">
                              <div className="font-mono text-sm">
                                {permission.code}
                              </div>
                              {permission.description && (
                                <div className="text-xs text-muted-foreground">
                                  {permission.description}
                                </div>
                              )}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </PermissionGuard>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setIsPermissionDialogOpen(false)
                  setSelectedRole(null)
                }}
              >
                關閉
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </PermissionGuard>
    </div>
  )
}

