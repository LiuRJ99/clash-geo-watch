"""配置加载模块"""

import json
import os
import yaml

# 配置文件路径（优先使用 YAML，其次 JSON）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE_YAML = os.path.join(BASE_DIR, "config.yaml")
CONFIG_FILE_JSON = os.path.join(BASE_DIR, "config.json")

# 确定使用的配置文件
if os.path.exists(CONFIG_FILE_YAML):
    CONFIG_FILE = CONFIG_FILE_YAML
elif os.path.exists(CONFIG_FILE_JSON):
    CONFIG_FILE = CONFIG_FILE_JSON
else:
    CONFIG_FILE = CONFIG_FILE_YAML  # 默认使用 YAML


def load_config():
    """加载配置文件，如果不存在则使用默认值"""
    default_config = {
        "proxy": {
            "url": "http://127.0.0.1:7897",
            "expected_country": "US",
            "interval_seconds": 3600,
            "bad_threshold": 3,
            "abnormal_check_interval_seconds": 60,
            "log_file": "clash_geo_watch.log"
        },
        "schedule": {
            "enabled": True,
            "start_hour": 10,
            "end_hour": 17
        },
        "clash_api": {
            "url": "http://127.0.0.1:9097",
            "secret": "12345678",
            "proxy_group": "🚀 节点选择",
            "auto_switch": True
        },
        "auto_switch": {
            "startup_check": False,
            "max_attempts": 3,
            "interval_seconds": 300,
            "switch_test_sleep_seconds": 3
        },
        "node_filter": {
            "latency_min_threshold_ms": 50,
            "latency_max_threshold_ms": 500,
            "target_node_keywords": [
                "美国", "美國", "US", "USA", "United States", "America",
                "Los Angeles", "LA", "San Jose", "Silicon Valley",
                "New York", "Seattle", "Dallas", "🇺🇸"
            ]
        },
        "service_check": {
            "targets": [
                {"name": "Google", "url": "https://www.google.com/generate_204"},
                {"name": "Gemini", "url": "https://gemini.google.com/"},
                {"name": "Google AI Studio", "url": "https://aistudio.google.com/"},
                {"name": "Antigravity", "url": "https://antigravity.google/"},
                {"name": "ChatGPT", "url": "https://chatgpt.com/"},
                {"name": "Codex", "url": "https://chatgpt.com/codex"},
                {"name": "OpenAI API", "url": "https://api.openai.com/"},
                {"name": "OpenAI Platform", "url": "https://platform.openai.com/"},
                {"name": "Claude", "url": "https://claude.ai/"},
                {"name": "Claude Platform", "url": "https://platform.claude.com/"},
                {"name": "Anthropic API", "url": "https://api.anthropic.com/"}
            ],
            "min_ok_count": 4,
            "timeout": 12
        }
    }

    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                if CONFIG_FILE.endswith(".yaml") or CONFIG_FILE.endswith(".yml"):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            # 合并默认值（处理缺失的配置项）
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
                elif isinstance(default_config[key], dict):
                    for sub_key in default_config[key]:
                        if sub_key not in config[key]:
                            config[key][sub_key] = default_config[key][sub_key]
            return config
        else:
            print(f"[WARNING] 配置文件不存在: {CONFIG_FILE}")
            print(f"[WARNING] 使用默认配置")
            return default_config
    except Exception as e:
        print(f"[ERROR] 加载配置文件失败: {e}")
        print(f"[WARNING] 使用默认配置")
        return default_config


# 加载配置
CONFIG = load_config()

# 从配置文件读取配置
PROXY_URL = CONFIG["proxy"]["url"]
EXPECTED_COUNTRY = CONFIG["proxy"]["expected_country"]
INTERVAL_SECONDS = CONFIG["proxy"]["interval_seconds"]
BAD_THRESHOLD = CONFIG["proxy"]["bad_threshold"]
ABNORMAL_CHECK_INTERVAL_SECONDS = CONFIG["proxy"]["abnormal_check_interval_seconds"]
LOG_FILE = CONFIG["proxy"]["log_file"]

SCHEDULE_ENABLED = CONFIG["schedule"]["enabled"]
SCHEDULE_START_HOUR = CONFIG["schedule"]["start_hour"]
SCHEDULE_END_HOUR = CONFIG["schedule"]["end_hour"]

CLASH_API = CONFIG["clash_api"]["url"]
CLASH_SECRET = CONFIG["clash_api"]["secret"]
PROXY_GROUP = CONFIG["clash_api"]["proxy_group"]
AUTO_SWITCH = CONFIG["clash_api"]["auto_switch"]

AUTO_SWITCH_STARTUP_CHECK = CONFIG["auto_switch"]["startup_check"]
AUTO_SWITCH_MAX_ATTEMPTS = CONFIG["auto_switch"]["max_attempts"]
AUTO_SWITCH_INTERVAL_SECONDS = CONFIG["auto_switch"]["interval_seconds"]
SWITCH_TEST_SLEEP_SECONDS = CONFIG["auto_switch"]["switch_test_sleep_seconds"]

LATENCY_MIN_THRESHOLD_MS = CONFIG["node_filter"]["latency_min_threshold_ms"]
LATENCY_MAX_THRESHOLD_MS = CONFIG["node_filter"]["latency_max_threshold_ms"]
TARGET_NODE_KEYWORDS = CONFIG["node_filter"]["target_node_keywords"]

CRITICAL_SERVICE_TARGETS = CONFIG["service_check"]["targets"]
MIN_CRITICAL_SERVICE_OK = CONFIG["service_check"]["min_ok_count"]
SERVICE_TEST_TIMEOUT = CONFIG["service_check"]["timeout"]

# 代理配置
proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL,
}
