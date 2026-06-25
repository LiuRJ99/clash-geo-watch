# Clash Geo Watch

自动检测 Clash Verge 代理出口 IP 是否为指定国家（默认 US），并在异常时自动切换到合格节点。

## 功能特性

- **GeoIP 检测**：使用 9 个 GeoIP 服务分层检测，拿够 3 个有效源就停止
- **服务可达性检测**：检测 13 个核心 AI 服务是否可达
- **自动切换**：连续异常或延迟超阈值时自动遍历节点找到合格节点
- **节点过滤**：自动跳过 Error/Timeout/高延迟节点，按延迟排序
- **检测时间范围**：可设置每天的检测时间段
- **节点信息日志**：记录节点切换历史，包含 IP、位置、ISP、服务信息
- **延迟颜色标识**：绿色 (<200ms)、蓝色 (200-399ms)、橙色 (≥400ms)
- **macOS 通知**：异常时弹出系统通知提醒
- **本地日志**：所有检测结果写入日志文件

## 检测逻辑

```
GeoIP 必须 US（至少 2/3 源确认）
  ↓
核心服务至少 4/13 可达
  ↓
节点延迟 < 阈值（默认 300ms）
  ↓
接受该节点
```

**核心服务列表：**
- Google / Gemini / Google AI Studio / Antigravity
- ChatGPT / Codex / OpenAI API / OpenAI Platform
- Claude / Claude Platform / Anthropic API
- GitHub / GitHub Raw

## 文件结构

```
clash-test/
├── main.py              # 主入口
├── config.yaml          # 配置文件（YAML 格式，支持中文注释）
├── config.json          # 配置文件（JSON 格式，备用）
├── README.md            # 使用文档
├── clash_geo_watch.log  # 运行日志（自动生成）
├── node_history.log     # 节点历史日志（自动生成）
└── modules/
    ├── __init__.py      # 模块初始化
    ├── config.py        # 配置加载
    ├── utils.py         # 工具函数
    ├── geo_check.py     # GeoIP 检测（分层策略）
    ├── service_check.py # 服务检测
    ├── clash_api.py     # Clash API
    ├── auto_switch.py   # 自动切换
    └── node_logger.py   # 节点信息日志
```

## 快速开始

### 1. 安装依赖

```bash
python3 -m pip install requests pyyaml
```

### 2. 配置文件

编辑 `config.yaml` 修改配置（支持中文注释）：

```yaml
# 代理检测配置
proxy:
  url: "http://127.0.0.1:7897"
  expected_country: "US"
  interval_seconds: 3600
  bad_threshold: 3
  abnormal_check_interval_seconds: 60

# 检测时间范围
schedule:
  enabled: true
  start_hour: 10
  end_hour: 18

# Clash API 配置
clash_api:
  url: "http://127.0.0.1:9097"
  secret: "12345678"
  proxy_group: "🚀 节点选择"
  auto_switch: true

# 自动切换配置
auto_switch:
  max_attempts: 3
  interval_seconds: 300

# 节点过滤配置
node_filter:
  latency_threshold_ms: 300
  target_node_keywords:
    - "美国"
    - "US"
    - "🇺🇸"

# 服务检测配置
service_check:
  min_ok_count: 4
  timeout: 12
```

### 3. 配置 Clash Verge 规则

在规则最前面添加：

```yaml
rules:
  # GeoIP 检测
  - DOMAIN-SUFFIX,cloudflare.com,🚀 节点选择
  - DOMAIN-SUFFIX,ip-api.com,🚀 节点选择
  - DOMAIN-SUFFIX,ipapi.co,🚀 节点选择
  - DOMAIN-SUFFIX,ip.sb,🚀 节点选择
  - DOMAIN-SUFFIX,ipwhois.app,🚀 节点选择
  - DOMAIN-SUFFIX,ipinfo.io,🚀 节点选择
  - DOMAIN-SUFFIX,ipwho.is,🚀 节点选择
  - DOMAIN-SUFFIX,ifconfig.co,🚀 节点选择
  - DOMAIN-SUFFIX,reallyfreegeoip.org,🚀 节点选择

  # Google / Gemini / Antigravity
  - DOMAIN-SUFFIX,google.com,🚀 节点选择
  - DOMAIN-SUFFIX,googleapis.com,🚀 节点选择
  - DOMAIN-SUFFIX,gstatic.com,🚀 节点选择
  - DOMAIN-SUFFIX,googleusercontent.com,🚀 节点选择
  - DOMAIN-SUFFIX,aistudio.google.com,🚀 节点选择
  - DOMAIN-SUFFIX,gemini.google.com,🚀 节点选择
  - DOMAIN-SUFFIX,antigravity.google,🚀 节点选择

  # OpenAI / ChatGPT / Codex
  - DOMAIN-SUFFIX,chatgpt.com,🚀 节点选择
  - DOMAIN-SUFFIX,openai.com,🚀 节点选择
  - DOMAIN-SUFFIX,oaistatic.com,🚀 节点选择
  - DOMAIN-SUFFIX,oaiusercontent.com,🚀 节点选择

  # Claude / Anthropic
  - DOMAIN-SUFFIX,claude.ai,🚀 节点选择
  - DOMAIN-SUFFIX,anthropic.com,🚀 节点选择

  # GitHub
  - DOMAIN-SUFFIX,github.com,🚀 节点选择
  - DOMAIN-SUFFIX,githubusercontent.com,🚀 节点选择
```

