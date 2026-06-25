"""GeoIP 检测模块

分层策略：
- 主力源：cloudflare、ip-api.com（每轮必打）
- 低频备用：ipapi.co、ip.sb、ipwhois.app
- 最后备用：ipinfo.io、ipwho.is、ifconfig.co、reallyfreegeoip.org

优化规则：
- 拿够 3 个有效源就停止请求
- 429 时标记冷却，避免频繁请求
- 冷却期间跳过该源
"""

import time
import requests

from .config import proxies, EXPECTED_COUNTRY
from .utils import log, now

# 源冷却管理（避免 429）
_source_cooldown = {}  # {source_name: cooldown_until_timestamp}
COOLDOWN_SECONDS = 600  # 429 后冷却 10 分钟

# 需要 User-Agent 的源
UA_HEADERS = {"User-Agent": "Mozilla/5.0 clash-geo-watch/1.0"}


def _is_source_available(source_name):
    """检查源是否可用（不在冷却期）"""
    if source_name not in _source_cooldown:
        return True
    return time.time() > _source_cooldown[source_name]


def _mark_source_cooldown(source_name):
    """标记源进入冷却期"""
    _source_cooldown[source_name] = time.time() + COOLDOWN_SECONDS


# ====== GeoIP 检测函数 ======

def check_cloudflare():
    """检测 cloudflare（最稳定，每轮必打）"""
    r = requests.get(
        "https://www.cloudflare.com/cdn-cgi/trace",
        proxies=proxies,
        timeout=10,
    )
    r.raise_for_status()

    parsed = {}
    for line in r.text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            parsed[k] = v

    return {
        "source": "cloudflare",
        "ip": parsed.get("ip"),
        "country": parsed.get("loc"),
        "city": None,
        "region": None,
        "org": None,
    }


def check_ipapi_com():
    """检测 ip-api.com（免费 HTTP，适合低频轮询）"""
    r = requests.get(
        "http://ip-api.com/json/?fields=status,message,query,countryCode,city,regionName,isp,org,as",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "ip-api.com",
        "ip": data.get("query"),
        "country": data.get("countryCode"),
        "city": data.get("city"),
        "region": data.get("regionName"),
        "org": data.get("org") or data.get("isp"),
        "asn": data.get("as"),
    }


def check_ipapi_co():
    """检测 ipapi.co"""
    r = requests.get(
        "https://ipapi.co/json/",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "ipapi.co",
        "ip": data.get("ip"),
        "country": data.get("country_code"),
        "city": data.get("city"),
        "region": data.get("region"),
        "org": data.get("org"),
        "asn": data.get("asn"),
    }


def check_ipsb():
    """检测 ip.sb"""
    r = requests.get(
        "https://api.ip.sb/geoip",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "ip.sb",
        "ip": data.get("ip"),
        "country": data.get("country_code"),
        "city": data.get("city"),
        "region": data.get("region"),
        "org": data.get("organization") or data.get("isp"),
        "asn": data.get("asn"),
    }


def check_ipwhois_app():
    """检测 ipwhois.app"""
    r = requests.get(
        "https://ipwhois.app/json/",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "ipwhois.app",
        "ip": data.get("ip"),
        "country": data.get("country_code"),
        "city": data.get("city"),
        "region": data.get("region"),
        "org": data.get("org") or data.get("isp"),
        "asn": data.get("asn"),
    }


def check_ipinfo():
    """检测 ipinfo.io（容易 429，备用）"""
    r = requests.get(
        "https://ipinfo.io/json",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "ipinfo.io",
        "ip": data.get("ip"),
        "country": data.get("country"),
        "city": data.get("city"),
        "region": data.get("region"),
        "org": data.get("org"),
    }


def check_ipwho():
    """检测 ipwho.is（容易 429，备用）"""
    r = requests.get(
        "https://ipwho.is/",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "ipwho.is",
        "ip": data.get("ip"),
        "country": data.get("country_code"),
        "city": data.get("city"),
        "region": data.get("region"),
        "org": data.get("connection", {}).get("org"),
        "asn": data.get("connection", {}).get("asn"),
    }


