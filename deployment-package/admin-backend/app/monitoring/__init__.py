from prometheus_client import Counter, Gauge, Histogram

session_online_gauge = Gauge("session_online_count", "当前在线 Session 账号数")
command_enqueue_counter = Counter("command_enqueue_total", "指令排队次数", ["status"])
api_latency_histogram = Histogram("api_latency_seconds", "API 响应耗时", ["endpoint"])

