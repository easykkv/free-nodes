#!/usr/bin/env python3
"""
免费节点爬虫 - 从公开源抓取代理节点
"""
import re
import base64
import json
import socket
import requests
from datetime import datetime

# ========== 配置区 ==========
# 数据源列表（URL 或本地文件路径）
SOURCES = [
    # 示例：从其他订阅站抓取（这些是示例 URL，请替换为实际可用的源）
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    
    # 也可以添加网页 URL，脚本会自动提取其中的节点链接
    # "https://example.com/nodes",
]

# 输出文件
OUTPUT_FILE = "index.html"
RAW_FILE = "nodes.txt"

# 节点验证（是否检测端口连通性，True/False）
VERIFY_NODES = False
VERIFY_TIMEOUT = 5  # 秒

# 节点去重
DEDUPLICATE = True

# User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_text(url):
    """从 URL 获取文本内容"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[ERROR] 抓取失败 {url}: {e}")
        return ""


def extract_nodes(text):
    """从文本中提取所有节点链接"""
    # 匹配 vless:// trojan:// ss:// vmess:// 开头的链接
    pattern = r'(?:vless|trojan|ss|vmess)://[^\s<>"\']+'
    nodes = re.findall(pattern, text)
    return nodes


def try_decode_base64(text):
    """尝试 Base64 解码（很多订阅内容是编码的）"""
    try:
        # 清理可能的 URL 安全字符
        cleaned = text.replace('-', '+').replace('_', '/')
        # 补齐 padding
        padding = 4 - len(cleaned) % 4
        if padding != 4:
            cleaned += '=' * padding
        decoded = base64.b64decode(cleaned).decode('utf-8', errors='ignore')
        return decoded
    except:
        return text


def parse_node_info(node_str):
    """解析节点信息，提取 host 和 port（用于验证）"""
    try:
        if node_str.startswith('vless://') or node_str.startswith('trojan://'):
            # vless://uuid@host:port?...
            match = re.search(r'@([^:]+):(\d+)', node_str)
            if match:
                return match.group(1), int(match.group(2))
    except:
        pass
    return None, None


def verify_node(host, port):
    """验证节点端口是否连通"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(VERIFY_TIMEOUT)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def crawl():
    """主爬取函数"""
    all_nodes = []
    
    print(f"[INFO] 开始爬取，共 {len(SOURCES)} 个数据源")
    
    for source in SOURCES:
        print(f"[INFO] 正在抓取: {source}")
        text = fetch_text(source)
        if not text:
            continue
        
        # 尝试解码（如果是 Base64 编码的）
        decoded_text = try_decode_base64(text)
        
        # 提取节点
        nodes = extract_nodes(decoded_text)
        print(f"[INFO] 从该源提取到 {len(nodes)} 个节点")
        all_nodes.extend(nodes)
    
    print(f"[INFO] 爬取完成，共获取 {len(all_nodes)} 个节点")
    
    # 去重
    if DEDUPLICATE:
        before = len(all_nodes)
        all_nodes = list(set(all_nodes))
        print(f"[INFO] 去重后剩余 {len(all_nodes)} 个节点（移除 {before - len(all_nodes)} 个重复）")
    
    # 验证节点可用性
    if VERIFY_NODES:
        print("[INFO] 开始验证节点可用性...")
        valid_nodes = []
        for node in all_nodes:
            host, port = parse_node_info(node)
            if host and port:
                if verify_node(host, port):
                    valid_nodes.append(node)
                    print(f"  [OK] {host}:{port}")
                else:
                    print(f"  [FAIL] {host}:{port}")
            else:
                valid_nodes.append(node)  # 无法解析的节点保留
        all_nodes = valid_nodes
        print(f"[INFO] 验证完成，可用节点 {len(all_nodes)} 个")
    
    return all_nodes


