"""模块初始化文件"""

from .config import (
    CONFIG_FILE,
    CONFIG,
    PROXY_URL,
    EXPECTED_COUNTRY,
    INTERVAL_SECONDS,
    BAD_THRESHOLD,
    ABNORMAL_CHECK_INTERVAL_SECONDS,
    LOG_FILE,
    SCHEDULE_ENABLED,
    SCHEDULE_START_HOUR,
    SCHEDULE_END_HOUR,
    CLASH_API,
    CLASH_SECRET,
    PROXY_GROUP,
    AUTO_SWITCH,
    AUTO_SWITCH_STARTUP_CHECK,
    AUTO_SWITCH_MAX_ATTEMPTS,
    AUTO_SWITCH_INTERVAL_SECONDS,
    SWITCH_TEST_SLEEP_SECONDS,
    LATENCY_THRESHOLD_MS,
    TARGET_NODE_KEYWORDS,
    CRITICAL_SERVICE_TARGETS,
    MIN_CRITICAL_SERVICE_OK,
    SERVICE_TEST_TIMEOUT,
    proxies,
)

from .utils import now, log, macos_notify, macos_alert

from .geo_check import check_once

from .service_check import check_services

from .clash_api import (
    clash_headers,
    clash_get_proxies,
    clash_get_group,
    clash_current_node,
    clash_current_node_info,
    is_us_node_name,
    clash_get_us_candidates,
    clash_switch_node,
    clash_switch_us_node,
)

from .auto_switch import auto_switch_to_good_us_node

from .node_logger import log_node_info
