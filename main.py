"""Clash Geo Watch 主入口"""

import time
from datetime import datetime

from modules import (
    CONFIG_FILE,
    PROXY_URL,
    EXPECTED_COUNTRY,
    INTERVAL_SECONDS,
    BAD_THRESHOLD,
    ABNORMAL_CHECK_INTERVAL_SECONDS,
    SCHEDULE_ENABLED,
    SCHEDULE_START_HOUR,
    SCHEDULE_END_HOUR,
    CLASH_API,
    PROXY_GROUP,
    AUTO_SWITCH,
    AUTO_SWITCH_STARTUP_CHECK,
    AUTO_SWITCH_MAX_ATTEMPTS,
    AUTO_SWITCH_INTERVAL_SECONDS,
    LATENCY_MIN_THRESHOLD_MS,
    LATENCY_MAX_THRESHOLD_MS,
    TARGET_NODE_KEYWORDS,
    CRITICAL_SERVICE_TARGETS,
    MIN_CRITICAL_SERVICE_OK,
    SERVICE_TEST_TIMEOUT,
    now,
    log,
    macos_notify,
    macos_alert,
    check_once,
    check_services,
    clash_current_node,
    clash_current_node_info,
    auto_switch_to_good_us_node,
    log_node_info,
)


def is_in_schedule():
    """检查当前时间是否在检测时间范围内"""
    if not SCHEDULE_ENABLED:
        return True
    
    current_hour = datetime.now().hour
    return SCHEDULE_START_HOUR <= current_hour < SCHEDULE_END_HOUR


def get_next_schedule_wait_seconds():
    """获取到下一个检测时间段的等待秒数"""
    current = datetime.now()
    current_hour = current.hour
    
    # 如果在检测时间范围内，返回 0
    if SCHEDULE_START_HOUR <= current_hour < SCHEDULE_END_HOUR:
        return 0
    
    if current_hour < SCHEDULE_START_HOUR:
        # 还没到开始时间，等到今天开始时间
        target = current.replace(hour=SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0)
    else:
        # 已过结束时间，等到明天开始时间
        target = current.replace(hour=SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0)
        target = target.replace(day=target.day + 1)
    
    wait_seconds = int((target - current).total_seconds())
    
    # 最小等待 60 秒，避免循环过快
    return max(wait_seconds, 60)


