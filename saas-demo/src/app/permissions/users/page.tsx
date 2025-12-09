/**
 * 用戶角色管理頁面
 */
"use client"

import React, { useState, useEffect, useRef, Suspense } from "react"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { useToast } from "@/hooks/use-toast"

// 懒加载重型组件
const Table = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.Table })), { ssr: false })
const TableBody = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableBody })), { ssr: false })
const TableCell = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableCell })), { ssr: false })
const TableHead = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHead })), { ssr: false })
const TableHeader = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableHeader })), { ssr: false })
const TableRow = dynamic(() => import("@/components/ui/table").then(mod => ({ default: mod.TableRow })), { ssr: false })
const Dialog = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.Dialog })), { ssr: false })
const DialogContent = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogContent })), { ssr: false })
const DialogDescription = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogDescription })), { ssr: false })
const DialogFooter = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogFooter })), { ssr: false })
const DialogHeader = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogHeader })), { ssr: false })
const DialogTitle = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogTitle })), { ssr: false })
const DialogTrigger = dynamic(() => import("@/components/ui/dialog").then(mod => ({ default: mod.DialogTrigger })), { ssr: false })
const Select = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.Select })), { ssr: false })
const SelectContent = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectContent })), { ssr: false })
const SelectItem = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectItem })), { ssr: false })
const SelectTrigger = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectTrigger })), { ssr: false })
const SelectValue = dynamic(() => import("@/components/ui/select").then(mod => ({ default: mod.SelectValue })), { ssr: false })
const Alert = dynamic(() => import("@/components/ui/alert").then(mod => ({ default: mod.Alert })), { ssr: false })
const AlertDescription = dynamic(() => import("@/components/ui/alert").then(mod => ({ default: mod.AlertDescription })), { ssr: false })
const AlertDialog = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialog })), { ssr: false })
const AlertDialogAction = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogAction })), { ssr: false })
const AlertDialogCancel = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogCancel })), { ssr: false })
const AlertDialogContent = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogContent })), { ssr: false })
const AlertDialogDescription = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogDescription })), { ssr: false })
const AlertDialogFooter = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogFooter })), { ssr: false })
const AlertDialogHeader = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogHeader })), { ssr: false })
const AlertDialogTitle = dynamic(() => import("@/components/ui/alert-dialog-center").then(mod => ({ default: mod.AlertDialogTitle })), { ssr: false })
import {
  listUsers,
  getUser,
  assignRoleToUser,
  revokeRoleFromUser,
  getUserRoles,
  batchAssignRole,
  batchRevokeRole,
  type User,
  type Role,
  type BatchOperationResult,
} from "@/lib/api/user-roles"
import {
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  getCurrentUser,
  type UserCreate,
  type UserUpdate,
  type UserPasswordReset,
} from "@/lib/api/users"
import {
  listRoles,
  type Role as SystemRole,
} from "@/lib/api/roles"
import { usePermissions } from "@/hooks/use-permissions"
import { PermissionGuard } from "@/components/permissions/permission-guard"
import { useQueryClient } from "@tanstack/react-query"
import { Users, Shield, Plus, X, Loader2, Edit, Trash2, Key, UserPlus } from "lucide-react"

