"""Clash API 模块"""

import urllib.parse
import requests

from .config import CLASH_API, CLASH_SECRET, PROXY_GROUP, TARGET_NODE_KEYWORDS, LATENCY_MIN_THRESHOLD_MS, LATENCY_MAX_THRESHOLD_MS
from .utils import log, now


def clash_headers():
    """获取 Clash API 请求头"""
    headers = {}
    if CLASH_SECRET:
        headers["Authorization"] = f"Bearer {CLASH_SECRET}"
    return headers


def clash_get_proxies():
    """获取所有代理信息"""
    url = f"{CLASH_API}/proxies"
    r = requests.get(
        url,
        headers=clash_headers(),
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def clash_get_group():
    """获取代理组信息"""
    data = clash_get_proxies()
    proxies_data = data.get("proxies", {})
    group = proxies_data.get(PROXY_GROUP)
    if not group:
        raise RuntimeError(f"找不到代理组：{PROXY_GROUP}")
    return group


def clash_current_node():
    """获取当前节点"""
    group = clash_get_group()
    return group.get("now")


def clash_current_node_info():
    """获取当前节点详细信息（包括延迟）"""
    current_node = clash_current_node()
    data = clash_get_proxies()
    proxies_data = data.get("proxies", {})
    node_info = proxies_data.get(current_node, {})
    
    # 如果是分组，获取实际使用的节点
    node_type = node_info.get("type", "")
    if node_type in ["URLTest", "Selector", "Fallback"]:
        actual_node = node_info.get("now", current_node)
        actual_info = proxies_data.get(actual_node, {})
        history = actual_info.get("history", [])
        latency = history[-1].get("delay", 0) if history else 0
        return {
            "name": actual_node,
            "group": current_node,
            "latency_ms": latency,
            "alive": actual_info.get("alive", True),
        }
    
    history = node_info.get("history", [])
    latency = history[-1].get("delay", 0) if history else 0
    
    return {
        "name": current_node,
        "group": None,
        "latency_ms": latency,
        "alive": node_info.get("alive", True),
    }


def is_us_node_name(name):
    """检查节点名是否是美国节点"""
    upper_name = name.upper()
    for keyword in TARGET_NODE_KEYWORDS:
        if keyword.upper() in upper_name:
            return True
    return False


def clash_get_us_candidates():
    """获取美国候选节点列表"""
    group = clash_get_group()
    all_nodes = group.get("all", [])
    now_node = group.get("now")
    
    # 获取所有代理节点信息
    data = clash_get_proxies()
    proxies_data = data.get("proxies", {})
    
    candidates = []
    
    for node_name in all_nodes:
        # 检查节点名是否包含美国关键词
        if is_us_node_name(node_name):
            node_info = proxies_data.get(node_name, {})
            node_type = node_info.get("type", "")
            
            # 如果是 URLTest/Selector 分组，获取其子节点
            if node_type in ["URLTest", "Selector", "Fallback"]:
                sub_nodes = node_info.get("all", [])
                for sub_node in sub_nodes:
                    if sub_node not in candidates:
                        candidates.append(sub_node)
            else:
                if node_name not in candidates:
                    candidates.append(node_name)
    
    # 过滤掉不可用节点（Error、Timeout、delay=0 等）
    filtered_candidates = []
    for node_name in candidates:
        node_info = proxies_data.get(node_name, {})
        alive = node_info.get("alive", True)
        history = node_info.get("history", [])
        
        # 检查是否可用
        is_usable = True
        reason = ""
        
        # 1. alive 为 False，说明是 Error 状态
        if not alive:
            is_usable = False
            reason = "alive=False"
        
        # 2. 检查最近的延迟记录，delay=0 表示超时或连接失败
        elif history:
            last_record = history[-1]
            delay = last_record.get("delay", 0)
            if delay == 0:
                is_usable = False
                reason = f"delay=0 (Timeout)"
            elif delay < LATENCY_MIN_THRESHOLD_MS:
                is_usable = False
                reason = f"delay={delay}ms < {LATENCY_MIN_THRESHOLD_MS}ms (太低，可能是假节点)"
            elif delay > LATENCY_MAX_THRESHOLD_MS:
                is_usable = False
                reason = f"delay={delay}ms > {LATENCY_MAX_THRESHOLD_MS}ms"
        
        if is_usable:
            filtered_candidates.append(node_name)
        else:
            log(f"[{now()}] AUTO_SWITCH: 跳过节点：{node_name} ({reason})")
    
    # 按延迟从小到大排序
    def get_node_delay(node_name):
        node_info = proxies_data.get(node_name, {})
        history = node_info.get("history", [])
        if history:
            return history[-1].get("delay", 99999)
        return 99999
    
    filtered_candidates.sort(key=get_node_delay)
    
    # 当前节点放最后，避免异常后又切回自己
    filtered_candidates = [
        name for name in filtered_candidates
        if name != now_node
    ] + [
        name for name in filtered_candidates
        if name == now_node
    ]

    return filtered_candidates


def clash_switch_node(node_name):
    """切换代理组节点"""
    encoded_group = urllib.parse.quote(PROXY_GROUP, safe="")
    url = f"{CLASH_API}/proxies/{encoded_group}"

    r = requests.put(
        url,
        headers={
            **clash_headers(),
            "Content-Type": "application/json",
        },
        json={"name": node_name},
        timeout=10,
    )
    r.raise_for_status()
    return True


def clash_switch_us_node(node_name):
    """切换美国自动选择分组内的具体节点"""
    us_group_name = "🇺🇸 美国自动选择"
    encoded_group = urllib.parse.quote(us_group_name, safe="")
    url = f"{CLASH_API}/proxies/{encoded_group}"

    r = requests.put(
        url,
        headers={
            **clash_headers(),
            "Content-Type": "application/json",
        },
        json={"name": node_name},
        timeout=10,
    )
    r.raise_for_status()
    return True
