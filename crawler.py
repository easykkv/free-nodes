#!/usr/bin/env python3
"""
免费节点爬虫 - 从公开源抓取代理节点
"""
import re
import base64
import requests
import os
from datetime import datetime

# ========== 配置区 ==========
SOURCES = [
   # === GitHub 订阅源 ===
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/base64",
    "https://raw.githubusercontent.com/MhdiTaheri/free-v2ray-collector/main/collector/output/base64",
    
    # === 直接订阅链接 ===
    "https://sub.445569.xyz",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    
    # === 其他活跃源 ===
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/alanbobs999/TopFreeProxies/master/Eternity",
]

OUTPUT_FILE = "index.html"
RAW_FILE = "nodes.txt"


def fetch_text(url):
    """从 URL 获取文本内容"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print("[ERROR] 抓取失败 %s: %s" % (url, e))
        return ""


def extract_nodes(text):
    """从文本中提取所有节点链接"""
    pattern = r'(?:vless|trojan|ss|vmess)://[^\s<>"\']+'
    return re.findall(pattern, text)


def try_decode_base64(text):
    """尝试 Base64 解码"""
    try:
        cleaned = text.replace('-', '+').replace('_', '/')
        padding = 4 - len(cleaned) % 4
        if padding != 4:
            cleaned += '=' * padding
        return base64.b64decode(cleaned).decode('utf-8', errors='ignore')
    except:
        return text


def crawl():
    """主爬取函数"""
    all_nodes = []
    print("[INFO] 开始爬取，共 %d 个数据源" % len(SOURCES))
    
    for source in SOURCES:
        print("[INFO] 正在抓取: %s" % source)
        text = fetch_text(source)
        if not text:
            continue
        decoded_text = try_decode_base64(text)
        nodes = extract_nodes(decoded_text)
        print("[INFO] 从该源提取到 %d 个节点" % len(nodes))
        all_nodes.extend(nodes)
    
    print("[INFO] 爬取完成，共获取 %d 个节点" % len(all_nodes))
    
    before = len(all_nodes)
    all_nodes = list(set(all_nodes))
    print("[INFO] 去重后剩余 %d 个节点" % len(all_nodes))
    
    return all_nodes


def render_section(title, node_list, css_class, tag_class):
    """渲染节点分类区块"""
    if not node_list:
        return ""
    items = ""
    for node in node_list:
        items += '<div class="node-item %s"><span class="tag %s">%s</span>%s</div>\n' % (css_class, tag_class, title, node)
    
    return '''
        <div class="section">
            <h2>%s (%d)</h2>
            <div class="node-list">
%s
            </div>
        </div>''' % (title, len(node_list), items)


def generate_page(nodes, sub_url="", base64_url=""):
    """生成订阅页面"""
    raw_text = "\n".join(nodes)
    encoded = base64.b64encode(raw_text.encode()).decode()
    
    vless_nodes = [n for n in nodes if n.startswith('vless://')]
    trojan_nodes = [n for n in nodes if n.startswith('trojan://')]
    ss_nodes = [n for n in nodes if n.startswith('ss://')]
    vmess_nodes = [n for n in nodes if n.startswith('vmess://')]
    
    sections = ""
    sections += render_section("VLESS 节点", vless_nodes, "vless", "tag-vless")
    sections += render_section("Trojan 节点", trojan_nodes, "trojan", "tag-trojan")
    sections += render_section("Shadowsocks 节点", ss_nodes, "ss", "tag-ss")
    sections += render_section("VMess 节点", vmess_nodes, "vmess", "tag-vmess")
    
    # 使用 %s 格式化，避免 CSS 大括号冲突
    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>免费节点订阅</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0a0a0a; color: #e0e0e0; line-height: 1.6; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #00d4ff; margin-bottom: 10px; font-size: 24px; }
        .stats { background: #1a1a1a; border-radius: 8px; padding: 15px; margin-bottom: 20px; display: flex; gap: 20px; flex-wrap: wrap; }
        .stat-item { text-align: center; }
        .stat-num { font-size: 28px; font-weight: bold; color: #00d4ff; }
        .stat-label { font-size: 12px; color: #888; }
        .section { background: #1a1a1a; border-radius: 8px; padding: 20px; margin-bottom: 15px; }
        .section h2 { color: #fff; margin-bottom: 10px; font-size: 16px; }
        .subscribe-box { display: flex; gap: 10px; margin-bottom: 15px; }
        .subscribe-box input { flex: 1; background: #0a0a0a; border: 1px solid #333; color: #00d4ff; padding: 10px 15px; border-radius: 6px; font-family: monospace; font-size: 13px; }
        .subscribe-box button { background: #00d4ff; color: #000; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; }
        .subscribe-box button:hover { background: #00b8e6; }
        .node-list { max-height: 400px; overflow-y: auto; background: #0a0a0a; border-radius: 6px; padding: 10px; }
        .node-item { font-family: monospace; font-size: 11px; padding: 8px; border-bottom: 1px solid #1a1a1a; word-break: break-all; color: #aaa; }
        .node-item:last-child { border-bottom: none; }
        .node-item.vless { border-left: 3px solid #00d4ff; }
        .node-item.trojan { border-left: 3px solid #ff6b6b; }
        .node-item.ss { border-left: 3px solid #51cf66; }
        .node-item.vmess { border-left: 3px solid #ffd43b; }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; margin-right: 5px; font-weight: bold; }
        .tag-vless { background: #00d4ff20; color: #00d4ff; }
        .tag-trojan { background: #ff6b6b20; color: #ff6b6b; }
        .tag-ss { background: #51cf6620; color: #51cf66; }
        .tag-vmess { background: #ffd43b20; color: #ffd43b; }
        .update-time { color: #666; font-size: 12px; margin-top: 20px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 免费节点订阅</h1>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-num">%d</div>
                <div class="stat-label">总节点数</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">%d</div>
                <div class="stat-label">VLESS</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">%d</div>
                <div class="stat-label">Trojan</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">%d</div>
                <div class="stat-label">Shadowsocks</div>
            </div>
            <div class="stat-item">
                <div class="stat-num">%d</div>
                <div class="stat-label">VMess</div>
            </div>
        </div>

        <div class="section">
            <h2>📋 订阅链接</h2>
            <div class="subscribe-box">
                <input type="text" id="subUrl" value="%s" readonly>
                <button onclick="copySub()">复制链接</button>
            </div>
            <div class="subscribe-box">
                <input type="text" id="base64Url" value="%s" readonly>
                <button onclick="copyBase64()">复制 Base64</button>
            </div>
        </div>

        %s

        <p class="update-time">最后更新：%s (UTC)</p>
    </div>

    <script>
        function copySub() {
            var url = document.getElementById('subUrl').value;
            navigator.clipboard.writeText(url).then(function() { alert('已复制订阅链接'); });
        }
        function copyBase64() {
            var url = document.getElementById('base64Url').value;
            navigator.clipboard.writeText(url).then(function() { alert('已复制 Base64 内容'); });
        }
    </script>
</body>
</html>''' % (
        len(nodes),
        len(vless_nodes),
        len(trojan_nodes),
        len(ss_nodes),
        len(vmess_nodes),
        sub_url,
        base64_url,
        sections,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    return html, raw_text, encoded


def main():
    print("=" * 50)
    print("  免费节点订阅生成器")
    print("=" * 50)
    
    sub_url = os.environ.get('SUB_URL', '')
    base64_url = os.environ.get('BASE64_URL', '')
    
    nodes = crawl()
    
    if not nodes:
        print("[WARN] 未获取到任何节点")
        nodes = ["# 暂无节点，请稍后再来"]
    
    html, raw_text, encoded = generate_page(nodes, sub_url, base64_url)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print("[OK] 已生成页面: %s" % OUTPUT_FILE)
    
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        f.write(raw_text)
    print("[OK] 已生成原始节点文件: %s" % RAW_FILE)
    
    with open("nodes_base64.txt", "w", encoding="utf-8") as f:
        f.write(encoded)
    print("[OK] 已生成 Base64 编码文件: nodes_base64.txt")
    
    print("[OK] 全部完成！共 %d 个节点" % len(nodes))


if __name__ == "__main__":
    main()
