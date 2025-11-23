import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ArrowUpRight, Calendar, Filter, MoreHorizontal } from "lucide-react";

const metrics = [
  {
    label: "月度經常性收入",
    value: "$128K",
    change: "+8.2%",
  },
  {
    label: "活躍客戶",
    value: "2,943",
    change: "+3.1%",
  },
  {
    label: "客戶留存率",
    value: "92.4%",
    change: "+1.6%",
  },
  {
    label: "NPS 滿意度",
    value: "64",
    change: "+4",
  },
];

const activities = [
  {
    name: "Rainbow Studio",
    detail: "升級至 Growth 方案",
    avatar: "RS",
    time: "2 小時前",
  },
  {
    name: "Atlas Labs",
    detail: "新建 3 個自動化流程",
    avatar: "AL",
    time: "5 小時前",
  },
  {
    name: "Northwind",
    detail: "提交年度續約",
    avatar: "NW",
    time: "昨天",
  },
];

const overviewRows = [
  {
    name: "功能使用率",
    value: "78%",
    trend: "+6.4%",
  },
  {
    name: "支援回應時間",
    value: "1h 12m",
    trend: "-14%",
  },
  {
    name: "自動化任務",
    value: "542",
    trend: "+12%",
  },
];

export default function DemoPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/40">
      <div className="container space-y-10 py-12">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-3">
            <Badge variant="outline" className="rounded-full px-4 py-1">
              SaaS 控制台預覽
            </Badge>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                成長儀表板
              </h1>
              <p className="mt-2 text-muted-foreground sm:max-w-2xl">
                追蹤核心營運指標、使用者行為與團隊協作情況，集中管理產品動態。
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="gap-2">
              <Calendar className="h-4 w-4" />
              本月
            </Button>
            <Button className="gap-2">
              建立報表
              <ArrowUpRight className="h-4 w-4" />
            </Button>
          </div>
        </header>

        <section className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <Card
              key={metric.label}
              className="border-border/70 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
            >
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {metric.label}
                </CardTitle>
                <Badge variant="secondary" className="text-xs font-medium">
                  {metric.change}
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-semibold">{metric.value}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <Card className="shadow-sm">
            <CardHeader className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>產品洞察</CardTitle>
                <CardDescription>
                  快速掌握產品動態與用戶反饋，支援策略決策。
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <NavigationMenu>
                  <NavigationMenuList>
                    <NavigationMenuItem>
                      <NavigationMenuLink
                        href="#"
                        className="rounded-full bg-muted px-3 py-1 text-xs font-medium hover:bg-primary hover:text-primary-foreground"
                      >
                        即時
                      </NavigationMenuLink>
                    </NavigationMenuItem>
                    <NavigationMenuItem>
                      <NavigationMenuLink
                        href="#"
                        className="rounded-full px-3 py-1 text-xs font-medium text-muted-foreground hover:bg-muted"
                      >
                        每週報
                      </NavigationMenuLink>
                    </NavigationMenuItem>
                  </NavigationMenuList>
                </NavigationMenu>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <Filter className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-44">
                    <DropdownMenuItem>營收</DropdownMenuItem>
                    <DropdownMenuItem>用戶成長</DropdownMenuItem>
                    <DropdownMenuItem>營運效率</DropdownMenuItem>
                    <DropdownMenuCheckboxItem checked>
                      整體概覽
                    </DropdownMenuCheckboxItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <Tabs defaultValue="overview" className="space-y-6">
                <TabsList className="w-full justify-start bg-muted/60">
                  <TabsTrigger value="overview">概覽</TabsTrigger>
                  <TabsTrigger value="details">詳情</TabsTrigger>
                  <TabsTrigger value="settings">設定</TabsTrigger>
                </TabsList>
                <TabsContent value="overview" className="space-y-6">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>指標</TableHead>
                        <TableHead className="text-right">目前值</TableHead>
                        <TableHead className="text-right">與上期比較</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {overviewRows.map((row) => (
                        <TableRow key={row.name}>
                          <TableCell className="font-medium">
                            {row.name}
                          </TableCell>
                          <TableCell className="text-right">
                            {row.value}
                          </TableCell>
                          <TableCell className="text-right text-emerald-600 dark:text-emerald-400">
                            {row.trend}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>
                <TabsContent value="details" className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Card className="border-dashed border-muted-foreground/40 bg-muted/50">
                      <CardContent className="space-y-3 py-6">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-16 w-full" />
                        <Skeleton className="h-4 w-32" />
                      </CardContent>
                    </Card>
                    <Card className="border-dashed border-muted-foreground/40 bg-muted/50">
                      <CardContent className="space-y-3 py-6">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-16 w-full" />
                        <Skeleton className="h-4 w-20" />
                      </CardContent>
                    </Card>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    正在建置進階圖表。完成後將顯示漏斗流程、功能採用率等指標。
                  </p>
                </TabsContent>
                <TabsContent value="settings">
                  <div className="space-y-4 rounded-lg border border-dashed border-muted-foreground/40 p-6">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                      <div className="space-y-1">
                        <h3 className="text-sm font-semibold">
                          自動化報表
                        </h3>
                        <p className="text-sm text-muted-foreground">
                          勾選後於每周一寄送最新趨勢摘要至收件人清單。
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Checkbox id="auto-report" defaultChecked />
                        <Label
                          htmlFor="auto-report"
                          className="text-sm text-muted-foreground"
                        >
                          啟用
                        </Label>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="report-note">附註訊息</Label>
                      <Textarea
                        id="report-note"
                        placeholder="向團隊說點什麼..."
                        className="resize-none"
                      />
                    </div>
                    <Button className="self-end">儲存偏好</Button>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle>即時活動</CardTitle>
                <CardDescription>
                  追蹤客戶與團隊在最新一週內的重點事件。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {activities.map((activity) => (
                  <div
                    key={activity.name}
                    className="flex items-center justify-between gap-3 rounded-xl border border-border/60 bg-card p-3 shadow-sm transition hover:border-primary/40 hover:shadow"
                  >
                    <div className="flex items-center gap-3">
                      <Avatar className="h-10 w-10">
                        <AvatarImage
                          src={`https://avatar.vercel.sh/${activity.avatar}`}
                        />
                        <AvatarFallback>{activity.avatar}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {activity.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {activity.detail}
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {activity.time}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>快速邀請</CardTitle>
                  <CardDescription>
                    分享最新儀表板與報表給你的協作者。
                  </CardDescription>
                </div>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">更多操作</span>
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="invite-email">Email</Label>
                  <Input
                    id="invite-email"
                    type="email"
                    placeholder="name@company.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-message">訊息</Label>
                  <Textarea
                    id="invite-message"
                    placeholder="我為你準備了一份全新的成長儀表板..."
                    className="resize-none"
                    rows={3}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Checkbox id="send-copy" defaultChecked />
                    <Label
                      htmlFor="send-copy"
                      className="text-sm text-muted-foreground"
                    >
                      發送副本給自己
                    </Label>
                  </div>
                  <Button variant="ghost" size="sm">
                    分享連結
                  </Button>
                </div>
                <Button className="w-full">發送邀請</Button>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}