def generate_html(nodes):
    """生成订阅页面"""
    # 原始文本
    raw_text = "\n".join(nodes)
    
    # Base64 编码（供客户端订阅使用）
    encoded = base64.b64encode(raw_text.encode()).decode()
    
    # 按类型分类
    vless_nodes = [n for n in nodes if n.startswith('vless://')]
    trojan_nodes = [n for n in nodes if n.startswith('trojan://')]
    ss_nodes = [n for n in nodes if n.startswith('ss://')]
    vmess_nodes = [n for n in nodes if n.startswith('vmess://')]
    other_nodes = [n for n in nodes if not any(
        n.startswith(p) for p in ['vless://', 'trojan://', 'ss://', 'vmess://']
    )]
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>免费节点订阅</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #0a0a0a; color: #e0e0e0; line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #00d4ff; margin-bottom: 10px; font-size: 24px; }}
        .stats {{ 
            background: #1a1a1a; border-radius: 8px; padding: 15px;
            margin-bottom: 20px; display: flex; gap: 20px; flex-wrap: wrap;
        }}
        .stat-item {{ text-align: center; }}
        .stat-num {{ font-size: 28px; font-weight: bold; color: #00d4ff; }}
        .stat-label {{ font-size: 12px; color: #888; }}
        .section {{
            background: #1a1a1a; border-radius: 8px; padding: 20px;
            margin-bottom: 15px;
        }}
        .section h2 {{ color: #fff; margin-bottom: 10px; font-size: 16px; }}
        .subscribe-box {{
            display: flex; gap: 10px; margin-bottom: 15px;
        }}
        .subscribe-box input {{
            flex: 1; background: #0a0a0a; border: 1px solid #333;
            color: #00d4ff; padding: 10px 15px; border-radius: 6px;
            font-family: monospace; font-size: 13px;
        }}
        .subscribe-box button {{
            background: #00d4ff; color: #000; border: none;
            padding: 10px 20px; border-radius: 6px; cursor: pointer;
            font-weight: bold;
        }}
        .subscribe-box button:hover {{ background: #00b8e6; }}
        .node-list {{
            max-height: 400px; overflow-y: auto;
            background: #0a0a0a; border-radius: 6px; padding: 10px;
        }}
        .node-item {{
            font-family: monospace; font-size: 11px; padding: 8px;
            border-bottom: 1px solid #1a1a1a; word-break: break-all;
            color: #aaa;
        }}
        .node-item:last-child {{ border-bottom: none; }}
        .node-item.vless {{ border-left: 3px solid #00d4ff; }}
        .node-item.trojan {{ border-left: 3px solid #ff6b6b; }}
        .node-item.ss {{ border-left: 3px solid #51cf66; }}
        .node-item.vmess {{ border-left: 3px solid #ffd43b; }}
        .tag {{
            display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 10px; margin-right: 5px; font-weight: bold;
        }}
        .tag-vless {{ background: #00d4ff20; color: #00d4ff; }}
        .tag-trojan {{ background: #ff6b6b20; color: #ff6b6b; }}
        .tag-ss {{ background: #51cf6620; color: #51cf66; }}
        .tag-vmess {{ background: #ffd43b20; color: #ffd43b; }}
        .update-time {{ color: #666; font-size: 12px; margin-top: 20px; text-align: center; }}
        .clients {{ display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }}
        .client-tag {{
            background: #1a1a1a; padding: 5px 12px; border-radius: 20px;
            font-size: 12px; color: #888; border: 1px solid #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 免费节点订阅</h1>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-num">{len(nodes)}</div>
                <div class="stat-label">总节点数</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">{len(vless_nodes)}</div>
                <div class="stat-label">VLESS</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">{len(trojan_nodes)}</div>
                <div class="stat-label">Trojan</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">{len(ss_nodes)}</div>
                <div class="stat-label">Shadowsocks</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">{len(vmess_nodes)}</div>
                <div class="stat-label">VMess</div>
            </div>
        </div>

        <div class="section">
            <h2>📋 订阅链接</h2>
            <div class="clients">
                <span class="client-tag">V2RayN</span>
                <span class="client-tag">Clash</span>
                <span class="client-tag">Shadowrocket</span>
                <span class="client-tag">NekoBox</span>
            </div>
            <div class="subscribe-box">
                <input type="text" id="subUrl" value="SUB_URL_PLACEHOLDER" readonly>
                <button onclick="copySub()">复制链接</button>
            </div>
            <div class="subscribe-box">
                <input type="text" id="base64Url" value="BASE64_URL_PLACEHOLDER" readonly>
                <button onclick="copyBase64()">复制 Base64</button>
            </div>
        </div>
"""

    # 按类型展示节点
    def render_node_section(title, node_list, css_class, tag_class):
        if not node_list:
            return ""
        items = ""
        for node in node_list:
            items += f'            <div class="node-item {css_class}"><span class="tag {tag_class}">{title}</span>{node}</div>\n'
        return f"""
        <div class="section">
            <h2>{title} ({len(node_list)})</h2>
            <div class="node-list">
{items}            </div>
        </div>"""

    html += render_node_section("VLESS 节点", vless_nodes, "vless", "tag-vless")
    html += render_node_section("Trojan 节点", trojan_nodes, "trojan", "tag-trojan")
    html += render_node_section("Shadowsocks 节点", ss_nodes, "ss", "tag-ss")
    html += render_node_section("VMess 节点", vmess_nodes, "vmess", "tag-vmess")

    html += f"""
        <p class="update-time">最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC)</p>
    </div>

    <script>
        function copySub() {{
            var url = document.getElementById('subUrl').value;
            navigator.clipboard.writeText(url).then(() => alert('已复制订阅链接'));
        }}
        function copyBase64() {{
            var url = document.getElementById('base64Url').value;
            navigator.clipboard.writeText(url).then(() => alert('已复制 Base64 内容'));
        }}
    </script>
</body>
</html>"""
    
    return html, raw_text, encoded


def main():
    print("=" * 50)
    print("  免费节点订阅生成器")
    print("=" * 50)
    
    # 爬取节点
    nodes = crawl()
    
    if not nodes:
        print("[WARN] 未获取到任何节点，请检查数据源是否可用")
        # 生成空页面
        nodes = ["# 暂无节点，请稍后再来"]
    
    # 生成页面
    html, raw_text, encoded = generate_html(nodes)
    
    # 写入文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] 已生成页面: {OUTPUT_FILE}")
    
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        f.write(raw_text)
    print(f"[OK] 已生成原始节点文件: {RAW_FILE}")
    
    # 同时保存 Base64 版本
    with open("nodes_base64.txt", "w", encoding="utf-8") as f:
        f.write(encoded)
    print(f"[OK] 已生成 Base64 编码文件: nodes_base64.txt")
    
    print(f"[OK] 全部完成！共 {len(nodes)} 个节点")


if __name__ == "__main__":
    main()
