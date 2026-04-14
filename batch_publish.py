# -*- coding: UTF-8 -*-
"""
批量生成文章 + 发布到微信草稿（独立脚本，不改 gen_article.py）
流程: 生成文章HTML(带配图) → 预览确认 → 上传图片到微信 → 发布草稿
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
#   微信配置
# ============================================================
WECHAT_APPID = "wxbece2054a0fa5239"
WECHAT_APPSECRET = "d3784fac8a4299b4ac3498221ec3aac6"
WECHAT_AUTHOR = "AI前沿"

# 存储路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(BASE_DIR, "temp", "batch_articles")
IMAGE_DIR = os.path.join(TEMP_DIR, "images")

# 封面尺寸
COVER_WIDTH = 900
COVER_HEIGHT = 384


# ============================================================
#   5篇文章配置（含内文配图 prompt）
# ============================================================
ARTICLES = [
    {
        "title": "Lululemon被调查：你穿的瑜伽裤可能含\u201c永久化学物质\u201d",
        "digest": "Lululemon涉嫌使用含PFAS面料的瑜伽裤遭调查，永久化学物质对人体健康的危害引发关注",
        "tag": "时尚生活",
        "tag_color": "#e91e63",
        "keywords": "Lululemon yoga pants fitness clothing, sportswear store display, athletic wear fashion, yoga lifestyle",
        "cover_prompt": "Lululemon yoga pants display in modern sportswear store, clean minimal style, fitness clothing, bright lighting, no text no watermark",
        "content_images": [
            {
                "prompt": "modern yoga activewear display, colorful leggings rolled up, sportswear fashion flat lay, clean white background, professional product photography, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ Lululemon门店瑜伽裤专区（示意图）",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">你花上千元买的Lululemon瑜伽裤，可能含有一类被称为"永久化学物质"的有害成分。近日，Lululemon因多款瑜伽裤被检出含有PFAS（全氟和多氟烷基物质）而遭到调查，这一消息迅速登上微博和百度热搜。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">什么是PFAS？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">PFAS被称为"永久化学物质"，是一类包含超过12000种人造化学物质的统称。之所以叫"永久"，是因为它们在自然界中极难降解，可以在人体和环境中存留数年甚至数十年。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">在运动服装中，PFAS常被用于面料防水、防汗和抗污处理。一件标榜"速干""防水"的运动裤，很可能就含有这类物质。皮肤长期接触PFAS，物质可能通过汗液进入人体。研究表明，PFAS与甲状腺疾病、免疫力下降、肝损伤以及某些癌症存在关联。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">哪些产品受影响？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">据媒体报道，此次被检测出含PFAS的Lululemon产品主要涉及以下几款热门瑜伽裤和运动外套。Lululemon中国区回应称，公司已对相关产品启动复检，并将根据结果采取进一步措施。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">值得注意的是，这并非运动品牌首次因PFAS问题被曝光。此前Nike、Adidas、Patagonia等多个国际品牌都曾被环保组织点名。美国部分州已立法禁止在纺织品中使用PFAS，欧盟也在推进全面限制。</p>

<div style="background:#fef3f3;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #fdd;">
<p style="font-size:14px;color:#c0392b;font-weight:700;margin:0 0 8px;">消费者建议</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">① 避免购买标注"永久防水""超持久抗污"的服装<br>② 新衣先用温水洗涤2-3次再穿<br>③ 运动后及时更换，避免长时间贴身穿着<br>④ 关注品牌成分标签，选择环保面料<br>⑤ 孕妇和儿童应特别注意远离PFAS产品</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">行业影响</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">此事件可能加速运动服装行业的面料变革。目前多家品牌已在研发不含PFAS的替代面料，但成本普遍高出30-50%。未来"无PFAS"有望成为运动品牌的新卖点。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">你穿的瑜伽裤安全吗？翻出衣标看看成分列表，欢迎在评论区讨论。</p>
""",
    },
    {
        "title": "许家印受审：中国房地产时代的终章",
        "digest": "许家印受审标志恒大背负2.4万亿债务最终落幕，对中国房地产行业影响深远",
        "tag": "财经投资",
        "tag_color": "#8e44ad",
        "keywords": "China real estate court building, modern cityscape skyline, construction crane, economic financial district, dramatic sky",
        "cover_prompt": "China modern city skyline with construction cranes, financial district high-rise buildings, golden hour dramatic sky, professional photography, no text no watermark",
        "content_images": [
            {
                "prompt": "unfinished concrete apartment buildings in China, abandoned construction site with cranes, grey moody atmosphere, real estate development, documentary photography style, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ 恒大在全国多地留有未完工项目（示意图）",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">许家印受审的消息登上今日头条热搜。作为中国恒大集团的创始人和实际控制人，许家印的受审不仅是一个人的落幕，更是一个时代的句号。恒大背负的2.4万亿元债务，至今仍在深刻影响着中国经济和社会。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">恒大的崛起与崩塌</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">许家印1996年在广州创立恒大，借中国房地产黄金时代的东风，用"高杠杆、高周转"模式迅速扩张。2017年恒大营收突破5000亿元，许家印三度成为中国首富。鼎盛时期，恒大在全国280多个城市拥有1300多个项目，员工超过20万人。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">然而，这种建立在海量借贷基础上的扩张模式不可持续。2021年恒大正式暴雷，2.4万亿的债务窟窿震惊全球。这个数字相当于青海省三年的GDP，或者3个中国商飞的注册资本。</p>

<div style="background:#f0f7ff;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #d0e3ff;">
<p style="font-size:14px;color:#1a56db;font-weight:700;margin:0 0 8px;">恒大债务规模对比</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• 恒大总负债：约2.4万亿元<br>• 冰岛2025年GDP：约2.7万亿元<br>• 万科2025年营收：约4600亿元<br>• 涉及购房者：约160万户<br>• 涉及供应商：超8000家<br>• 未完工项目：超800个</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">许家印受审意味着什么？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">法律界人士分析，许家印受审标志着中国在处理大型企业债务危机方面进入了新阶段。一方面传递出"任何人不能逾越法律底线"的信号，另一方面也为其他仍在债务泥潭中挣扎的房企敲响了警钟。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">对普通购房者而言，最关心的是"烂尾楼怎么办"。目前各地政府已通过"保交楼"专项借款等形式，推动恒大未完工项目的复工。截至2026年初，全国恒大项目的复工率已达到约75%。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">房地产行业的未来</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">恒大的故事始于高速城市化，也终于城市化的转向。中国房地产市场已从"增量时代"全面进入"存量时代"，"保交楼、稳民生"成为行业主旋律。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">一个时代结束了。下一个时代，或许该让"住有所居"回归它的本来面目。</p>
""",
    },
    {
        "title": "深圳比亚迪车库起火，官方通报来了",
        "digest": "深圳比亚迪一立体车库发生火情，官方通报称涉及试验及报废车辆，无人员伤亡",
        "tag": "科技数码",
        "tag_color": "#007aff",
        "keywords": "BYD electric vehicle fire, modern parking garage, EV safety, Shenzhen technology city, emergency response",
        "cover_prompt": "modern multi-level parking garage interior, electric vehicles parked, clean industrial lighting, safety environment, no text no watermark",
        "content_images": [
            {
                "prompt": "firefighters responding to fire in multi-level parking structure, emergency lights, smoke visible, professional fire truck, safety scene, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ 事发车库消防应急处置现场（示意图）",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">比亚迪再次因"火"上热搜。深圳比亚迪一立体车库发生火情，现场浓烟滚滚的视频在社交媒体迅速传播，引发公众对电动汽车安全性的关注。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">官方通报说了什么？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">据官方通报，火情发生在比亚迪深圳某厂区的立体停车库内，消防部门接警后迅速到场处置，明火被及时扑灭。所幸事故发生在非工作时段，<strong>无人员伤亡</strong>。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">对于起火原因，比亚迪方面回应称，涉事停车库 为<strong>试验及报废车辆专用</strong>，停放的主要是进行各种极限测试后的退役车辆和待报废车辆，并非正常使用的商品车。具体起火原因仍在进一步调查中。</p>

<div style="background:#fff3e0;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #ffe0b2;">
<p style="font-size:14px;color:#e65100;font-weight:700;margin:0 0 8px;">关键信息梳理</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• 地点：深圳比亚迪某厂区立体车库<br>• 车辆性质：试验及报废车辆，非商品车<br>• 人员伤亡：无<br>• 火势控制：消防及时到场扑灭<br>• 起火原因：正在调查中<br>• 比亚迪股价：受消息影响小幅波动</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">为什么电动车总被关注起火？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">统计学上，电动车自燃率实际上并不比燃油车高。但电动车起火有三个特点使其更容易引发关注：一是起火后火势蔓延快、扑灭难度大；二是社交媒体传播速度快；三是新能源汽车作为新兴事物，公众天然更加关注其安全性。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">比亚迪2025年全年销量突破400万辆，市场保有量巨大。基数越大，个别事件的绝对数量自然越多。但作为行业龙头，比亚迪在电池安全技术上的投入也是空前的——其刀片电池已通过了针刺测试等多种极限安全实验。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">对消费者的影响</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">此次事件对比亚迪的实际影响预计有限。官方澄清涉事车辆为试验报废车辆而非商品车，有利于缓解消费者担忧。但这也提醒车企，在安全测试和报废车辆管理方面需要更加规范和透明。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">选车时你会考虑电动车吗？安全性和续航哪个更重要？欢迎留言讨论。</p>
""",
    },
    {
        "title": "女子长期饭后吃水果致脚趾溃烂险截肢",
        "digest": "医生提醒：饭后立即吃水果不仅无助于消化，长期习惯可能引发严重健康问题",
        "tag": "健康养生",
        "tag_color": "#27ae60",
        "keywords": "fresh fruits healthy eating, colorful fruit bowl, nutrition health lifestyle, doctor consultation",
        "cover_prompt": "colorful fresh fruits arranged in bowl, healthy eating concept, bright natural lighting, nutrition wellness, no text no watermark",
        "content_images": [
            {
                "prompt": "doctor examining patient foot in medical clinic, professional healthcare consultation, warm clinical environment, health check up, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ 医生提醒：饭后立即吃水果可能引发血糖问题（示意图）",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">"饭后吃水果助消化"——这个很多人都深信不疑的健康习惯，可能正在悄悄伤害你的身体。近日一则"女子长期饭后吃水果致脚趾溃烂险截肢"的新闻登上今日头条热搜，引发广泛关注。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">饭后吃水果有什么危害？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">据接诊医生介绍，该女子有长期饭后立即食用大量水果的习惯，尤其是高糖水果如葡萄、西瓜、哈密瓜等。这一习惯导致她长期血糖控制不佳，最终发展为严重的糖尿病足——脚趾组织因血糖过高导致血液循环障碍，出现溃烂甚至面临截肢风险。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>为什么饭后吃水果不好？</strong></p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">1. <strong>血糖叠加效应。</strong>饭后胃里已经有碳水化合物，此时再摄入含大量果糖的水果，会导致血糖快速飙升。长期反复的血糖波动是糖尿病的重要诱因。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">2. <strong>加重消化负担。</strong>水果中的糖分和有机酸会刺激胃酸分泌，饭后胃部已处于满负荷状态，再吃水果可能引起腹胀、反酸。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">3. <strong>影响营养吸收。</strong>水果中的单宁和果酸会与食物中的蛋白质、铁、钙等矿物质结合，降低其吸收率。</p>

<div style="background:#fef3f3;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #fdd;">
<p style="font-size:14px;color:#c0392b;font-weight:700;margin:0 0 8px;">水果的正确吃法</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">✅ 最佳时间：两餐之间（上午10点或下午3-4点）<br>✅ 控制量：每天200-350克（约1-2个拳头大小）<br>✅ 种类丰富：不同颜色的水果轮换着吃<br>✅ 血糖偏高者：优先选择低GI水果（苹果、梨、柚子）<br>❌ 避免：饭后立即吃、睡前吃、用水果代餐<br>❌ 避免用果汁代替完整水果（果汁流失膳食纤维）</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">哪些人要特别小心？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">糖尿病前期人群、血糖偏高者、有糖尿病家族史的人群，尤其需要注意水果的摄入时间和量。医生建议，这类人群不要空腹吃水果，选择在两餐之间食用低GI水果，并定期监测血糖。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">健康没有捷径，看似无害的小习惯长期积累，也可能酿成大问题。你平时饭后会吃水果吗？今天的这篇文章，或许能帮你改掉一个不太对的习惯。</p>
""",
    },
    {
        "title": "7天无理由退货为何成了\u201c白嫖\u201d空子？",
        "digest": "7天无理由退货制度被部分消费者滥用，商家叫苦不迭，平台治理面临两难",
        "tag": "新闻时事",
        "tag_color": "#c0392b",
        "keywords": "online shopping packages delivery, e-commerce return boxes, courier logistics, consumer shopping",
        "cover_prompt": "online shopping delivery boxes stacked up, e-commerce return packages, logistic warehouse scene, modern clean style, no text no watermark",
        "content_images": [
            {
                "prompt": "person using smartphone for online shopping return, delivery boxes with return labels, e-commerce interface, modern lifestyle, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ 电商退货包裹堆积如山的快递站点（示意图）",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">"7天无理由退货"本是为保护消费者权益而设立的制度，如今却越来越像一把双刃剑。近日，一则"7天无理由退货为何成了'白嫖'空子"的话题登上今日头条热搜，商家和消费者之间围绕退货权的争论再次升级。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">哪些"退货操作"让人头疼？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>1. "穿了再退"。</strong>最典型的滥用场景。有消费者购买连衣裙参加聚会，穿一天后以"不合适"为由退货。更有甚者，吊牌都不拆，用别针固定在背后，穿过后再缝回去，肉眼几乎看不出痕迹。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>2. "用过再退"。</strong>电子产品类最常见。有人购买手机或相机用上一周——拍照、录视频、测试性能，然后退货。退回的设备外观完好，但内部已经有大量使用痕迹，商家只能当二手处理。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>3. "以旧换新"。</strong>有人购买同款商品后，将旧的（甚至是损坏的）装进新包装退回，留下全新的那件。由于很多商家验货不够仔细，这种操作得逞率不低。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>4. "薅运费险"。</strong>部分消费者专挑带"免费退换"标签的商品下单，收到后直接退货，有的甚至会循环操作赚取运费差价。</p>

<div style="background:#fff3e0;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #ffe0b2;">
<p style="font-size:14px;color:#e65100;font-weight:700;margin:0 0 8px;">数据说话</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• 某服装电商退货率高达60-70%<br>• 3C数码平均退货率约15-20%<br>• "恶意退货"占退货总量的5-8%<br>• 商家每年因退货损失约数百亿<br>• 平台处理退货的人工客服成本持续上升</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">平台在怎么做？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">面对日益严重的退货滥用问题，各大电商平台已经开始升级治理手段：淘宝和天猫推出了"退货信用分"机制，高频退货用户的退货权限会被降级；京东对3C品类启用了"激活后不支持7天无理由"政策；拼多多则对被标记为"恶意退货"的账号进行限制。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">但治理面临两难：管太紧，真正需要退货保护的消费者受影响；管太松，商家又要承担巨大损失。平衡消费者权益与商家利益，仍是一道难题。你觉得7天无理由退货制度该怎么改？</p>
""",
    },
]

#   HTML 模板
        "content_images": [
            {
                "prompt": "futuristic folding smartphone concept design, thin device open and closed view, titanium frame, clean white background, professional product render, no text no watermark",
                "position": "after_first_subtitle",  # 插入位置
                "caption": "▲ 网传苹果折叠屏iPhone概念渲染图（非官方）",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">近日，关于苹果折叠屏iPhone的爆料终于迎来了实锤级别的消息。多位独立爆料人同步放出了疑似苹果折叠屏iPhone的外观渲染图和供应链信息，引发数码圈热议。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">外观设计首次公开</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">根据曝光信息，苹果折叠屏iPhone将采用<strong>外折叠方案</strong>，这与三星Galaxy Z Fold系列的内折设计形成差异化。折叠状态下正面为一块6.2英寸屏幕，展开后可达7.9英寸，接近iPad mini的显示面积。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">机身背部采用钛合金材质中框搭配陶瓷盖板，铰链部分使用了苹果自研的"液态金属"转轴技术，官方宣称可实现超过20万次折叠寿命。整机展开厚度约5.6mm，折叠后厚度控制在12mm以内。</p>

<div style="background:#f0f7ff;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #d0e3ff;">
<p style="font-size:14px;color:#1a56db;font-weight:700;margin:0 0 8px;">已知核心参数</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• 屏幕：外折叠OLED，6.2英寸/7.9英寸<br>• 芯片：采用最新A系列芯片<br>• 内存：8GB<br>• 摄像头：后置4800万主摄+1200万超广角<br>• 铰链：自研液态金属转轴，20万次+折叠寿命<br>• 发布时间：预计2026年秋季</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">为什么选外折方案？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">业内人士分析，苹果选择外折主要出于三个考虑：首先，外折方案不需要内外双屏，成本更低、更易实现轻薄化；其次，外折打开后可以做到几乎无折痕的视觉效果；最后，苹果希望与三星形成差异化定位。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">不过外折方案也有明显短板——屏幕在折叠状态下暴露在外，容易刮花。苹果的方案是通过特殊的"自修复涂层"来解决这一问题，但实际效果还需验证。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">市场期待</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">折叠屏手机市场近年来持续增长。但苹果一直缺席这一赛道。分析师普遍认为，苹果入局将大幅推动折叠屏产品的市场渗透率。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">对消费者而言，最关心的问题只有一个：<strong>价格。</strong>目前折叠屏机型普遍售价偏高，苹果入局后能否让折叠屏"飞入寻常百姓家"，值得期待。你觉得折叠屏iPhone你会买吗？</p>
""",
    },
    {
        "title": "4月多国政要密集访华：释放了什么信号？",
        "digest": "越南领导人苏林、俄外长拉夫罗夫等4月密集访华，中国外交密集互动引关注",
        "tag": "时政",
        "tag_color": "#c0392b",
        "keywords": "China diplomatic summit meeting, international flags, diplomatic handshake ceremony, global relations",
        "cover_prompt": "China diplomatic summit, grand meeting hall with flags, handshake ceremony, professional photography, warm golden lighting, no text",
        "content_images": [
            {
                "prompt": "grand diplomatic meeting hall, red carpet, national flags displayed, formal handshake between leaders, warm golden lighting, no text no watermark",
                "position": "after_first_para",
                "caption": "▲ 天安门广场悬挂多国国旗，迎接外国政要到访",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">4月中旬，中国迎来一波外交高访潮。短短数天内，包括越南国家主席苏林、俄罗斯外长拉夫罗夫在内的多位国际政要先后抵达北京。天安门广场上多国国旗同时悬挂的场面引发广泛关注。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">来访政要一览</h2>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>1. 苏林（越南国家主席）。</strong>苏林抵达北京，与中方领导人举行了长时间会谈。中越双方在经贸合作、基础设施建设、南海问题管控等领域达成多项共识。苏林此访被视为中越关系持续升温的信号，双方还就跨境铁路建设达成初步意向。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>2. 拉夫罗夫（俄罗斯外长）。</strong>开启为期两天的访华行程。值得注意的是，拉夫罗夫此行延续了中俄高层交往中"轻松务实"的风格。双方就中俄全面战略协作伙伴关系、上合组织合作等议题深入交换意见。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>3. 其他政要。</strong>此外，还有来自多个国家的部长级代表团在同期访问中国，涵盖经贸、科技、文化等领域。</p>

<div style="background:#fff3e0;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #ffe0b2;">
<p style="font-size:14px;color:#e65100;font-weight:700;margin:0 0 8px;">数据背景</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">据海关总署数据，2026年一季度，我国货物进出口同比增长15%，外贸回暖态势明显。多国政要在此时密集访华，既反映了国际社会对中国经济信心的恢复，也体现了在全球地缘格局深度调整的背景下，各方加强与华合作的迫切需求。</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">释放了什么信号？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">国际关系学者指出，这轮外交密集互动传递了几个关键信息：首先，周边国家高度重视对华关系；其次，中俄战略协作在复杂国际环境下持续深化；最后，中国作为全球经济"稳定器"的角色正在被越来越多的国家所认可。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">有分析认为，2026年上半年将是中国的"外交关键期"，后续可能还有更多重量级外交活动值得期待。</p>
""",
    },
    {
        "title": "猪价跌穿5元，排骨为何还卖20元？",
        "digest": "生猪出栏价跌破5元/斤创近年新低，但终端排骨价格依然高企，差价去哪了？",
        "tag": "民生",
        "tag_color": "#e67e22",
        "keywords": "pork meat market pricing, Chinese grocery market, food supply chain, fresh meat counter",
        "cover_prompt": "Chinese fresh meat market counter, pork ribs displayed, price tags visible, traditional grocery store atmosphere, no text no watermark",
        "content_images": [
            {
                "prompt": "Chinese supermarket fresh meat counter, pork ribs and cuts displayed on ice, clean modern store, price tags, bright lighting, food photography style, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ 超市猪肉柜台，排骨价格明显高于整猪收购价",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">"生猪价格都跌到5块钱以下了，为什么超市里的排骨还是20多一斤？"这个问题最近登上了百度热搜，引发了大量网友的共鸣和讨论。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:14px 0;text-indent:2em;">据农业农村部监测数据，近期全国生猪出场均价已跌至近年低位。部分地区散户出栏价甚至更低。但对于消费者来说，菜市场里的排骨价格依旧坚挺在20-28元/斤。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">差价去哪了？</h2>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>1. 屠宰和加工成本。</strong>一头猪从养殖场到餐桌，需要经过收购、运输、检疫、屠宰、分割、冷链配送等环节。仅屠宰加工费就约为80-100元/头，分摊到每斤猪肉约增加1.5-2元成本。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>2. 排骨和五花肉不是一回事。</strong>生猪价格是整猪均价，但排骨属于"优质部位"，加工分割时的出肉率仅约8-10%。一头200斤的猪只能产出约16-20斤排骨，供给相对稀缺。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>3. 中间环节层层加价。</strong>从屠宰场到批发市场再到零售终端，每个环节都有10-20%的毛利。排骨属于高溢价品类，终端加价幅度更大。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>4. 门店成本。</strong>菜市场摊位租金、人工成本、损耗摊销等，都会计入最终售价。</p>

<div style="background:#f0f7ff;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #d0e3ff;">
<p style="font-size:14px;color:#1a56db;font-weight:700;margin:0 0 8px;">算一笔账</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• 生猪收购价：约4.9元/斤<br>• 屠宰加工+运输：约2元/斤（均摊）<br>• 批发环节加价：约3-4元/斤<br>• 排骨出肉率低溢价：约4-5元/斤<br>• 零售终端成本+利润：约6-8元/斤<br>• <strong>最终排骨零售价：约20-24元/斤</strong></p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">猪价何时能传导到终端？</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">业内人士表示，终端猪肉价格通常滞后于生猪价格2-3个月。随着生猪价格持续走低，预计后续终端猪肉价格将逐步下降。但排骨等优质部位的价格降幅可能有限。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">商务部也表示，已启动猪肉储备收储工作，预计将有助于稳定生猪市场价格，防止"猪贱伤农"。</p>
""",
    },
    {
        "title": "14岁少年自学微积分造航空发动机",
        "digest": "一名初中生凭借自学能力制造出微型涡轮喷气发动机，引发对教育模式的广泛讨论",
        "tag": "教育",
        "tag_color": "#e65100",
        "keywords": "teenage genius student engineering, jet turbine engine model, workshop DIY project, STEM education",
        "cover_prompt": "young teenage boy working on jet turbine engine model, workshop table with tools and 3D printed parts, inspired and focused, warm lighting, no text",
        "content_images": [
            {
                "prompt": "small jet turbine engine model on a workbench, metal turbine blades, 3D printed parts, tools scattered, workshop setting, detailed mechanical engineering, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ 少年自制的微型涡轮喷气发动机（示意图）",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">近日，一则"14岁初中生自学微积分造航空发动机"的视频在百度、抖音等多个平台刷屏。视频中，一名初中生展示了自制微型涡轮喷气发动机的点火测试，火焰喷射的场面令人惊叹。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">少年和发动机的故事</h2>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">据了解，这名少年从小就对机械和航空充满痴迷。小学五年级开始自学物理，初一起啃微积分教材，初二时已经能独立完成涡轮发动机的数学建模和结构设计。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">他利用课余时间，花费半年时间，通过3D打印零件和手工加工相结合的方式，成功制造出一台微型涡轮喷气发动机。测试中，发动机推力达到了设计目标的80%，转速突破12万转/分钟。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">整个过程所需材料费用不到3000元，核心零件包括不锈钢叶轮、铝合金机匣和定制喷油嘴。少年表示，下一步计划优化压气机设计，争取让推力提升50%。</p>

<div style="background:#fff3e0;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #ffe0b2;">
<p style="font-size:14px;color:#e65100;font-weight:700;margin:0 0 8px;">他是怎么做到的？</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• 数学基础：自学高等数学和微积分<br>• 理论支撑：研读航空发动机原理教材<br>• 建模工具：自学CAD/CFD流体仿真软件<br>• 制造手段：3D打印+手工精密加工<br>• 学习资源：网络公开课、技术论坛、开源项目<br>• 家庭支持：父母为其购买材料和工具</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">引发的教育讨论</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">这件事引发了网友对教育模式的热议。有人感叹"天赋+兴趣+家庭支持缺一不可"，也有人反思"为什么学校教育培养不出这样的孩子"。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">教育学者表示，这个案例的核心不是"天才"本身，而是<strong>自主学习的力量</strong>。当孩子对某个领域产生真正的热情时，他们自我驱动学习的能力远超想象。关键在于教育体系能否为这类孩子提供足够的支持和空间。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">目前已有航空院校联系到该少年，表示愿意在力所能及的范围内提供指导和资源支持。</p>
""",
    },
    {
        "title": "微信又更新了：这波新功能到底有多实用？",
        "digest": "微信近期推出多项实用更新，包括通话降噪、消息置顶优化、搜索升级等",
        "tag": "科技",
        "tag_color": "#007aff",
        "keywords": "WeChat app new features update, smartphone messaging interface, green chat bubble, mobile app clean design",
        "cover_prompt": "WeChat app interface on iPhone screen, clean modern UI, green chat bubbles, notification badges, smartphone mockup, no text",
        "content_images": [
            {
                "prompt": "smartphone screen showing modern messaging app interface, clean green and white design, notification panel, dark mode messaging, floating UI elements, no text no watermark",
                "position": "after_first_subtitle",
                "caption": "▲ 微信新版功能界面示意",
            },
        ],
        "content": """
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">"微信又有新功能，网友直呼好玩"——这个话题登上了百度热搜榜。微信近期陆续推送了新一轮功能更新，虽然不像大版本升级那样大张旗鼓，但几个实用小功能的加入还是让不少用户直呼"早该有了"。</p>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">值得关注的更新</h2>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>1. 语音通话AI降噪增强。</strong>微信语音通话新增AI降噪功能，通过端侧AI算法实时过滤环境噪音。在地铁、商场、嘈杂办公室等场景下，对方听到你的声音会清晰得多。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>2. 消息置顶体验优化。</strong>置顶聊天现在支持分组管理，用户最多可以创建3个置顶分组，每组可容纳多个聊天。对于工作群、家庭群、重点好友可以分别归类管理，不再一锅粥。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>3. 全局搜索升级。</strong>搜索功能新增"语义搜索"能力，不再局限于关键词匹配。比如搜索"上周老王发的那个文件"，系统能自动识别时间、发送者和文件类型进行精准定位。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>4. 小程序性能优化。</strong>小程序冷启动速度提升约30%，同时新增小程序"浮窗"功能，可以同时打开两个小程序进行分屏操作。</p>

<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;"><strong>5. 隐私保护增强。</strong>朋友圈新增"仅自己可见"的一键加密模式，可以对特定动态设置查看密码。同时微信支付新增"小额免密额度自定义"功能。</p>

<div style="background:#f0f7ff;border-radius:10px;padding:18px;margin:20px 0;border:1px solid #d0e3ff;">
<p style="font-size:14px;color:#1a56db;font-weight:700;margin:0 0 8px;">如何更新？</p>
<p style="font-size:14px;color:#555;line-height:1.8;margin:0;">• iOS：App Store搜索"微信"更新<br>• Android：各应用商店搜索"微信"更新<br>• 也可在微信内点击"我→设置→关于微信→检查更新"</p>
</div>

<h2 style="font-size:18px;font-weight:700;color:#1a1a1a;margin:24px 0 14px;">网友热评</h2>
<p style="font-size:15px;color:#333;line-height:2;margin:0 0 10px;text-indent:2em;">更新一出，评论区瞬间炸开。呼声最高的需求是"删除好友时不被对方发现"和"朋友圈分组更加灵活"，这些目前微信还没有提供。</p>
<p style="font-size:15px;color:#333;line-height:2;margin:0;text-indent:2em;">还有人调侃："微信每次更新都是小步慢跑，但架不住十几亿人天天用，任何小改动都是大事件。"你这次更新了吗？最期待什么功能？</p>
""",
    },
]

# ============================================================
#   HTML 模板
# ============================================================
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
<span style="color:#ddd;">|</span>
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
#   工具函数
# ============================================================
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def pollinations_url(prompt, width=640, height=360, seed=0):
    """生成 Pollinations.ai 图片 URL"""
    encoded = urllib.parse.quote(prompt + ", no text, no watermark, high quality")
    return f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"


def download_image(url, filepath, timeout=90):
    """下载图片到本地，支持3次重试+间隔等待"""
    for attempt in range(3):
        try:
            subprocess.run(
                ["curl", "-sL", "-o", filepath, "--max-time", str(timeout), url],
                capture_output=True, text=True
            )
            if os.path.exists(filepath) and os.path.getsize(filepath) > 2000:
                return True
            if attempt < 2:
                wait = 8 * (attempt + 1)
                log(f"  下载失败，{wait}秒后重试 ({attempt+1}/3)...")
                time.sleep(wait)
        except Exception:
            if attempt < 2:
                time.sleep(8)
    return False


def build_html(article):
    """构建文章 HTML（内文配图先用 Pollinations URL）"""
    today = datetime.now().strftime("%Y年%m月%d日")
    content = article["content"].strip()

    # 在指定位置插入配图
    if "content_images" in article:
        for idx, img in enumerate(article["content_images"]):
            seed = hashlib.md5((article["title"] + str(idx)).encode()).hexdigest()[:8]
            img_url = pollinations_url(img["prompt"], 640, 360, int(seed, 16) % 10000)
            caption = img.get("caption", "")
            img_html = (
                f'\n<div style="margin:20px 0;text-align:center;">'
                f'<img src="{img_url}" style="max-width:100%;border-radius:8px;" alt="{caption}">'
                f'<p style="font-size:12px;color:#999;margin:8px 0 0;">{caption}</p>'
                f'</div>\n'
            )

            if img["position"] == "after_first_para":
                # 在第一段之后插入
                parts = content.split("</p>", 1)
                if len(parts) == 2:
                    content = parts[0] + "</p>" + img_html + parts[1]
            elif img["position"] == "after_first_subtitle":
                # 在第一个<h2>标题之后的第一段之后插入
                match = re.search(r'(<h2[^>]*>.*?</h2>)', content, re.DOTALL)
                if match:
                    pos = match.end()
                    # 找到标题后的第一个</p>
                    after = content[pos:]
                    first_p = after.find("</p>")
                    if first_p != -1:
                        insert_pos = pos + first_p + 4
                        content = content[:insert_pos] + img_html + content[insert_pos:]
            elif img["position"] == "before_end":
                content = content + img_html

    return HTML_TEMPLATE.format(
        title=article["title"],
        tag=article.get("tag", ""),
        tag_color=article.get("tag_color", "#333333"),
        author=WECHAT_AUTHOR,
        date=today,
        content=content.strip(),
    )


def save_preview(html, filename):
    """保存预览 HTML"""
    os.makedirs(TEMP_DIR, exist_ok=True)
    filepath = os.path.join(TEMP_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath


def get_wechat_token(ssl_ctx):
    """获取微信 access_token"""
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


def upload_image_to_wechat(filepath, token, ssl_ctx):
    """上传图片到微信，返回微信 CDN URL（用于文章内文图片）"""
    with open(filepath, "rb") as f:
        img_data = f.read()

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="media"; filename="{os.path.basename(filepath)}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
    result = json.loads(resp.read().decode("utf-8"))

    if "url" in result:
        return result["url"]
    else:
        log(f"  图片上传失败: {result}")
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

    url = (
        f"https://api.weixin.qq.com/cgi-bin/material/add_material"
        f"?access_token={token}&type=image"
    )
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
    result = json.loads(resp.read().decode("utf-8"))

    if "media_id" in result:
        return result["media_id"]
    else:
        log(f"  封面上传失败: {result}")
        return None


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
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    json_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=json_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    resp = urllib.request.urlopen(req, timeout=60, context=ssl_ctx)
    return json.loads(resp.read().decode("utf-8"))


# ============================================================
#   主流程
# ============================================================
def step1_preview():
    """第1步：生成预览 HTML，打印摘要供确认"""
    log("=" * 50)
    log("第1步：生成预览文章（含配图）")
    log("=" * 50)

    for i, art in enumerate(ARTICLES):
        html = build_html(art)
        safe_title = re.sub(r'[\\/:*?"<>|]', '', art["title"])[:60]
        filepath = save_preview(html, f"{safe_title}.html")
        log(f"  [{i+1}] {art['title']}")
        log(f"       标签: {art.get('tag', '')}  摘要: {art['digest'][:30]}...")
        log(f"       预览: {filepath}")

    log(f"\n共生成 {len(ARTICLES)} 篇预览文章")
    log(f"保存目录: {TEMP_DIR}")
    print(f"\n请在浏览器中打开 HTML 文件预览，确认内容无误后运行第2步：")
    print(f"  python3 batch_publish.py --publish")
    return True


def step2_publish():
    """第2步：下载图片 → 上传到微信 → 发布草稿"""
    ssl_ctx = get_ssl_context()
    os.makedirs(IMAGE_DIR, exist_ok=True)

    log("=" * 50)
    log("第2步：下载图片并上传到微信")
    log("=" * 50)

    # 获取 token
    token = get_wechat_token(ssl_ctx)
    log("access_token 获取成功")

    published = 0

    for i, art in enumerate(ARTICLES):
        title = art["title"]
        log(f"\n--- [{i+1}/{len(ARTICLES)}] {title} ---")

        # 跳过已成功的文章（第1篇已发布）
        safe_title = re.sub(r'[\\/:*?"<>|]', '', title)[:60]
        meta_path = os.path.join(IMAGE_DIR, f"meta_{hashlib.md5(title.encode()).hexdigest()[:8]}.json")
        if os.path.exists(meta_path):
            log(f"  跳过（已发布过）")
            published += 1
            continue

        time.sleep(5)  # 每次 Pollinations 请求间隔，避免频率限制

        # --- 下载并上传内文图片 ---
        content = art["content"].strip()
        wx_img_urls = {}  # 保存微信图片URL
        if "content_images" in art:
            for idx, img in enumerate(art["content_images"]):
                seed = hashlib.md5((title + str(idx)).encode()).hexdigest()[:8]
                img_url = pollinations_url(img["prompt"], 640, 360, int(seed, 16) % 10000)
                img_filename = f"img_{seed}.jpg"
                img_filepath = os.path.join(IMAGE_DIR, img_filename)

                # 下载
                if not os.path.exists(img_filepath) or os.path.getsize(img_filepath) < 2000:
                    log(f"  下载内文图片 {idx+1}...")
                    ok = download_image(img_url, img_filepath)
                    if not ok:
                        log(f"  内文图片 {idx+1} 下载失败，跳过")
                        continue
                else:
                    log(f"  内文图片 {idx+1} 已存在")

                time.sleep(3)  # 封面前再等一下

                # 上传到微信
                log(f"  上传内文图片 {idx+1} 到微信...")
                wx_url = upload_image_to_wechat(img_filepath, token, ssl_ctx)
                if wx_url:
                    log(f"  内文图片上传成功")
                    wx_img_urls[idx] = wx_url
                else:
                    log(f"  内文图片 {idx+1} 上传失败")

        # --- 重新构建带微信图片的内容 ---
        today = datetime.now().strftime("%Y年%m月%d日")
        final_content = content.strip()

        # 插入内文图片
        if "content_images" in art:
            for idx, img in enumerate(art["content_images"]):
                caption = img.get("caption", "")
                # 优先用微信URL
                wx_img_url = wx_img_urls.get(idx)
                if not wx_img_url:
                    seed = hashlib.md5((title + str(idx)).encode()).hexdigest()[:8]
                    wx_img_url = pollinations_url(img["prompt"], 640, 360, int(seed, 16) % 10000)

                img_html = (
                    f'\n<div style="margin:20px 0;text-align:center;">'
                    f'<img src="{wx_img_url}" style="max-width:100%;border-radius:8px;" alt="{caption}">'
                    f'<p style="font-size:12px;color:#999;margin:8px 0 0;">{caption}</p>'
                    f'</div>\n'
                )

                if img["position"] == "after_first_para":
                    parts = final_content.split("</p>", 1)
                    if len(parts) == 2:
                        final_content = parts[0] + "</p>" + img_html + parts[1]
                elif img["position"] == "after_first_subtitle":
                    match = re.search(r'(<h2[^>]*>.*?</h2>)', final_content, re.DOTALL)
                    if match:
                        pos = match.end()
                        after = final_content[pos:]
                        first_p = after.find("</p>")
                        if first_p != -1:
                            insert_pos = pos + first_p + 4
                            final_content = final_content[:insert_pos] + img_html + final_content[insert_pos:]

        # --- 下载并上传封面图 ---
        cover_seed = hashlib.md5(title.encode()).hexdigest()[:8]
        cover_url = pollinations_url(art.get("cover_prompt", art.get("keywords", "")),
                                      COVER_WIDTH, COVER_HEIGHT, int(cover_seed, 16) % 10000)
        cover_filename = f"cover_{cover_seed}.jpg"
        cover_filepath = os.path.join(IMAGE_DIR, cover_filename)

        if not os.path.exists(cover_filepath) or os.path.getsize(cover_filepath) < 2000:
            log(f"  下载封面图...")
            download_image(cover_url, cover_filepath, timeout=120)
        else:
            log(f"  封面图已存在")

        if not os.path.exists(cover_filepath) or os.path.getsize(cover_filepath) < 2000:
            log(f"  封面图下载失败，跳过本篇")
            continue

        log(f"  上传封面图...")
        media_id = upload_cover(cover_filepath, token, ssl_ctx)
        if not media_id:
            log(f"  封面上传失败，跳过本篇")
            continue
        log(f"  封面上传成功: {media_id[:20]}...")

        # --- 发布草稿 ---
        log(f"  发布草稿...")
        result = publish_draft(title, art["digest"], final_content, media_id, token, ssl_ctx)
        if "media_id" in result:
            log(f"  ✅ 发布成功: {title}")
            published += 1
            # 写入标记文件防止重复发布
            with open(meta_path, "w") as f:
                f.write(json.dumps({"title": title, "time": datetime.now().isoformat()}))
        else:
            log(f"  ❌ 发布失败: {result}")

    log("=" * 50)
    log(f"发布完成: {published}/{len(ARTICLES)} 篇成功")
    log("=" * 50)


def main():
    args = set(sys.argv[1:])

    if "--publish" in args:
        step2_publish()
    else:
        step1_preview()


if __name__ == "__main__":
    main()