### 4. 运行脚本

```bash
cd clash-test
python3 main.py
```

### 5. 后台运行

```bash
nohup python3 main.py > watcher.out 2>&1 &
```

### 6. 查看日志

```bash
# 运行日志
tail -f clash_geo_watch.log

# 节点历史日志
tail -f node_history.log
```

### 7. 停止脚本

```bash
ps aux | grep main.py
kill 进程号
```

## 配置项说明

### proxy - 代理检测配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `url` | `http://127.0.0.1:7897` | Clash Verge 代理端口 |
| `expected_country` | `US` | 目标国家代码 |
| `interval_seconds` | `3600` | 正常检测间隔（秒） |
| `bad_threshold` | `3` | 连续异常次数阈值 |
| `abnormal_check_interval_seconds` | `60` | 异常检测间隔（秒） |
| `log_file` | `clash_geo_watch.log` | 日志文件名 |

### schedule - 检测时间范围

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `enabled` | `true` | 是否启用时间范围限制 |
| `start_hour` | `10` | 检测开始时间（24小时制） |
| `end_hour` | `18` | 检测结束时间（24小时制） |

### clash_api - Clash API 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `url` | `http://127.0.0.1:9097` | Clash External Controller 地址 |
| `secret` | `12345678` | API 密钥 |
| `proxy_group` | `🚀 节点选择` | 代理组名 |
| `auto_switch` | `true` | 是否启用自动切换 |

### auto_switch - 自动切换配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `max_attempts` | `3` | 最大尝试切换次数 |
| `interval_seconds` | `300` | 每次切换间隔（秒） |
| `switch_test_sleep_seconds` | `3` | 切换后等待检测时间（秒） |

### node_filter - 节点过滤配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `latency_threshold_ms` | `300` | 延迟阈值（毫秒），超过会触发切换 |
| `target_node_keywords` | `["美国", "US", "🇺🇸", ...]` | 目标节点关键词 |

**节点过滤规则：**
- 自动跳过 `alive=False` 的节点（Error 状态）
- 自动跳过 `delay=0` 的节点（Timeout 状态）
- 自动跳过 `delay > latency_threshold_ms` 的节点
- 按延迟从小到大排序，优先尝试低延迟节点

### service_check - 服务检测配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `targets` | 13 个 AI 服务 | 核心服务列表 |
| `min_ok_count` | `4` | 最少可达服务数 |
| `timeout` | `12` | 服务检测超时（秒） |

## 输出示例

```
============================================================
[2026-06-24 18:09:04] ✅ 状态: OK (连续异常: 0/3)
============================================================
🏷️  当前节点: 🇺🇸美国04 | 合适下载使用-0.01倍
   分组: 🇺🇸 美国自动选择
   延迟: 🟢 ✅ 158ms (阈值: 300ms)
============================================================
📍 GeoIP 检测 (期望: US)
   投票: ✅ 3 / ❌ 1
   • cloudflare: ✅ US (108.181.24.47)
   • ip-api.com: ✅ US (134.195.101.194)
   • ipapi.co: ❌ 403 Client Error
   • ip.sb: ✅ US (134.195.101.194)
🌐 服务可达性 (要求: ≥4)
   可达: 13/13
   • ✅ Google: 204 🟢 (645ms)
   • ✅ Gemini: 200 🔵 (1886ms)
   • ✅ ChatGPT: 403 🟠 (2500ms)
   ...
============================================================

[2026-06-24 18:09:04] 📝 节点日志: 🇺🇸美国02-0.1倍 | 电信联通移动推荐 | US San Francisco | 134.195.101.194 | Black Mesa Corporation
   节点延迟: 🟢 150ms | 服务可达: 13/13 | 服务平均耗时: 🔵 1077ms
```

## 延迟颜色标识

| 颜色 | 节点延迟 | 服务延迟 |
|------|----------|----------|
| 🟢 绿色 | < 200ms | < 1000ms |
| 🔵 蓝色 | 200-399ms | 1000-1999ms |
| 🟠 橙色 | ≥ 400ms | ≥ 2000ms |

## GeoIP 检测源分层

**主力源（每轮必打）：**
- cloudflare（最稳定）
- ip-api.com（免费 HTTP）

**低频备用：**
- ipapi.co
- ip.sb
- ipwhois.app

**最后备用（容易 429）：**
- ipinfo.io
- ipwho.is
- ifconfig.co
- reallyfreegeoip.org

