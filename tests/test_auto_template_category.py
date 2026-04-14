# -*- coding: UTF-8 -*-
"""
测试自动匹配模板分类功能
覆盖全部 10 个类目，验证分类匹配是否正确
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dataclasses import dataclass
from typing import Dict, Any
from unittest.mock import MagicMock, patch
from datetime import datetime


# 模拟 ContentResult（不依赖真实模块）
@dataclass
class MockContentResult:
    title: str
    content: str
    summary: str = ""
    content_format: str = "markdown"
    metadata: Dict[str, Any] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


def run_test():
    # 仅测试分类匹配逻辑，mock 掉外部依赖
    from src.ai_write_x.core.unified_workflow import UnifiedContentWorkflow

    test_cases = [
        # (标题, 正文摘要, 期望分类)
        (
            "DeepSeek R2推理模型发布，数学能力超越OpenAI o3",
            "DeepSeek发布R2推理模型，引入思维树架构，支持12种编程语言，API定价策略激进",
            "科技数码",
        ),
        (
            "A股三大指数集体上涨，沪指重回3300点",
            "股票市场今日表现强劲，基金净值普遍回升，融资余额连续增加，GDP数据超预期",
            "财经投资",
        ),
        (
            "最新研究：每天走路30分钟可降低癌症风险",
            "医疗专家建议通过锻炼和健康饮食来预防疾病，定期体检和疫苗接种也必不可少",
            "健康养生",
        ),
        (
            "2026高考AI专业大学排名出炉，清华蝉联榜首",
            "清华北大浙大位列三甲，高考录取分数持续走高，考研竞争激烈，录取专业更热门",
            "教育学习",
        ),
        (
            "成都三天两夜美食攻略，人均不到500元",
            "打卡多家网红餐厅和火锅店，酒店性价比超高的民宿推荐，机票便宜签证方便",
            "美食旅行",
        ),
        (
            "2026春夏穿搭趋势：极简风重回巅峰",
            "国际时装周引领潮流，奢侈品牌推出新护肤系列，美妆博主推荐爆款单品造型",
            "时尚生活",
        ),
        (
            "婚后三年才发现的婚姻真相，句句扎心",
            "恋爱和婚姻完全不同，夫妻之间需要用心经营，亲子关系和婆媳矛盾是离婚主因",
            "情感心理",
        ),
        (
            "4月多国政要密集访华，释放了什么信号？",
            "外交部发布声明，国际会谈取得成果，政府政策调整，联合国会议讨论制裁法案",
            "新闻时事",
        ),
        (
            "某顶流偶像塌房！粉丝集体脱粉，代言全部下架",
            "娱乐圈大地震，明星绯闻曝光后官宣分手，综艺热搜霸榜，直播人气暴跌",
            "娱乐八卦",
        ),
        (
            "互联网大厂裁员潮再起，这3个岗位最危险",
            "职场人纷纷面试跳槽，996加班文化引发讨论，五险一金和社保成求职关注焦点",
            "职场发展",
        ),
    ]

    # Mock Config 和 log
    mock_config = MagicMock()
    mock_config.custom_template_category = ""
    mock_config.template_category = ""

    workflow = UnifiedContentWorkflow.__new__(UnifiedContentWorkflow)

    print(f"\n{'='*60}")
    print(f"{'类目':<8} {'期望分类':<8} {'实际分类':<8} {'匹配度':<6} {'结果'}")
    print(f"{'-'*60}")

    passed = 0
    failed = 0

    for i, (title, content, expected) in enumerate(test_cases):
        mock_config.custom_template_category = ""
        mock_config.template_category = ""

        with patch("src.ai_write_x.core.unified_workflow.Config") as MockCfg, \
             patch("src.ai_write_x.core.unified_workflow.log") as mock_log:
            MockCfg.get_instance.return_value = mock_config

            article = MockContentResult(title=title, content=content)
            workflow._auto_match_template_category(article)

            actual = mock_config.custom_template_category
            match = actual == expected

            if match:
                passed += 1
                status = "✅ PASS"
            else:
                failed += 1
                status = "❌ FAIL"

            # 从 log 调用中提取匹配度
            score_str = ""
            for call in mock_log.print_log.call_args_list:
                msg = str(call)
                if "自动匹配模板分类" in msg:
                    import re as _re
                    m = _re.search(r"匹配度 (\d+)", msg)
                    if m:
                        score_str = m.group(1)

            short_title = title[:16] + "..." if len(title) > 16 else title
            print(f"{short_title:<20} {expected:<8} {actual:<8} {score_str:<6} {status}")

    print(f"{'-'*60}")
    print(f"总计 {len(test_cases)} 个测试，通过 {passed} 个，失败 {failed} 个")
    print(f"{'='*60}\n")

    return failed == 0


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
