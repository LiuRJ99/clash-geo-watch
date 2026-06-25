"""服务可达性检测模块"""

import time
import requests

from .config import proxies, CRITICAL_SERVICE_TARGETS, SERVICE_TEST_TIMEOUT
from .utils import log, now


def check_service(target):
    """检测单个服务"""
    start = time.time()

    try:
        r = requests.get(
            target["url"],
            proxies=proxies,
            timeout=SERVICE_TEST_TIMEOUT,
            allow_redirects=False,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0 Safari/537.36"
                )
            },
        )

        latency_ms = int((time.time() - start) * 1000)

        # 注意：
        # 200/204：明确可达
        # 301/302/307/308：跳转，通常也说明服务可达
        # 401/403：服务可达，但未登录、地区限制、权限限制或反爬
        # 429：服务可达，但被限流
        reachable_status_codes = {
            200, 204,
            301, 302, 303, 307, 308,
            401, 403, 404, 405, 429, 421,
        }

        ok = r.status_code in reachable_status_codes

        return {
            "name": target["name"],
            "url": target["url"],
            "ok": ok,
            "status_code": r.status_code,
            "latency_ms": latency_ms,
        }

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)

        return {
            "name": target["name"],
            "url": target["url"],
            "ok": False,
            "latency_ms": latency_ms,
            "error": str(e),
        }


def check_services():
    """检测所有服务"""
    results = []
    total = len(CRITICAL_SERVICE_TARGETS)

    for i, target in enumerate(CRITICAL_SERVICE_TARGETS, 1):
        name = target["name"]
        # log(f"[{now()}] 🌐 服务 [{i}/{total}] {name}: 检测中...")
        
        result = check_service(target)
        results.append(result)
        
        icon = "✅" if result.get("ok") else "❌"
        latency = result.get("latency_ms", "N/A")
        
        # 延迟颜色标识
        if latency == "N/A":
            latency_color = ""
        elif latency < 200:
            latency_color = "🟢"
        elif latency < 400:
            latency_color = "🔵"
        else:
            latency_color = "🟠"
        
        log(f"[{now()}] 🌐 服务 [{i}/{total}] {name}: {icon} {latency_color} ({latency}ms)")

    ok_count = sum(1 for r in results if r.get("ok"))
    return ok_count, results