export default function UserRolesPage() {
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<SystemRole[]>([])
  const [loading, setLoading] = useState(true)
  const [isRoleDialogOpen, setIsRoleDialogOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedRoleName, setSelectedRoleName] = useState<string>("")
  const [selectedUserIds, setSelectedUserIds] = useState<Set<number>>(new Set())
  const [isBatchDialogOpen, setIsBatchDialogOpen] = useState(false)
  const [batchOperationType, setBatchOperationType] = useState<"assign" | "revoke">("assign")
  const [batchRoleName, setBatchRoleName] = useState<string>("")
  const [batchProcessing, setBatchProcessing] = useState(false)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [isPasswordDialogOpen, setIsPasswordDialogOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [deletingUser, setDeletingUser] = useState<User | null>(null)
  const [passwordUser, setPasswordUser] = useState<User | null>(null)
  const [newUser, setNewUser] = useState<UserCreate>({
    email: "",
    password: "",
    full_name: "",
    is_active: true,
    is_superuser: false,
  })
  const [editUser, setEditUser] = useState<UserUpdate>({})
  const [newPassword, setNewPassword] = useState("")
  const [processing, setProcessing] = useState(false)
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const { toast } = useToast()
  const { hasPermission } = usePermissions()
  const queryClient = useQueryClient()
  const selectAllCheckboxRef = useRef<HTMLButtonElement>(null)

  const loadUsers = async () => {
    try {
      setLoading(true)
      const data = await listUsers()
      setUsers(data)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "加載用戶列表失敗",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const loadRoles = async () => {
    try {
      const data = await listRoles()
      setRoles(data)
    } catch (err) {
      console.error("加載角色列表失敗:", err)
    }
  }

  useEffect(() => {
    loadUsers()
    loadRoles()
    // 獲取當前用戶信息
    getCurrentUser()
      .then((user) => {
        // 轉換為 User 類型（從 user-roles API）
        setCurrentUser({
          id: user.id,
          email: user.email,
          full_name: user.full_name,
          is_active: user.is_active,
          is_superuser: user.is_superuser,
          roles: user.roles,
        })
      })
      .catch((err) => {
        console.error("獲取當前用戶失敗:", err)
      })
  }, [])

  const handleOpenRoleDialog = async (user: User) => {
    try {
      const userDetail = await getUser(user.id)
      setSelectedUser(userDetail)
      setSelectedRoleName("")
      setIsRoleDialogOpen(true)
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "獲取用戶詳情失敗",
        variant: "destructive",
      })
    }
  }

  const handleAssignRole = async () => {
    if (!selectedUser || !selectedRoleName) {
      toast({
        title: "錯誤",
        description: "請選擇角色",
        variant: "destructive",
      })
      return
    }

    try {
      await assignRoleToUser(selectedUser.id, {
        role_name: selectedRoleName,
      })
      toast({
        title: "成功",
        description: "角色已分配",
      })
      // 重新加載用戶詳情
      const updatedUser = await getUser(selectedUser.id)
      setSelectedUser(updatedUser)
      setSelectedRoleName("")
      loadUsers()
      // 清除權限緩存（角色變更可能影響權限）
      queryClient.invalidateQueries({ queryKey: ["permissions", "me"] })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "分配角色失敗",
        variant: "destructive",
      })
    }
  }

  const handleRevokeRole = async (user: User, roleName: string) => {
    if (!confirm(`確定要從用戶 ${user.email} 撤銷角色 "${roleName}" 嗎？`)) {
      return
    }

    try {
      await revokeRoleFromUser(user.id, roleName)
      toast({
        title: "成功",
        description: "角色已撤銷",
      })
      loadUsers()
      // 清除權限緩存（角色變更可能影響權限）
      queryClient.invalidateQueries({ queryKey: ["permissions", "me"] })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "撤銷角色失敗",
        variant: "destructive",
      })
    }
  }

  // 獲取用戶未分配的角色
  const getAvailableRoles = (user: User) => {
    const userRoleNames = new Set(user.roles.map((r) => r.name))
    return roles.filter((r) => !userRoleNames.has(r.name))
  }

  // 批量選擇相關函數
  const handleSelectUser = (userId: number, checked: boolean) => {
    setSelectedUserIds((prev) => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(userId)
      } else {
        newSet.delete(userId)
      }
      return newSet
    })
  }

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedUserIds(new Set(users.map((u) => u.id)))
    } else {
      setSelectedUserIds(new Set())
    }
  }

  const isAllSelected = users.length > 0 && selectedUserIds.size === users.length
  const isIndeterminate = selectedUserIds.size > 0 && selectedUserIds.size < users.length

  // 設置全選複選框的 indeterminate 狀態
  useEffect(() => {
    if (selectAllCheckboxRef.current) {
      // Checkbox 組件內部使用 input 元素，需要通過類型斷言訪問
      const input = selectAllCheckboxRef.current.querySelector('input') as HTMLInputElement | null
      if (input) {
        input.indeterminate = isIndeterminate
      }
    }
  }, [isIndeterminate])

  // 批量操作
  const handleOpenBatchDialog = (type: "assign" | "revoke") => {
    if (selectedUserIds.size === 0) {
      toast({
        title: "提示",
        description: "請至少選擇一個用戶",
        variant: "destructive",
      })
      return
    }
    setBatchOperationType(type)
    setBatchRoleName("")
    setIsBatchDialogOpen(true)
  }

  const handleBatchOperation = async () => {
    if (!batchRoleName) {
      toast({
        title: "錯誤",
        description: "請選擇角色",
        variant: "destructive",
      })
      return
    }

    if (selectedUserIds.size === 0) {
      toast({
        title: "錯誤",
        description: "請至少選擇一個用戶",
        variant: "destructive",
      })
      return
    }

    try {
      setBatchProcessing(true)
      const userIds = Array.from(selectedUserIds)
      let result: BatchOperationResult

      if (batchOperationType === "assign") {
        result = await batchAssignRole({
          user_ids: userIds,
          role_name: batchRoleName,
        })
      } else {
        result = await batchRevokeRole({
          user_ids: userIds,
          role_name: batchRoleName,
        })
      }

      // 顯示結果
      if (result.success_count > 0) {
        toast({
          title: "成功",
          description: `成功${batchOperationType === "assign" ? "分配" : "撤銷"} ${result.success_count} 個用戶的角色`,
        })
      }

      if (result.failed_count > 0) {
        toast({
          title: "部分失敗",
          description: `${result.failed_count} 個操作失敗。${result.errors.slice(0, 3).join("; ")}${result.errors.length > 3 ? "..." : ""}`,
          variant: "destructive",
        })
      }

      // 清空選擇並刷新列表
      setSelectedUserIds(new Set())
      setIsBatchDialogOpen(false)
      setBatchRoleName("")
      loadUsers()
      // 清除權限緩存（批量角色變更可能影響權限）
      queryClient.invalidateQueries({ queryKey: ["permissions", "me"] })
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "批量操作失敗",
        variant: "destructive",
      })
    } finally {
      setBatchProcessing(false)
    }
  }

  // 用戶管理功能
  const handleOpenCreateDialog = () => {
    setNewUser({
      email: "",
      password: "",
      full_name: "",
      is_active: true,
      is_superuser: false,
    })
    setIsCreateDialogOpen(true)
  }

  const handleCreateUser = async () => {
    if (!newUser.email || !newUser.password) {
      toast({
        title: "錯誤",
        description: "請填寫郵箱和密碼",
        variant: "destructive",
      })
      return
    }

    try {
      setProcessing(true)
      await createUser(newUser)
      toast({
        title: "成功",
        description: "用戶已創建",
      })
      setIsCreateDialogOpen(false)
      setNewUser({
        email: "",
        password: "",
        full_name: "",
        is_active: true,
        is_superuser: false,
      })
      loadUsers()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "創建用戶失敗",
        variant: "destructive",
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleOpenEditDialog = (user: User) => {
    setEditingUser(user)
    setEditUser({
      email: user.email,
      full_name: user.full_name || "",
      is_active: user.is_active,
      is_superuser: user.is_superuser,
    })
    setIsEditDialogOpen(true)
  }

  const handleUpdateUser = async () => {
    if (!editingUser) return

    try {
      setProcessing(true)
      await updateUser(editingUser.id, editUser)
      toast({
        title: "成功",
        description: "用戶信息已更新",
      })
      setIsEditDialogOpen(false)
      setEditingUser(null)
      setEditUser({})
      loadUsers()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "更新用戶失敗",
        variant: "destructive",
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleOpenDeleteDialog = (user: User) => {
    setDeletingUser(user)
    setIsDeleteDialogOpen(true)
  }

  const handleDeleteUser = async () => {
    if (!deletingUser) return

    try {
      setProcessing(true)
      await deleteUser(deletingUser.id)
      toast({
        title: "成功",
        description: "用戶已刪除",
      })
      setIsDeleteDialogOpen(false)
      setDeletingUser(null)
      loadUsers()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "刪除用戶失敗",
        variant: "destructive",
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleOpenPasswordDialog = (user: User) => {
    setPasswordUser(user)
    setNewPassword("")
    setIsPasswordDialogOpen(true)
  }

  const handleResetPassword = async () => {
    if (!passwordUser || !newPassword) {
      toast({
        title: "錯誤",
        description: "請輸入新密碼",
        variant: "destructive",
      })
      return
    }

    try {
      setProcessing(true)
      await resetUserPassword(passwordUser.id, { new_password: newPassword })
      toast({
        title: "成功",
        description: "密碼已重置",
      })
      setIsPasswordDialogOpen(false)
      setPasswordUser(null)
      setNewPassword("")
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "重置密碼失敗",
        variant: "destructive",
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleToggleActive = async (user: User) => {
    try {
      await updateUser(user.id, { is_active: !user.is_active })
      toast({
        title: "成功",
        description: `用戶已${!user.is_active ? "啟用" : "停用"}`,
      })
      loadUsers()
    } catch (err) {
      toast({
        title: "錯誤",
        description: err instanceof Error ? err.message : "更新用戶狀態失敗",
        variant: "destructive",
      })
    }
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Users className="h-8 w-8" />
            用戶角色管理
          </h1>
          <p className="text-muted-foreground mt-2">
            管理用戶角色分配
          </p>
        </div>
        <PermissionGuard permission="user:create">
          <Button onClick={handleOpenCreateDialog}>
            <UserPlus className="h-4 w-4 mr-2" />
            創建用戶
          </Button>
        </PermissionGuard>
      </div>

      <PermissionGuard permission="user:view">
        {loading ? (
          <div className="text-center py-8">加載中...</div>
        ) : (
          <div className="space-y-4">
            {/* 批量操作按鈕 */}
            <PermissionGuard permission="user:role:assign">
              {selectedUserIds.size > 0 && (
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">
                      已選擇 {selectedUserIds.size} 個用戶
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleOpenBatchDialog("assign")}
                    >
                      <Plus className="h-4 w-4 mr-2" />
                      批量分配角色
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleOpenBatchDialog("revoke")}
                    >
                      <X className="h-4 w-4 mr-2" />
                      批量撤銷角色
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedUserIds(new Set())}
                    >
                      清除選擇
                    </Button>
                  </div>
                </div>
              )}
            </PermissionGuard>

            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        ref={selectAllCheckboxRef}
                        checked={isAllSelected}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>郵箱</TableHead>
                    <TableHead>姓名</TableHead>
                    <TableHead>狀態</TableHead>
                    <TableHead>角色</TableHead>
                    <TableHead className="text-right">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center py-8">
                        沒有用戶數據
                      </TableCell>
                    </TableRow>
                  ) : (
                    users.map((user) => (
                      <TableRow key={user.id}>
                        <TableCell>
                          <Checkbox
                            checked={selectedUserIds.has(user.id)}
                            onCheckedChange={(checked) => handleSelectUser(user.id, checked as boolean)}
                          />
                        </TableCell>
                        <TableCell>{user.id}</TableCell>
                        <TableCell className="font-medium">{user.email}</TableCell>
                        <TableCell>{user.full_name || "-"}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <PermissionGuard permission="user:update">
                              <Switch
                                checked={user.is_active}
                                onCheckedChange={() => handleToggleActive(user)}
                              />
                            </PermissionGuard>
                            <Badge variant={user.is_active ? "default" : "secondary"}>
                              {user.is_active ? "啟用" : "停用"}
                            </Badge>
                            {user.is_superuser && (
                              <Badge variant="destructive" className="ml-2">
                                超級管理員
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {user.roles.length === 0 ? (
                              <span className="text-muted-foreground text-sm">無角色</span>
                            ) : (
                              user.roles.map((role) => (
                                <Badge key={role.id} variant="outline" className="flex items-center gap-1">
                                  {role.name}
                                  <PermissionGuard permission="user:role:assign">
                                    <button
                                      onClick={() => handleRevokeRole(user, role.name)}
                                      className="ml-1 hover:text-destructive"
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </PermissionGuard>
                                </Badge>
                              ))
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            <PermissionGuard permission="user:role:assign">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenRoleDialog(user)}
                              >
                                <Shield className="h-4 w-4 mr-1" />
                                分配角色
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="user:update">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenEditDialog(user)}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenPasswordDialog(user)}
                              >
                                <Key className="h-4 w-4" />
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="user:delete">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOpenDeleteDialog(user)}
                                disabled={user.id === currentUser?.id}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
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
          </div>
        )}
      </PermissionGuard>

      {/* 對話框組件 */}
      <Dialog open={isRoleDialogOpen} onOpenChange={setIsRoleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              為用戶分配角色: {selectedUser?.email}
            </DialogTitle>
            <DialogDescription>
              為用戶分配或撤銷角色
            </DialogDescription>
          </DialogHeader>
          <PermissionGuard permission="user:role:assign">
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">選擇角色</label>
                <Select
                  value={selectedRoleName}
                  onValueChange={setSelectedRoleName}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="選擇要分配的角色" />
                  </SelectTrigger>
                  <SelectContent>
                    {selectedUser && getAvailableRoles(selectedUser).length === 0 ? (
                      <SelectItem value="__no_roles__" disabled>
                        沒有可用的角色
                      </SelectItem>
                    ) : (
                      selectedUser &&
                      getAvailableRoles(selectedUser).map((role) => (
                        <SelectItem key={role.id} value={role.name}>
                          {role.name}
                          {role.description && ` - ${role.description}`}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
              {selectedUser && selectedUser.roles.length > 0 && (
                <div>
                  <label className="text-sm font-medium mb-2 block">當前角色</label>
                  <div className="flex flex-wrap gap-2">
                    {selectedUser.roles.map((role) => (
                      <Badge key={role.id} variant="outline" className="flex items-center gap-1">
                        {role.name}
                        <button
                          onClick={() => handleRevokeRole(selectedUser, role.name)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </PermissionGuard>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsRoleDialogOpen(false)
                setSelectedUser(null)
                setSelectedRoleName("")
              }}
            >
              關閉
            </Button>
            <PermissionGuard permission="user:role:assign">
              <Button
                onClick={handleAssignRole}
                disabled={!selectedRoleName}
              >
                <Plus className="h-4 w-4 mr-2" />
                分配角色
              </Button>
            </PermissionGuard>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 批量操作對話框 */}
      <Dialog open={isBatchDialogOpen} onOpenChange={setIsBatchDialogOpen}>
              <DialogContent>
                <DialogHeader>
                <DialogTitle>
                  {batchOperationType === "assign" ? "批量分配角色" : "批量撤銷角色"}
                </DialogTitle>
                <DialogDescription>
                  為 {selectedUserIds.size} 個用戶{batchOperationType === "assign" ? "分配" : "撤銷"}角色
                </DialogDescription>
              </DialogHeader>
              <PermissionGuard permission="user:role:assign">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">選擇角色</label>
                    <Select
                      value={batchRoleName}
                      onValueChange={setBatchRoleName}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="選擇角色" />
                      </SelectTrigger>
                      <SelectContent>
                        {roles.map((role) => (
                          <SelectItem key={role.id} value={role.name}>
                            {role.name}
                            {role.description && ` - ${role.description}`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {batchOperationType === "revoke" && (
                    <Alert>
                      <AlertDescription>
                        此操作將從所有選中的用戶撤銷該角色。請確認操作。
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              </PermissionGuard>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsBatchDialogOpen(false)
                    setBatchRoleName("")
                  }}
                  disabled={batchProcessing}
                >
                  取消
                </Button>
                <PermissionGuard permission="user:role:assign">
                  <Button
                    onClick={handleBatchOperation}
                    disabled={!batchRoleName || batchProcessing}
                  >
                    {batchProcessing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        處理中...
                      </>
                    ) : (
                      <>
                        {batchOperationType === "assign" ? (
                          <>
                            <Plus className="h-4 w-4 mr-2" />
                            分配
                          </>
                        ) : (
                          <>
                            <X className="h-4 w-4 mr-2" />
                            撤銷
                          </>
                        )}
                      </>
                    )}
                  </Button>
                </PermissionGuard>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          {/* 創建用戶對話框 */}
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>創建新用戶</DialogTitle>
                <DialogDescription>
                  填寫用戶信息以創建新用戶
                </DialogDescription>
              </DialogHeader>
              <PermissionGuard permission="user:create">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="create-email">郵箱 *</Label>
                    <Input
                      id="create-email"
                      type="email"
                      value={newUser.email}
                      onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                      placeholder="user@example.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="create-password">密碼 *</Label>
                    <Input
                      id="create-password"
                      type="password"
                      value={newUser.password}
                      onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                      placeholder="輸入密碼"
                    />
                  </div>
                  <div>
                    <Label htmlFor="create-full-name">姓名</Label>
                    <Input
                      id="create-full-name"
                      value={newUser.full_name || ""}
                      onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                      placeholder="用戶姓名（可選）"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="create-active">啟用狀態</Label>
                    <Switch
                      id="create-active"
                      checked={newUser.is_active}
                      onCheckedChange={(checked) => setNewUser({ ...newUser, is_active: checked })}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="create-superuser">超級管理員</Label>
                    <Switch
                      id="create-superuser"
                      checked={newUser.is_superuser}
                      onCheckedChange={(checked) => setNewUser({ ...newUser, is_superuser: checked })}
                    />
                  </div>
                </div>
              </PermissionGuard>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                  disabled={processing}
                >
                  取消
                </Button>
                <PermissionGuard permission="user:create">
                  <Button onClick={handleCreateUser} disabled={processing || !newUser.email || !newUser.password}>
                    {processing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        創建中...
                      </>
                    ) : (
                      <>
                        <UserPlus className="h-4 w-4 mr-2" />
                        創建
                      </>
                    )}
                  </Button>
                </PermissionGuard>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          
          {/* 編輯用戶對話框 */}
          <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>編輯用戶: {editingUser?.email}</DialogTitle>
                <DialogDescription>
                  更新用戶信息
                </DialogDescription>
              </DialogHeader>
              <PermissionGuard permission="user:update">
                {editingUser && (
                  <div className="space-y-4">
                    <div>
                      <Label htmlFor="edit-email">郵箱</Label>
                      <Input
                        id="edit-email"
                        type="email"
                        value={editUser.email || editingUser.email}
                        onChange={(e) => setEditUser({ ...editUser, email: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="edit-full-name">姓名</Label>
                      <Input
                        id="edit-full-name"
                        value={editUser.full_name !== undefined ? editUser.full_name : (editingUser.full_name || "")}
                        onChange={(e) => setEditUser({ ...editUser, full_name: e.target.value })}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="edit-active">啟用狀態</Label>
                      <Switch
                        id="edit-active"
                        checked={editUser.is_active !== undefined ? editUser.is_active : editingUser.is_active}
                        onCheckedChange={(checked) => setEditUser({ ...editUser, is_active: checked })}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="edit-superuser">超級管理員</Label>
                      <Switch
                        id="edit-superuser"
                        checked={editUser.is_superuser !== undefined ? editUser.is_superuser : editingUser.is_superuser}
                        onCheckedChange={(checked) => setEditUser({ ...editUser, is_superuser: checked })}
                      />
                    </div>
                  </div>
                )}
              </PermissionGuard>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsEditDialogOpen(false)
                    setEditingUser(null)
                    setEditUser({})
                  }}
                  disabled={processing}
                >
                  取消
                </Button>
                <PermissionGuard permission="user:update">
                  <Button onClick={handleUpdateUser} disabled={processing}>
                    {processing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        更新中...
                      </>
                    ) : (
                      <>
                        <Edit className="h-4 w-4 mr-2" />
                        更新
                      </>
                    )}
                  </Button>
                </PermissionGuard>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          {/* 刪除用戶確認對話框 */}
          <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>確認刪除用戶</AlertDialogTitle>
                <AlertDialogDescription>
                  確定要刪除用戶 <strong>{deletingUser?.email}</strong> 嗎？此操作無法撤銷。
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel disabled={processing}>取消</AlertDialogCancel>
                <PermissionGuard permission="user:delete">
                  <AlertDialogAction
                    onClick={handleDeleteUser}
                    disabled={processing}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {processing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        刪除中...
                      </>
                    ) : (
                      <>
                        <Trash2 className="h-4 w-4 mr-2" />
                        刪除
                      </>
                    )}
                  </AlertDialogAction>
                </PermissionGuard>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          
          {/* 重置密碼對話框 */}
          <Dialog open={isPasswordDialogOpen} onOpenChange={setIsPasswordDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>重置密碼: {passwordUser?.email}</DialogTitle>
                <DialogDescription>
                  為用戶設置新密碼
                </DialogDescription>
              </DialogHeader>
              <PermissionGuard permission="user:update">
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="new-password">新密碼 *</Label>
                    <Input
                      id="new-password"
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="輸入新密碼"
                    />
                  </div>
                  <Alert>
                    <AlertDescription>
                      請確保新密碼足夠安全。重置後用戶需要使用新密碼登錄。
                    </AlertDescription>
                  </Alert>
                </div>
              </PermissionGuard>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setIsPasswordDialogOpen(false)
                    setPasswordUser(null)
                    setNewPassword("")
                  }}
                  disabled={processing}
                >
                  取消
                </Button>
                <PermissionGuard permission="user:update">
                  <Button onClick={handleResetPassword} disabled={processing || !newPassword}>
                    {processing ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        重置中...
                      </>
                    ) : (
                      <>
                        <Key className="h-4 w-4 mr-2" />
                        重置
                      </>
                    )}
                  </Button>
                </PermissionGuard>
              </DialogFooter>
            </DialogContent>
          </Dialog>
    </div>
  )
}

