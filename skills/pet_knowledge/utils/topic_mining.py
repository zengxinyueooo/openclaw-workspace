#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys

def get_popular_topics(breed):
    """
    根据选定的品种，调用大模型生成热门科普话题。
    这是一个模拟函数，实际应调用LLM。
    """
    print(f"正在为‘{breed}’挖掘热门科普话题...", file=sys.stderr)
    
    # 模拟调用大模型的prompt
    # prompt = f"帮我科普{breed}，列出大众最关注的6-8个科普点（比如颜值特征、饲养难度、性格、易患病种、价格、养护技巧等），每个点用1句话概括（单句不超过20字）"
    # llm_response = call_llm(prompt)
    
    # 为了演示，返回固定的示例话题
    topics = {
        "颜值特征": "标志性小短腿，看起来萌萌哒。",
        "饲养难度": "需要细心呵护，对新手有一定挑战。",
        "性格特点": "活泼好动，像个永远充满好奇心的小孩子。",
        "易患病种": "需关注脊椎和关节健康问题。",
        "市场价格": "价格范围较广，根据品相决定。",
        "养护技巧": "避免剧烈跳跃，保护好它们的腰。",
        "互动表现": "非常亲人，喜欢和主人玩耍。"
    }
    return topics

if __name__ == "__main__":
    breed_name = sys.argv[1]
    result = get_popular_topics(breed_name)
    print(json.dumps(result, ensure_ascii=False))
