# -*- coding: UTF-8 -*-
"""
AIWriteX 一键文章生成+发布脚本

用法:
  python3 gen_article.py              # 生成+封面+发布 全流程
  python3 gen_article.py --articles   # 仅写文章HTML到本地
  python3 gen_article.py --covers    # 仅生成封面图
  python3 gen_article.py --publish   # 仅发布已有文章到微信草稿
  python3 gen_article.py --list      # 列出待发布的文章配置

配置方式:
  直接修改下方 ARTICLES 列表，每篇文章包含:
    - title:    文章标题（建议≤28个字符，微信搜索友好）
    - digest:   摘要（建议≤45个字符）
    - keywords: 英文关键词（用于生成封面图）
    - tag:      左上角标签（如"突发""行业数据"等）
    - content:  正文HTML片段（支持<p><h2><div><strong><span>等标签）

  每次清空旧文章的ARTICLES列表，填入新文章，运行即可。
"""

import hashlib
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime

# ============================================================
#   📌 文章配置区 —— 修改这里即可
# ============================================================

ARTICLES = [
    {
        "title": "DeepSeek R2推理模型发布",
        "digest": "DeepSeek发布R2推理模型，数学和代码能力超越OpenAI o3",
        "keywords": "DeepSeek R2 reasoning model launch, neural network visualization, blue technology theme",
        "tag": "产品发布",
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">4月13日，DeepSeek正式发布R2推理模型。这是继DeepSeek V3之后最重要的产品升级，专注于长链推理、数学证明和代码生成三大场景。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:14px 0;text-indent:2em;">据官方公布的基准测试数据，DeepSeek R2在MATH-500（数学推理）中得分96.2%，超越OpenAI o3的94.7%；在HumanEval（代码生成）中得分93.8%，超越Claude 4 Opus的91.5%。API定价维持DeepSeek一贯的低价策略，输入0.1元/百万token，输出0.4元/百万token。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:14px 0;text-indent:2em;"><strong>核心能力升级：</strong></p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">1. <strong>长链推理。</strong>R2引入"思维树"架构，支持最多50步递归推理，擅长处理复杂数学证明和多步骤逻辑问题。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">2. <strong>代码能力。</strong>原生支持Python、JavaScript、Rust等12种编程语言，可一次性生成500行以上高质量代码。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">3. <strong>上下文窗口。</strong>支持256K tokens，兼顾推理深度和上下文长度。</p>
<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">市场影响</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">R2发布后，国产大模型赛道格局进一步清晰。DeepSeek凭借V3（通用）+R2（推理）的双模型策略，在性价比和性能两个维度同时领跑。阿里通义千问团队在2小时内宣布Qwen-Reasoner将在"近期内"发布。OpenAI方面暂未回应。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">截至发稿，DeepSeek R2 API已开放注册，网页版同步上线。首日访问量突破800万次。</p>
""",
    },
    {
        "title": "2026高考AI专业大学排名出炉",
        "digest": "清华北大浙大前三，AI专业录取分持续走高，6所高校新增AI本科",
        "keywords": "university ranking, AI major education, graduation ceremony, Chinese university campus",
        "tag": "教育资讯",
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">4月12日，软科发布《2026年中国大学人工智能专业排名》。清华大学连续第四年蝉联榜首，北京大学和浙江大学分列二三位。</p>
<div style="background:#fff3e0;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #ffe0b2;">
<p style="font-size:15px;color:#e65100;font-weight:700;margin:0 0 12px;">2026 AI专业排名 Top 10</p>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#c0392b;font-weight:700;">1. 清华大学</span><span style="font-size:14px;color:#333;">A+</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#e65100;font-weight:700;">2. 北京大学</span><span style="font-size:14px;color:#333;">A+</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#e65100;font-weight:700;">3. 浙江大学</span><span style="font-size:14px;color:#333;">A+</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#555;">4. 上海交通大学</span><span style="font-size:14px;color:#333;">A</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#555;">5. 南京大学</span><span style="font-size:14px;color:#333;">A</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#555;">6. 中国科学技术大学</span><span style="font-size:14px;color:#333;">A</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#555;">7. 哈尔滨工业大学</span><span style="font-size:14px;color:#333;">A</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#555;">8. 北京航空航天大学</span><span style="font-size:14px;color:#333;">A</span></div>
<div style="padding:8px 0;border-bottom:1px solid #ffe0b2;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#555;">9. 华中科技大学</span><span style="font-size:14px;color:#333;">A-</span></div>
<div style="padding:8px 0;display:flex;justify-content:space-between;"><span style="font-size:14px;color:#555;">10. 武汉大学</span><span style="font-size:14px;color:#333;">A-</span></div>
</div>
<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">录取分数持续走高</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">2025年高考，全国AI相关专业平均录取分数线较2024年上涨12分。清华AI班在多省录取线超过理科一批线120分以上。浙江大学竺可桢学院AI方向在浙江本省录取线为692分。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">2026年，教育部批准北京邮电大学、西安电子科技大学等6所高校新增AI本科专业。截至目前，全国开设AI本科专业的高校已达472所。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">就业方面，AI专业2025届本科毕业生平均起薪为1.2万元/月，研究生起薪为2.5万元/月，均位居各专业前列。</p>
""",
    },
    {
        "title": "Cursor月活突破5000万 AI编程爆发",
        "digest": "AI编程工具Cursor月活突破5000万，AI代码生成占比超40%",
        "keywords": "AI code editor Cursor, programming workspace, code on screen, dark theme developer tools",
        "tag": "行业数据",
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">4月11日，AI编程工具Cursor创始人Michael Truell在社交媒体宣布，Cursor月活跃用户突破5000万，成为全球增长最快的开发者工具。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:14px 0;text-indent:2em;">这一数字相比2025年同期的800万增长了525%。Cursor在2024年推出AI原生代码编辑器，凭借"Tab补全""Chat对话写代码""Codebase全项目理解"三大核心功能迅速走红。</p>
<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">关键数据</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">• <strong>月活用户：5000万</strong>（Vs GitHub Copilot约1500万）</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">• <strong>AI生成代码占比：42%</strong> —— 用户提交的代码中，超过四成由AI生成或建议</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">• <strong>付费转化率：18%</strong> —— 远高于SaaS行业平均的3-5%</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">• <strong>企业客户：2.3万家</strong>，包括Google、Meta在内的硅谷头部科技公司</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">• <strong>最新估值：90亿美元</strong>，2026年1月完成E轮融资</p>
<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">竞争格局</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">微软旗下GitHub Copilot目前拥有约1500万月活用户。Cursor的快速增长直接影响了Copilot的市场份额。同时，国内厂商字节跳动推出Trae、阿里推出通义灵码、百度推出Comate，都在争夺AI编程市场。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">Cursor目前支持VS Code核心插件、独立桌面版和Web版。独立桌面版基于VS Code AI fork构建，原生集成Anthropic Claude 4和OpenAI GPT-5双模型引擎。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">Cursor个人版定价20美元/月，商业版40美元/月。本周宣布对中国用户开放支付宝付款。</p>
""",
    },
    {
        "title": "AI换脸诈骗涉案金额超10亿",
        "digest": "公安部通报AI换脸诈骗案件同比增加180%，涉案金额累计超10亿",
        "keywords": "cybersecurity AI deepfake fraud alert, digital identity theft, police investigation scene, dramatic lighting",
        "tag": "警方通报",
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">4月12日，公安部刑事侦查局发布通报称，2026年第一季度全国AI换脸诈骗立案数达1.2万起，同比增加180%，涉案金额累计超过10亿元人民币。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:14px 0;text-indent:2em;">通报指出，犯罪分子利用AI换脸和AI声音克隆技术，冒充企业高管、亲友、政府官员进行视频通话诈骗。由于AI伪造的实时视频通话逼真度高，受害者往往难以辨别。</p>
<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">典型手法</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>1. 企业高管 impersonation。</strong>犯罪分子获取企业高管照片和声音后，生成逼真的视频通话画面，通过微信或Teams联系财务人员，以"紧急转账"为由实施诈骗。单笔金额最高达2800万元。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>2. 亲友冒充。</strong>通过社交媒体获取用户家人照片，生成换脸视频拨打用户电话，声称"出车祸需要手术费"等紧急情况。此类案件占总量35%。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>3. 投资诈骗。</strong>伪造知名投资人或企业家的视频直播，在直播间推荐"内部项目"，诱导观众投资。最高单案涉案金额达5000万元。</p>
<div style="background:#fef3f3;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #fdd;">
<p style="font-size:14px;color:#c0392b;font-weight:700;margin:0 0 8px;">防骗提醒</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">① 涉及转账务必电话二次核实<br>② 要求对方做指定动作（如转头、捂脸）来验证<br>③ 设置转账延迟到账（24小时）<br>④ 企业财务应建立双签制度<br>⑤ 安装国家反诈中心APP</p>
</div>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">公安部表示，已联合网信办、工信部开展为期6个月的"净网·AI"专项行动，重点打击AI换脸、声音克隆等技术滥用违法犯罪行为。</p>
""",
    },
    {
        "title": "抖音AI短视频流量扶持政策",
        "digest": "抖音宣布AI生成短视频专项流量扶持，月播放量超10万可获现金奖励",
        "keywords": "TikTok Douyin short video, AI content creation, smartphone filming, social media vibrant",
        "tag": "平台政策",
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">4月10日，抖音创作者联盟正式发布"AI创享计划"，针对使用AI工具生成的短视频内容推出专项流量扶持和变现政策。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:14px 0;text-indent:2em;">这是国内主流短视频平台首次明确为AI生成内容划定独立赛道并提供变现通道。政策自5月1日起正式实施。</p>
<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">核心政策</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>1. 流量扶持：</strong>AI生成视频将获得额外30%的初始推荐流量池。抖音算法将AI内容与人工内容分别评估，避免同质化竞争。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>2. 现金奖励：</strong>单条AI视频月播放量超10万，奖励500元；超100万，奖励5000元；超1000万，奖励5万元。每月上限10万元/创作者。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>3. MCN合作：</strong>AI内容MCN机构可获得额外20%流量加成，且享受专属商业化对接通道。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>4. 工具对接：</strong>抖音已与即梦AI（字节内部）、可灵AI（快手）等工具打通，一键发布至抖音并自动打上"AI生成"标签。</p>
<div style="background:#f0f7ff;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #d0e3ff;">
<p style="font-size:14px;color:#1a56db;font-weight:700;margin:0 0 8px;">准入规则</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• 必须声明使用AI工具生成<br>• 内容需原创或经授权<br>• 禁止生成虚假新闻、人物肖像侵权<br>• 禁止生成色情、暴力、违法内容<br>• 违规三次取消计划资格</p>
</div>
<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">行业分析</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">业内人士分析，抖音此举意在抢占AI内容生态先手。此前快手已于3月推出"AI星火计划"，B站则在测试AI生成视频专区。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">目前抖音AI生成内容日均发布量约为120万条，占平台总发布量的3.8%。预计政策实施后，这一比例将在3个月内翻倍。</p>
""",
    },
]

# ============================================================
#   ⚙️ 配置区 —— 一般不需要修改
# ============================================================

# 微信公众号配置
WECHAT_APPID = "wxbece2054a0fa5239"
WECHAT_APPSECRET = "d3784fac8a4299b4ac3498221ec3aac6"
WECHAT_AUTHOR = "AI前沿"

# 存储路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTICLE_DIR = os.path.expanduser("~/Library/Application Support/AIWriteX/output/article")
IMAGE_DIR = os.path.expanduser("~/Library/Application Support/AIWriteX/images")

# 封面图尺寸
COVER_WIDTH = 900
COVER_HEIGHT = 384

# 标签颜色映射
TAG_COLORS = {
    "突发": "#10a37f",
    "行业数据": "#e74c3c",
    "产品发布": "#007aff",
    "独家爆料": "#ff6b35",
    "薪资报告": "#8e44ad",
    "警方通报": "#e74c3c",
    "教育资讯": "#e65100",
    "平台政策": "#1a56db",
}
TAG_DEFAULT = "#333333"

# HTML 模板
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;">
<div style="max-width:677px;margin:0 auto;background:#ffffff;">
<div style="padding:30px 24px 20px;text-align:center;">
<span style="display:inline-block;background:{tag_color};color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:20px;margin-bottom:14px;">{tag}</span>
<h1 style="font-size:22px;font-weight:800;color:#1a1a1a;line-height:1.5;margin:0 0 12px;">{title}</h1>
<div style="display:flex;align-items:center;justify-content:center;gap:8px;">
<span style="font-size:12px;color:#999;">{author}</span>
<span style="color:#ddd;">·</span>
<span style="font-size:12px;color:#999;">{date}</span>
</div>
</div>
<div style="height:1px;background:linear-gradient(to right,transparent,#e0e0e0,transparent);margin:0 24px;"></div>
<div style="padding:24px;">
{content}
</div>
<div style="padding:16px 24px;text-align:center;background:#fafafa;border-top:1px solid #eee;">
<p style="font-size:12px;color:#bbb;margin:0;">— END —</p>
</div>
</div>
</body>
</html>"""


# ============================================================
#   🔧 工具函数
# ============================================================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def build_html(article):
    today = datetime.now().strftime("%Y年%m月%d日")
    tag_color = TAG_COLORS.get(article.get("tag", ""), TAG_DEFAULT)
    return HTML_TEMPLATE.format(
        title=article["title"],
        tag=article.get("tag", ""),
        tag_color=tag_color,
        author=WECHAT_AUTHOR,
        date=today,
        content=article["content"].strip(),
    )


def save_article(html, filename):
    os.makedirs(ARTICLE_DIR, exist_ok=True)
    filepath = os.path.join(ARTICLE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


def generate_cover(keyword_text, seed):
    """用 Pollinations.ai 生成封面图，返回文件路径"""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    prompt = urllib.parse.quote(
        keyword_text + ", clean digital illustration, no text, no watermark"
    )
    url = (
        f"https://image.pollinations.ai/prompt/{prompt}"
        f"?width={COVER_WIDTH}&height={COVER_HEIGHT}&seed={seed}&nologo=true"
    )
    filename = f"cover_{seed}.jpg"
    filepath = os.path.join(IMAGE_DIR, filename)

    log(f"  下载封面: {filename}...")
    result = subprocess.run(
        ["curl", "-sL", "-o", filepath, "--max-time", "180", url],
        capture_output=True, text=True
    )
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        size = os.path.getsize(filepath)
        log(f"  封面 OK: {filename} ({size // 1024}KB)")
        return filepath
    else:
        log(f"  封面 FAIL: {filename}")
        return None


def upload_cover(filepath, token, ssl_ctx):
    """上传封面图到微信，返回 media_id"""
    with open(filepath, "rb") as f:
        cover_data = f.read()

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="cover.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + cover_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    upload_url = (
        f"https://api.weixin.qq.com/cgi-bin/material/add_material"
        f"?access_token={token}&type=image"
    )
    req = urllib.request.Request(
        upload_url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
    result = json.loads(resp.read().decode("utf-8"))

    if "media_id" in result:
        return result["media_id"]
    else:
        log(f"  封面上传失败: {result}")
        return None


def get_wechat_token(ssl_ctx):
    url = (
        f"https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={WECHAT_APPID}&secret={WECHAT_APPSECRET}"
    )
    resp = urllib.request.urlopen(url, timeout=30, context=ssl_ctx)
    data = json.loads(resp.read().decode("utf-8"))
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"获取token失败: {data}")
    return token


def publish_draft(title, digest, content, thumb_media_id, token, ssl_ctx):
    """发布单篇文章到微信草稿"""
    payload = {
        "articles": [{
            "title": title,
            "author": WECHAT_AUTHOR,
            "digest": digest,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 1,
            "only_fans_can_comment": 0,
        }]
    }
    draft_url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        draft_url, data=json_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
    result = json.loads(resp.read().decode("utf-8"))
    return result


# ============================================================
#   🚀 主流程
# ============================================================

def do_articles(articles):
    """第1步: 生成文章HTML"""
    log("=" * 50)
    log(f"开始生成 {len(articles)} 篇文章")
    log("=" * 50)
    results = []
    for i, art in enumerate(articles):
        title = art["title"]
        html = build_html(art)
        safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:60]
        filepath = save_article(html, f"{safe_title}.html")
        log(f"  [{i+1}/{len(articles)}] {title}")
        log(f"    保存: {filepath}")
        results.append(filepath)
    log(f"文章生成完成: {len(results)} 篇")
    return results


def do_covers(articles):
    """第2步: 生成封面图"""
    log("=" * 50)
    log(f"开始生成 {len(articles)} 张封面图 (Pollinations.ai)")
    log("=" * 50)
    results = {}
    for i, art in enumerate(articles):
        title = art["title"]
        seed = hashlib.md5(title.encode()).hexdigest()[:8]
        filepath = generate_cover(art["keywords"], seed)
        if filepath:
            results[seed] = filepath
    log(f"封面生成完成: {len(results)} 张")
    return results


def do_publish():
    """第3步: 查找本地未发布的文章并发布到微信草稿"""
    log("=" * 50)
    log("开始发布到微信草稿")
    log("=" * 50)

    ssl_ctx = get_ssl_context()

    # 获取token
    token = get_wechat_token(ssl_ctx)
    log("access_token 获取成功")

    # 遍历文章配置列表
    for i, art in enumerate(ARTICLES):
        title = art["title"]
        digest = art["digest"]
        seed = hashlib.md5(title.encode()).hexdigest()[:8]

        # 找文章
        safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:60]
        art_path = os.path.join(ARTICLE_DIR, f"{safe_title}.html")
        if not os.path.exists(art_path):
            log(f"  [{i+1}] SKIP - 文章不存在: {art_path}")
            continue

        # 找封面
        cover_path = os.path.join(IMAGE_DIR, f"cover_{seed}.jpg")
        if not os.path.exists(cover_path):
            log(f"  [{i+1}] SKIP - 封面不存在: {cover_path}")
            continue

        # 上传封面
        log(f"  [{i+1}] 上传封面...")
        media_id = upload_cover(cover_path, token, ssl_ctx)
        if not media_id:
            log(f"  [{i+1}] FAIL - 封面上传失败")
            continue
        log(f"  [{i+1}] 封面上传成功: {media_id[:20]}...")

        # 读取文章正文
        with open(art_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        body_match = re.search(r"<body[^>]*>(.*)</body>", html_content, re.DOTALL)
        content = body_match.group(1).strip() if body_match else html_content

        # 发布草稿
        result = publish_draft(title, digest, content, media_id, token, ssl_ctx)
        if "media_id" in result:
            log(f"  [{i+1}] 发布成功: {title}")
        else:
            log(f"  [{i+1}] 发布失败: {result}")

    log("发布流程结束")


def do_list():
    """列出当前配置的文章"""
    if not ARTICLES:
        print("文章列表为空，请编辑 ARTICLES 配置。")
        return
    print(f"\n共 {len(ARTICLES)} 篇文章待生成/发布:\n")
    for i, art in enumerate(ARTICLES):
        seed = hashlib.md5(art["title"].encode()).hexdigest()[:8]
        safe_title = re.sub(r'[\\/:*?"<>|]', '', art["title"])[:60]
        art_exists = os.path.exists(os.path.join(ARTICLE_DIR, f"{safe_title}.html"))
        cover_exists = os.path.exists(os.path.join(IMAGE_DIR, f"cover_{seed}.jpg"))
        status = "✅" if (art_exists and cover_exists) else "⏳"
        print(f"  [{i+1}] {status} {art['title']}")
        print(f"       摘要: {art['digest']}")
        print(f"       标签: {art.get('tag', '无')}")
        print(f"       文章: {'有' if art_exists else '无'}  封面: {'有' if cover_exists else '无'}")
        print()


def main():
    os.makedirs(ARTICLE_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    args = set(sys.argv[1:])

    if "--list" in args:
        do_list()
        return

    if not ARTICLES:
        print("⚠️  ARTICLES 列表为空！")
        print("   请编辑 gen_article.py 中的 ARTICLES 列表，添加文章配置。")
        return

    # 仅生成文章
    if "--articles" in args:
        do_articles(ARTICLES)
        return

    # 仅生成封面
    if "--covers" in args:
        do_covers(ARTICLES)
        return

    # 仅发布
    if "--publish" in args:
        do_publish()
        return

    # 全流程: 文章 → 封面 → 发布
    log("🚀 全流程启动: 文章 → 封面 → 发布")
    do_articles(ARTICLES)
    covers = do_covers(ARTICLES)
    if len(covers) == len(ARTICLES):
        do_publish()
    else:
        log("⚠️  部分封面生成失败，跳过发布。可单独运行: python3 gen_article.py --publish")
    log("🎉 全部完成!")


if __name__ == "__main__":
    main()