**优化规则：**
- 拿够 3 个有效源就停止请求
- 429 时自动冷却 10 分钟
- 冷却期间跳过该源

## 时间线逻辑

**场景1：节点一直正常**
```
00:00  检测1 → ✅ OK (bad_count=0)
       ↓ 等待 1 小时
01:00  检测2 → ✅ OK (bad_count=0)
...    一直正常，每小时检测一次
```

**场景2：节点异常，自动切换成功**
```
00:00  检测1 → ✅ OK (bad_count=0)
       ↓ 等待 1 小时
01:00  检测2 → ❌ BAD (bad_count=1)
       ↓ 等待 1 分钟
01:01  检测3 → ❌ BAD (bad_count=2)
       ↓ 等待 1 分钟
01:02  检测4 → ❌ BAD (bad_count=3) - 达到阈值！
       ↓ 开始自动切换 (尝试 1/3)
       ↓ 切换成功 ✅
       ↓ 等待 1 小时
02:02  检测5 → ✅ OK (bad_count=0)
```

**场景3：节点延迟超阈值，自动切换**
```
00:00  检测1 → ✅ OK，但延迟 500ms > 300ms
       ↓ 触发自动切换
       ↓ 切换成功 ✅，延迟 150ms
       ↓ 等待 1 小时
01:00  检测2 → ✅ OK (bad_count=0)
```

**场景4：节点异常，自动切换失败，3次后提醒**
```
00:00  检测1 → ✅ OK (bad_count=0)
       ↓ 等待 1 小时
01:00  检测2 → ❌ BAD (bad_count=1)
       ↓ 等待 1 分钟
01:01  检测3 → ❌ BAD (bad_count=2)
       ↓ 等待 1 分钟
01:02  检测4 → ❌ BAD (bad_count=3) - 达到阈值！
       ↓ 开始自动切换 (尝试 1/3)
       ↓ 切换失败 ❌
       ↓ 等待 5 分钟
01:07  自动切换 (尝试 2/3)
       ↓ 切换失败 ❌
       ↓ 等待 5 分钟
01:12  自动切换 (尝试 3/3)
       ↓ 切换失败 ❌
       ↓ ⚠️ 触发提醒：已尝试3次自动切换，均失败！请手动切换节点！
       ↓ 等待 1 小时
02:12  检测5 → ✅ OK 或 ❌ BAD
```

## 节点历史日志

**日志文件：** `node_history.log`

**记录时机：**
- 启动时记录一次
- 切换成功后记录一次

**日志格式：**
```json
{
  "time": "2026-06-24 18:09:04",
  "trigger": "startup",
  "node": "🇺🇸美国02-0.1倍 | 电信联通移动推荐",
  "group": "🇺🇸 美国自动选择",
  "latency_ms": 150,
  "ip": "134.195.101.194",
  "country": "US",
  "city": "San Francisco",
  "region": "California",
  "isp": "Black Mesa Corporation",
  "service_ok": 13,
  "service_total": 13,
  "service_avg_latency_ms": 608
}
```

## 切换地区

修改 `config.yaml` 即可切换到其他地区节点：

**日本节点：**
```yaml
proxy:
  expected_country: "JP"

node_filter:
  target_node_keywords:
    - "日本"
    - "JP"
    - "Japan"
    - "Tokyo"
    - "🇯🇵"
```

**新加坡节点：**
```yaml
proxy:
  expected_country: "SG"

node_filter:
  target_node_keywords:
    - "新加坡"
    - "SG"
    - "Singapore"
    - "🇸🇬"
```

## 依赖

- Python 3.9+
- requests
- pyyaml

```bash
python3 -m pip install requests pyyaml
```

## 注意事项

1. **配置文件**：优先使用 `config.yaml`（支持中文注释），也支持 `config.json`
2. **规则必须添加**：检测域名必须走代理组，否则检测结果不准确
3. **节点命名**：目标节点名需包含关键词
4. **自动切换会改变当前节点**：脚本会切换 Clash Verge 的代理组，影响所有流量
5. **检测时间范围**：默认只在 10:00-18:00 检测，其他时间自动等待
6. **日志文件**：运行日志写入 `clash_geo_watch.log`，节点历史写入 `node_history.log`

## 故障排查

### 配置文件不存在

如果配置文件不存在，脚本会使用默认配置并打印警告。

### 检测到的 IP 是中国 IP

- 检查规则是否正确添加
- 暂时切到 Global 模式验证
- 确认代理端口是否正确

### 自动切换失败

- 检查节点命名是否包含目标关键词
- 检查 Clash API 是否可访问
- 查看日志中的错误信息

### 服务检测失败

- 检查规则是否包含所有服务域名
- 确认代理节点可以访问这些服务
- 查看日志中的具体错误

### GeoIP 429 错误

- 脚本会自动冷却 10 分钟
- 冷却期间会使用其他源
- 不需要手动处理
