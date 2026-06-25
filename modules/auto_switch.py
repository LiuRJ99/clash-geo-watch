"""自动切换模块"""

import time
import json

from .config import (
    EXPECTED_COUNTRY,
    AUTO_SWITCH_MAX_ATTEMPTS,
    AUTO_SWITCH_INTERVAL_SECONDS,
    SWITCH_TEST_SLEEP_SECONDS,
    MIN_CRITICAL_SERVICE_OK,
    CRITICAL_SERVICE_TARGETS,
)
from .utils import log, now, macos_notify, macos_alert
from .geo_check import check_once
from .service_check import check_services
from .clash_api import (
    clash_current_node,
    clash_switch_node,
    clash_switch_us_node,
    clash_get_us_candidates,
)


def auto_switch_to_good_us_node():
    """自动切换到合格的美国节点"""
    # 先确保切换到美国自动选择分组
    try:
        current_node = clash_current_node()
        if current_node != "🇺🇸 美国自动选择":
            log(f"[{now()}] AUTO_SWITCH: 先切换到美国自动选择分组")
            clash_switch_node("🇺🇸 美国自动选择")
            time.sleep(2)
    except Exception as e:
        log(f"[{now()}] AUTO_SWITCH: 切换到美国分组失败：{e}")
    
    candidates = clash_get_us_candidates()

    if not candidates:
        log(f"[{now()}] AUTO_SWITCH: 没有找到美国候选节点，请检查节点命名")
        return False

    log(f"[{now()}] AUTO_SWITCH: 找到 {len(candidates)} 个美国候选节点")

    attempts = 0

    for node_name in candidates:
        attempts += 1

        if attempts > AUTO_SWITCH_MAX_ATTEMPTS:
            log(f"[{now()}] AUTO_SWITCH: 达到最大尝试次数 {AUTO_SWITCH_MAX_ATTEMPTS}")
            return False

        log(f"[{now()}] AUTO_SWITCH: 尝试切换到节点：{node_name}")

        try:
            # 切换美国自动选择分组内的具体节点
            clash_switch_us_node(node_name)
            time.sleep(SWITCH_TEST_SLEEP_SECONDS)

            ok, good_votes, bad_votes, results = check_once()

            # 格式化 GeoIP 检测结果
            log("")
            log(f"  📍 GeoIP 检测 - 节点：{node_name}")
            log(f"     投票: ✅ {good_votes} / ❌ {bad_votes} | 结果: {'✅ 合格' if ok else '❌ 不合格'}")
            for r in results:
                if "error" in r:
                    log(f"     • {r.get('source', 'unknown')}: ❌ {str(r.get('error', ''))[:50]}")
                else:
                    country = r.get("country", "N/A")
                    ip = r.get("ip", "N/A")
                    icon = "✅" if country == EXPECTED_COUNTRY else "❌"
                    log(f"     • {r.get('source', 'unknown')}: {icon} {country} ({ip})")

            if ok:
                service_ok_count, service_results = check_services()

                # 格式化服务检测结果
                log(f"  🌐 服务可达性检测 - 节点：{node_name}")
                log(f"     可达: {service_ok_count}/{len(CRITICAL_SERVICE_TARGETS)} | 要求: ≥{MIN_CRITICAL_SERVICE_OK}")
                for r in service_results:
                    icon = "✅" if r.get("ok") else "❌"
                    name = r.get("name", "unknown")
                    status_code = r.get("status_code", "N/A")
                    latency = r.get("latency_ms", "N/A")
                    log(f"     • {icon} {name}: {status_code} ({latency}ms)")

                if service_ok_count >= MIN_CRITICAL_SERVICE_OK:
                    log(f"[{now()}] AUTO_SWITCH: 成功切换到合格节点：{node_name}")
                    macos_notify(
                        "Clash 已自动切换节点",
                        f"已切换到合格美国节点：{node_name}，服务可达 {service_ok_count}/{len(CRITICAL_SERVICE_TARGETS)}"
                    )
                    return True

                log(
                    f"[{now()}] AUTO_SWITCH: 节点地区合格，但服务可达性不足："
                    f"{node_name}, {service_ok_count}/{len(CRITICAL_SERVICE_TARGETS)}"
                )
            else:
                log(f"[{now()}] AUTO_SWITCH: 节点不合格：{node_name}")

        except Exception as e:
            log(f"[{now()}] AUTO_SWITCH: 切换/检测失败：{node_name}, error={e}")

    log(f"[{now()}] AUTO_SWITCH: 没有找到合格美国节点")
    return False
