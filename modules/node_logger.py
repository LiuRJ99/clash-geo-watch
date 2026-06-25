"""节点信息日志模块"""

import json
from datetime import datetime

from .utils import log, now

# 节点信息日志文件
NODE_LOG_FILE = "node_history.log"


def log_node_info(node_name, latency_ms, geo_results=None, service_results=None, group=None, trigger="startup"):
    """记录节点信息到日志文件
    
    Args:
        node_name: 节点名称
        latency_ms: 延迟（毫秒）
        geo_results: GeoIP 检测结果（复用，不重复请求）
        service_results: 服务检测结果
        group: 所属分组
        trigger: 触发原因（startup/switch）
    """
    # 从 GeoIP 结果中提取信息（优先使用有完整信息的结果）
    ip = "N/A"
    country = "N/A"
    city = "N/A"
    region = "N/A"
    isp = "N/A"
    
    if geo_results:
        # 先找有完整信息的结果
        for r in geo_results:
            if r.get("ip") and not r.get("error") and r.get("city"):
                ip = r.get("ip", ip)
                country = r.get("country", country)
                city = r.get("city", city)
                region = r.get("region", region)
                isp = r.get("org") or r.get("isp") or r.get("asn") or "N/A"
                break
        
        # 如果没有完整信息，用第一个有 IP 的结果
        if ip == "N/A":
            for r in geo_results:
                if r.get("ip") and not r.get("error"):
                    ip = r.get("ip", ip)
                    country = r.get("country", country)
                    city = r.get("city", city)
                    region = r.get("region", region)
                    isp = r.get("org") or r.get("isp") or r.get("asn") or "N/A"
                    break
    
    # 计算服务可达性和平均耗时
    service_ok_count = 0
    service_total = 0
    service_avg_latency = 0
    
    if service_results:
        service_total = len(service_results)
        ok_latencies = []
        for r in service_results:
            if r.get("ok"):
                service_ok_count += 1
                latency = r.get("latency_ms")
                if latency and latency != "N/A":
                    ok_latencies.append(latency)
        if ok_latencies:
            service_avg_latency = int(sum(ok_latencies) / len(ok_latencies))
    
    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "trigger": trigger,
        "node": node_name,
        "group": group,
        "latency_ms": latency_ms,
        "ip": ip,
        "country": country,
        "city": city,
        "region": region,
        "isp": isp,
        "service_ok": service_ok_count,
        "service_total": service_total,
        "service_avg_latency_ms": service_avg_latency,
    }
    
    # 写入日志文件
    with open(NODE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # 延迟颜色标识
    if latency_ms < 200:
        latency_display = f"🟢 {latency_ms}ms"
    elif latency_ms < 400:
        latency_display = f"🔵 {latency_ms}ms"
    else:
        latency_display = f"🟠 {latency_ms}ms"
    
    # 服务平均耗时颜色标识
    if service_avg_latency < 1000:
        service_latency_display = f"🟢 {service_avg_latency}ms"
    elif service_avg_latency < 2000:
        service_latency_display = f"🔵 {service_avg_latency}ms"
    else:
        service_latency_display = f"🟠 {service_avg_latency}ms"
    
    # 控制台输出
    log(f"[{now()}] 📝 节点日志: {node_name} | {country} {city} | {ip} | {isp}")
    log(f"   节点延迟: {latency_display} | 服务可达: {service_ok_count}/{service_total} | 服务平均耗时: {service_latency_display}")
    
    return record