def check_ifconfig_co():
    """检测 ifconfig.co（备用）"""
    r = requests.get(
        "https://ifconfig.co/json",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "ifconfig.co",
        "ip": data.get("ip"),
        "country": data.get("country_iso") or data.get("country"),
        "city": data.get("city"),
        "region": data.get("region_name") or data.get("region"),
        "org": data.get("asn_org"),
        "asn": data.get("asn"),
    }


def check_reallyfreegeoip():
    """检测 reallyfreegeoip.org（最后备用）"""
    r = requests.get(
        "https://reallyfreegeoip.org/json/",
        proxies=proxies,
        timeout=10,
        headers=UA_HEADERS,
    )
    r.raise_for_status()
    data = r.json()

    return {
        "source": "reallyfreegeoip.org",
        "ip": data.get("ip"),
        "country": data.get("country_code"),
        "city": data.get("city"),
        "region": data.get("region_code") or data.get("region_name"),
        "org": None,
        "asn": None,
    }


# ====== 分层检测源列表 ======
# 顺序：主力源 → 低频备用 → 最后备用
CHECKS = [
    # 主力源（每轮必打）
    ("cloudflare", check_cloudflare),
    ("ip-api.com", check_ipapi_com),
    # 低频备用
    ("ipapi.co", check_ipapi_co),
    ("ip.sb", check_ipsb),
    ("ipwhois.app", check_ipwhois_app),
    # 最后备用（容易 429）
    ("ipinfo.io", check_ipinfo),
    ("ipwho.is", check_ipwho),
    ("ifconfig.co", check_ifconfig_co),
    ("reallyfreegeoip.org", check_reallyfreegeoip),
]


def check_once():
    """执行一次 GeoIP 检测（分层策略）"""
    results = []
    total_sources = len(CHECKS)

    for i, (source_name, fn) in enumerate(CHECKS, 1):
        # 拿够 3 个有效源就停止
        valid_count = sum(1 for r in results if r.get("country"))
        if valid_count >= 3:
            log(f"[{now()}] 📍 GeoIP: 已获取 {valid_count} 个有效源，跳过剩余")
            break

        # 检查源是否在冷却期
        if not _is_source_available(source_name):
            results.append({
                "source": source_name,
                "skipped": True,
                "reason": "cooldown (429)",
            })
            log(f"[{now()}] 📍 GeoIP [{i}/{total_sources}] {source_name}: ⏭️ 冷却中")
            continue

        # log(f"[{now()}] 📍 GeoIP [{i}/{total_sources}] {source_name}: 检测中...")
        try:
            result = fn()
            result["source"] = source_name
            results.append(result)
            country = result.get("country", "N/A")
            icon = "✅" if country == EXPECTED_COUNTRY else "❌"
            log(f"[{now()}] 📍 GeoIP [{i}/{total_sources}] {source_name}: {icon} {country}")
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None

            # 429 时标记冷却
            if status_code == 429:
                _mark_source_cooldown(source_name)

            results.append({
                "source": source_name,
                "error": str(e),
                "status_code": status_code,
            })
            log(f"[{now()}] 📍 GeoIP [{i}/{total_sources}] {source_name}: ❌ {status_code}")
        except Exception as e:
            results.append({
                "source": source_name,
                "error": str(e),
            })
            log(f"[{now()}] 📍 GeoIP [{i}/{total_sources}] {source_name}: ❌ 错误")

    # 统计投票（包含失败的请求）
    valid_results = [r for r in results if not r.get("skipped")]
    
    good_votes = 0
    bad_votes = 0
    
    for r in valid_results:
        if r.get("error"):
            # 请求失败，算作 ❌
            bad_votes += 1
        elif r.get("country"):
            if r.get("country") == EXPECTED_COUNTRY:
                good_votes += 1
            else:
                bad_votes += 1
    
    valid_count = good_votes + bad_votes

    # 判断逻辑
    if valid_count < 2:
        # 有效源不足，不自动切换
        ok = False
    else:
        # 至少 2 个源显示目标国家，才认为正常
        ok = good_votes >= 2

    return ok, good_votes, bad_votes, results
