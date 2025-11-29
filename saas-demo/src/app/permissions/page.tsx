/**
 * 权限管理页面
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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useToast } from "@/hooks/use-toast"
import {
  listPermissions,
  createPermission,
  updatePermission,
  deletePermission,
  initPermissions,
  type Permission,
  type PermissionCreate,
  type PermissionUpdate,
} from "@/lib/api/permissions"
import { usePermissions } from "@/hooks/use-permissions"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { Plus, Edit, Trash2, RefreshCw, Shield, Users } from "lucide-react"
import { useRouter } from "next/navigation"

export default function PermissionsPage() {
  const router = useRouter()
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null)
  const [formData, setFormData] = useState<PermissionCreate>({
    code: "",
    description: "",
  })
  const { toast } = useToast()
  const { hasPermission } = usePermissions()

  const loadPermissions = async () => {
    try {
      setLoading(true)
      const data = await listPermissions()
      setPermissions(data)
    } catch (err) {
      toast({
        title: "错误",
        description: err instanceof Error ? err.message : "加载权限列表失败",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPermissions()
  }, [])

  const handleCreate = async () => {
    try {
      if (!formData.code.trim()) {
        toast({
          title: "错误",
          description: "权限代码不能為空",
          variant: "destructive",
        })
        return
      }

      await createPermission(formData)
      toast({
        title: "成功",
        description: "權限创建成功",
      })
      setIsCreateDialogOpen(false)
      setFormData({ code: "", description: "" })
      loadPermissions()
    } catch (err) {
      toast({
        title: "错误",
        description: err instanceof Error ? err.message : "创建權限失败",
        variant: "destructive",
      })
    }
  }

  const handleEdit = (permission: Permission) => {
    setEditingPermission(permission)
    setFormData({
      code: permission.code,
      description: permission.description || "",
    })
    setIsEditDialogOpen(true)
  }

  const handleUpdate = async () => {
    if (!editingPermission) return

    try {
      const update: PermissionUpdate = {}
      if (formData.code !== editingPermission.code) {
        update.code = formData.code
      }
      if (formData.description !== editingPermission.description) {
        update.description = formData.description
      }

      if (Object.keys(update).length === 0) {
        toast({
          title: "提示",
          description: "沒有變更",
        })
        return
      }

      await updatePermission(editingPermission.id, update)
      toast({
        title: "成功",
        description: "權限更新成功",
      })
      setIsEditDialogOpen(false)
      setEditingPermission(null)
      setFormData({ code: "", description: "" })
      loadPermissions()
    } catch (err) {
      toast({
        title: "错误",
        description: err instanceof Error ? err.message : "更新權限失败",
        variant: "destructive",
      })
    }
  }

  const handleDelete = async (permission: Permission) => {
    if (!confirm(`确定要删除權限 "${permission.code}" 嗎？`)) {
      return
    }

    try {
      await deletePermission(permission.id)
      toast({
        title: "成功",
        description: "權限删除成功",
      })
      loadPermissions()
    } catch (err) {
      toast({
        title: "错误",
        description: err instanceof Error ? err.message : "删除權限失败",
        variant: "destructive",
      })
    }
  }

  const handleInit = async () => {
    if (!confirm("确定要初始化系統權限嗎？這將创建所有預定義權限和角色。")) {
      return
    }

    try {
      const result = await initPermissions()
      toast({
        title: "成功",
        description: `初始化完成：创建了 ${result.permissions_created} 个權限和 ${result.roles_created} 个角色`,
      })
      loadPermissions()
    } catch (err) {
      toast({
        title: "错误",
        description: err instanceof Error ? err.message : "初始化权限失败",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Shield className="h-8 w-8" />
            权限管理
          </h1>
          <p className="text-muted-foreground mt-2">
            管理系統權限和角色權限分配
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => router.push("/permissions/roles")}
          >
            <Users className="h-4 w-4 mr-2" />
            角色管理
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push("/permissions/users")}
          >
            <Users className="h-4 w-4 mr-2" />
            用户角色管理
          </Button>
          <PermissionGuard permission="permission:view">
            <Button
              variant="outline"
              onClick={handleInit}
              disabled={loading}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              初始化权限
            </Button>
          </PermissionGuard>
          <PermissionGuard permission="permission:create">
            <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  创建權限
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>创建權限</DialogTitle>
                  <DialogDescription>
                    创建一个新的權限
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="code">权限代码</Label>
                    <Input
                      id="code"
                      value={formData.code}
                      onChange={(e) =>
                        setFormData({ ...formData, code: e.target.value })
                      }
                      placeholder="例如: account:create"
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">描述</Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) =>
                        setFormData({ ...formData, description: e.target.value })
                      }
                      placeholder="權限描述"
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
                  <Button onClick={handleCreate}>创建</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </PermissionGuard>
        </div>
      </div>

      <PermissionGuard permission="permission:view">
        {loading ? (
          <div className="text-center py-8">加载中...</div>
        ) : (
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>权限代码</TableHead>
                  <TableHead>描述</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {permissions.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8">
                      没有权限数据，請先初始化权限
                    </TableCell>
                  </TableRow>
                ) : (
                  permissions.map((permission) => (
                    <TableRow key={permission.id}>
                      <TableCell>{permission.id}</TableCell>
                      <TableCell className="font-mono text-sm">
                        {permission.code}
                      </TableCell>
                      <TableCell>{permission.description || "-"}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <PermissionGuard permission="permission:update">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEdit(permission)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </PermissionGuard>
                          <PermissionGuard permission="permission:delete">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(permission)}
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
              <DialogTitle>编辑權限</DialogTitle>
              <DialogDescription>
                更新權限信息
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-code">权限代码</Label>
                <Input
                  id="edit-code"
                  value={formData.code}
                  onChange={(e) =>
                    setFormData({ ...formData, code: e.target.value })
                  }
                  placeholder="例如: account:create"
                />
              </div>
              <div>
                <Label htmlFor="edit-description">描述</Label>
                <Textarea
                  id="edit-description"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  placeholder="權限描述"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setIsEditDialogOpen(false)
                  setEditingPermission(null)
                  setFormData({ code: "", description: "" })
                }}
              >
                取消
              </Button>
              <Button onClick={handleUpdate}>更新</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </PermissionGuard>
    </div>
  )
}