def main():
    """主函数"""
    bad_count = 0
    switch_attempts = 0

    log(f"{'='*60}")
    log(f"[{now()}] 🚀 Clash Geo Watch 启动")
    log(f"{'='*60}")
    log(f"📁 配置文件: {CONFIG_FILE}")
    log(f"")
    log(f"📡 代理配置:")
    log(f"   • 代理地址: {PROXY_URL}")
    log(f"   • 目标国家: {EXPECTED_COUNTRY}")
    log(f"   • 正常检测间隔: {INTERVAL_SECONDS}秒")
    log(f"   • 异常阈值: {BAD_THRESHOLD}次")
    log(f"   • 异常检测间隔: {ABNORMAL_CHECK_INTERVAL_SECONDS}秒")
    log(f"")
    log(f"⏰ 检测时间:")
    log(f"   • 启用: {'✅ 是' if SCHEDULE_ENABLED else '❌ 否'}")
    if SCHEDULE_ENABLED:
        log(f"   • 时间范围: {SCHEDULE_START_HOUR}:00 - {SCHEDULE_END_HOUR}:00")
    log(f"")
    log(f"🔌 Clash API:")
    log(f"   • API 地址: {CLASH_API}")
    log(f"   • 代理组: {PROXY_GROUP}")
    log(f"   • 自动切换: {'✅ 启用' if AUTO_SWITCH else '❌ 禁用'}")
    log(f"")
    log(f"🔄 自动切换:")
    log(f"   • 启动检查: {'✅ 启用' if AUTO_SWITCH_STARTUP_CHECK else '❌ 禁用'}")
    log(f"   • 最大尝试次数: {AUTO_SWITCH_MAX_ATTEMPTS}")
    log(f"   • 切换间隔: {AUTO_SWITCH_INTERVAL_SECONDS}秒")
    log(f"")
    log(f"🔍 节点过滤:")
    log(f"   • 目标节点关键词: {len(TARGET_NODE_KEYWORDS)}个")
    log(f"")
    log(f"🌐 服务检测:")
    log(f"   • 检测服务数: {len(CRITICAL_SERVICE_TARGETS)}")
    log(f"   • 最少可达数: {MIN_CRITICAL_SERVICE_OK}")
    log(f"   • 超时时间: {SERVICE_TEST_TIMEOUT}秒")
    log(f"{'='*60}")
    log("")
    
    # 启动标记（用于第一次检测时记录节点信息）
    is_first_check = True

    while True:
        try:
            # 检查是否在检测时间范围内
            if not is_in_schedule():
                wait_seconds = get_next_schedule_wait_seconds()
                log(f"[{now()}] ⏰ 当前不在检测时间范围内 ({SCHEDULE_START_HOUR}:00-{SCHEDULE_END_HOUR}:00)")
                log(f"[{now()}] ⏰ 等待 {wait_seconds} 秒后开始检测...")
                time.sleep(wait_seconds)
                continue
            ok, good_votes, bad_votes, results = check_once()
            service_ok_count, service_results = check_services()
            
            # 启动时检查
            if is_first_check:
                is_first_check = False
                startup_node_info = clash_current_node_info()
                startup_node_name = startup_node_info.get("name", "N/A")
                startup_node_latency = startup_node_info.get("latency_ms", 0)
                startup_node_group = startup_node_info.get("group")
                
                if AUTO_SWITCH_STARTUP_CHECK:
                    # 开启：直接筛选符合要求的节点并主动切换
                    log(f"[{now()}] 🔍 启动检查: 主动筛选合格节点...")
                    switched = auto_switch_to_good_us_node()
                    
                    if switched:
                        log(f"[{now()}] ✅ 启动检查: 已切换到合格节点")
                        # 重新获取节点信息
                        startup_node_info = clash_current_node_info()
                        startup_node_name = startup_node_info.get("name", "N/A")
                        startup_node_latency = startup_node_info.get("latency_ms", 0)
                        startup_node_group = startup_node_info.get("group")
                        # 重新检测
                        ok, good_votes, bad_votes, results = check_once()
                        service_ok_count, service_results = check_services()
                    else:
                        log(f"[{now()}] ⚠️ 启动检查: 未找到合格节点，使用当前节点")
                else:
                    # 关闭：按原逻辑检查当前节点情况
                    is_node_ok = ok and service_ok_count >= MIN_CRITICAL_SERVICE_OK and LATENCY_MIN_THRESHOLD_MS <= startup_node_latency <= LATENCY_MAX_THRESHOLD_MS
                    
                    if is_node_ok:
                        log(f"[{now()}] ✅ 启动检查: 当前节点合格")
                    else:
                        log(f"[{now()}] ⚠️ 启动检查: 当前节点不合格")
                        if not ok:
                            log(f"[{now()}]    ❌ GeoIP 不符合要求 (期望: {EXPECTED_COUNTRY})")
                        if service_ok_count < MIN_CRITICAL_SERVICE_OK:
                            log(f"[{now()}]    ❌ 服务可达性不足 ({service_ok_count}/{MIN_CRITICAL_SERVICE_OK})")
                        if startup_node_latency < LATENCY_MIN_THRESHOLD_MS and startup_node_latency > 0:
                            log(f"[{now()}]    ❌ 延迟太低 ({startup_node_latency}ms < {LATENCY_MIN_THRESHOLD_MS}ms，可能是假节点)")
                        if startup_node_latency > LATENCY_MAX_THRESHOLD_MS:
                            log(f"[{now()}]    ❌ 延迟超阈值 ({startup_node_latency}ms > {LATENCY_MAX_THRESHOLD_MS}ms)")
                
                # 记录节点信息
                log_node_info(
                    startup_node_name,
                    startup_node_latency,
                    geo_results=results,
                    service_results=service_results,
                    group=startup_node_group,
                    trigger="startup"
                )
                log("")

            if ok:
                bad_count = 0
                switch_attempts = 0
                status = "OK"
            else:
                bad_count += 1
                status = "BAD" if bad_count >= BAD_THRESHOLD else "SUSPECT"

            # 格式化输出
            status_icon = "✅" if status == "OK" else "⚠️" if status == "SUSPECT" else "❌"
            
            # 获取当前节点信息
            node_info = clash_current_node_info()
            node_name = node_info.get("name", "N/A")
            node_group = node_info.get("group")
            node_latency = node_info.get("latency_ms", 0)
            node_alive = node_info.get("alive", True)
            
            # 节点延迟状态
            if not node_alive:
                latency_icon = "❌"
                latency_color = ""
                latency_status = "Error"
            elif node_latency == 0:
                latency_icon = "❌"
                latency_color = ""
                latency_status = "Timeout"
            elif node_latency < LATENCY_MIN_THRESHOLD_MS:
                latency_icon = "⚠️"
                latency_color = ""
                latency_status = f"{node_latency}ms (<{LATENCY_MIN_THRESHOLD_MS}ms，可能是假节点)"
            elif node_latency > LATENCY_MAX_THRESHOLD_MS:
                latency_icon = "⚠️"
                latency_color = ""
                latency_status = f"{node_latency}ms (>{LATENCY_MAX_THRESHOLD_MS}ms)"
            else:
                # 颜色标识：绿色 <200ms，蓝色 <400ms，橙色 >=400ms
                if node_latency < 200:
                    latency_color = "🟢"
                elif node_latency < 400:
                    latency_color = "🔵"
                else:
                    latency_color = "🟠"
                latency_icon = "✅"
                latency_status = f"{node_latency}ms"
            
            log("")
            log(f"{'='*60}")
            log(f"[{now()}] {status_icon} 状态: {status} (连续异常: {bad_count}/{BAD_THRESHOLD})")
            log(f"{'='*60}")
            if node_group:
                log(f"🏷️  当前节点: {node_name}")
                log(f"   分组: {node_group}")
            else:
                log(f"🏷️  当前节点: {node_name}")
            log(f"   延迟: {latency_color} {latency_icon} {latency_status} (阈值: {LATENCY_MIN_THRESHOLD_MS}-{LATENCY_MAX_THRESHOLD_MS}ms)")
            
            # 检查是否需要因延迟异常而切换
            switched_by_latency = False
            need_switch = False
            switch_reason = ""
            
            if node_latency < LATENCY_MIN_THRESHOLD_MS and node_latency > 0:
                need_switch = True
                switch_reason = f"延迟 {node_latency}ms 低于最小阈值 {LATENCY_MIN_THRESHOLD_MS}ms（可能是假节点）"
            elif node_latency > LATENCY_MAX_THRESHOLD_MS:
                need_switch = True
                switch_reason = f"延迟 {node_latency}ms 超过最大阈值 {LATENCY_MAX_THRESHOLD_MS}ms"
            
            if need_switch and AUTO_SWITCH:
                log(f"[{now()}] ⚠️ {switch_reason}，触发自动切换...")
                switched = auto_switch_to_good_us_node()
                if switched:
                    log(f"[{now()}] ✅ 因延迟异常，自动切换成功")
                    bad_count = 0
                    switched_by_latency = True
                    # 获取切换后的节点信息
                    node_info = clash_current_node_info()
                    node_name = node_info.get("name", "N/A")
                    node_group = node_info.get("group")
                    node_latency = node_info.get("latency_ms", 0)
                    latency_icon = "✅" if LATENCY_MIN_THRESHOLD_MS <= node_latency <= LATENCY_MAX_THRESHOLD_MS else "⚠️"
                    latency_status = f"{node_latency}ms"
                    log(f"{'='*60}")
                    log(f"🏷️  切换后节点: {node_name}")
                    if node_group:
                        log(f"   分组: {node_group}")
                    log(f"   延迟: {latency_icon} {latency_status} (阈值: {LATENCY_MAX_THRESHOLD_MS}ms)")
                    
                    # 记录切换后的节点信息（复用当前检测结果）
                    log_node_info(
                        node_name,
                        node_latency,
                        geo_results=results,
                        service_results=service_results,
                        group=node_group,
                        trigger="switch"
                    )
                else:
                    log(f"[{now()}] ❌ 因延迟超阈值，自动切换失败")
            
            log(f"{'='*60}")
            
            # GeoIP 检测结果（使用切换时的检测结果）
            log(f"📍 GeoIP 检测 (期望: {EXPECTED_COUNTRY})")
            log(f"   投票: ✅ {good_votes} / ❌ {bad_votes}")
            for r in results:
                if "error" in r:
                    log(f"   • {r.get('source', 'unknown')}: ❌ {r.get('error', '')[:50]}...")
                else:
                    country = r.get("country", "N/A")
                    ip = r.get("ip", "N/A")
                    icon = "✅" if country == EXPECTED_COUNTRY else "❌"
                    log(f"   • {r.get('source', 'unknown')}: {icon} {country} ({ip})")
            
            # 服务可达性检测结果（使用切换时的检测结果）
            log(f"🌐 服务可达性 (要求: ≥{MIN_CRITICAL_SERVICE_OK})")
            log(f"   可达: {service_ok_count}/{len(CRITICAL_SERVICE_TARGETS)}")
            for r in service_results:
                icon = "✅" if r.get("ok") else "❌"
                name = r.get("name", "unknown")
                status_code = r.get("status_code", "N/A")
                latency = r.get("latency_ms", "N/A")
                error = r.get("error", "")
                
                # 延迟颜色标识
                if latency == "N/A":
                    latency_color = ""
                elif latency < 200:
                    latency_color = "🟢"
                elif latency < 400:
                    latency_color = "🔵"
                else:
                    latency_color = "🟠"
                
                if error:
                    log(f"   • {icon} {name}: {error[:40]}...")
                else:
                    log(f"   • {icon} {name}: {status_code} {latency_color} ({latency}ms)")
            
            log(f"{'='*60}")
            log("")
            
            # 如果因延迟切换成功，跳过后续异常处理
            if switched_by_latency:
                time.sleep(INTERVAL_SECONDS)
                continue

            # 异常处理逻辑
            if status == "BAD":
                current_node = None
                try:
                    current_node = clash_current_node()
                except Exception as e:
                    current_node = f"读取失败：{e}"

                log(f"[{now()}] ❌ 检测到异常，当前节点：{current_node}")

                # 达到阈值，开始自动切换
                if AUTO_SWITCH:
                    switch_attempts += 1
                    log(f"[{now()}] 🔄 开始自动切换 (尝试 {switch_attempts}/{AUTO_SWITCH_MAX_ATTEMPTS})...")
                    
                    switched = auto_switch_to_good_us_node()

                    if switched:
                        log(f"[{now()}] ✅ 自动切换成功")
                        bad_count = 0
                        switch_attempts = 0
                    else:
                        log(f"[{now()}] ❌ 自动切换失败")
                        
                        # 达到最大切换次数，触发提醒
                        if switch_attempts >= AUTO_SWITCH_MAX_ATTEMPTS:
                            log(f"[{now()}] ⚠️ 已尝试 {switch_attempts} 次自动切换，均失败！")
                            macos_alert(
                                "Clash 节点异常",
                                f"已尝试 {switch_attempts} 次自动切换，均失败！\n请手动切换美国节点。"
                            )
                            # 重置计数，回到正常检测间隔
                            bad_count = 0
                            switch_attempts = 0
                        else:
                            # 未达到最大次数，等待后继续尝试
                            log(f"[{now()}] ⏳ {AUTO_SWITCH_INTERVAL_SECONDS}秒后再次尝试...")
                            time.sleep(AUTO_SWITCH_INTERVAL_SECONDS)
                            continue
                else:
                    # 未启用自动切换，直接提醒
                    macos_alert(
                        "Clash 节点异常",
                        f"检测到出口地区异常，请手动切换美国节点。"
                    )
                    bad_count = 0

        except KeyboardInterrupt:
            log(f"[{now()}] STOP watcher")
            break
        except Exception as e:
            log(f"[{now()}] ERROR: {e}")

        # 根据状态决定检测间隔
        if bad_count > 0 and bad_count < BAD_THRESHOLD:
            # 异常但未达到阈值：异常检测间隔
            log(f"[{now()}] 异常状态，{ABNORMAL_CHECK_INTERVAL_SECONDS}秒后再次检测...")
            time.sleep(ABNORMAL_CHECK_INTERVAL_SECONDS)
        else:
            # 正常或已处理：正常检测间隔
            time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
