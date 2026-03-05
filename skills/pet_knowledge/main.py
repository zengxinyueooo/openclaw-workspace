#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
import subprocess
import yaml

# --- 配置与路径 --- #
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SKILL_DIR, 'config.yml')

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

config = load_config()
IMAGE_GENERATOR_SCRIPT = config['image_generator']['script_path']

# --- 交互式输入/确认函数 --- #
def get_user_confirmation(prompt):
    """模拟获取用户的确认或调整指令。"""
    print(f"\n[小桃] 🍑 {prompt}")
    response = input("[宝宝] 你的选择是: ")
    return response

# --- 步骤1：品种检索 --- #
def step1_breed_selection(category):
    while True:
        # 调用工具脚本
        process = subprocess.run(["python3", os.path.join(SKILL_DIR, "utils/breed_search.py"), category], capture_output=True, text=True)
        breeds = json.loads(process.stdout)
        
        choice = get_user_confirmation(f"宝宝，我为你找到了这些小众又可爱的‘{category}’：{breeds}。你喜欢哪一个呀？或者你心里有别的选择吗？(输入名字/换一批/我指定)")
        
        if choice in breeds:
            return choice
        elif choice == "换一批":
            print("[小桃] 好的呀，我再帮你找找看！")
            continue
        else: # 用户直接指定
            return choice

# --- 步骤2：话题挖掘 --- #
def step2_topic_selection(breed):
    while True:
        process = subprocess.run(["python3", os.path.join(SKILL_DIR, "utils/topic_mining.py"), breed], capture_output=True, text=True, encoding='utf-8')
        all_topics = json.loads(process.stdout)
        
        print("\n[小桃] 🍑 关于‘" + breed + "’，大家最关心这些点哦：")
        for i, (topic, summary) in enumerate(all_topics.items(), 1):
            print(f"  {i}. {topic}: {summary}")
        
        choice = get_user_confirmation("宝宝想先看哪些科普图呀？(输入编号，用逗号隔开，比如‘1,3,4,6’，或回复‘全都要’/‘我自己加’)")

        if choice.lower() == '全都要':
            return all_topics
        elif choice.lower() == '我自己加':
            # 此处应有更复杂的逻辑让用户添加，为演示简化
            print("[小桃] 好的呀，那我们还是按默认的来哦~")
            return all_topics
        else:
            selected_indices = [int(x.strip()) - 1 for x in choice.split(',')]
            selected_topics = {list(all_topics.keys())[i]: list(all_topics.values())[i] for i in selected_indices}
            return selected_topics

# --- 步骤3：图片生成 --- #
def step3_image_generation(pet_category, breed, topics):
    generated_images = []
    # 读取模板
    cover_prompt_template = subprocess.run(["python3", os.path.join(SKILL_DIR, "utils/image_generation.py"), "read_template", os.path.join(SKILL_DIR, 'prompts/cover_prompt.txt')], capture_output=True, text=True).stdout
    content_prompt_template = subprocess.run(["python3", os.path.join(SKILL_DIR, "utils/image_generation.py"), "read_template", os.path.join(SKILL_DIR, 'prompts/content_prompt.txt')], capture_output=True, text=True).stdout
    cover_prompt_template = json.loads(cover_prompt_template)['template']
    content_prompt_template = json.loads(content_prompt_template)['template']
    
    # 生成封面图
    while True:
        # 核心代码：拼接封面图Prompt
        cover_prompt = cover_prompt_template.format(pet_category=pet_category, pet_breed=breed, pet_breed_fullname=breed) # 此处可进一步丰富
        print("\n[小桃] 正在为你生成封面图...✨")
        process = subprocess.run(["python3", os.path.join(SKILL_DIR, "utils/image_generation.py"), "generate", cover_prompt, IMAGE_GENERATOR_SCRIPT], capture_output=True, text=True)
        image_url = json.loads(process.stdout)['url']
        
        choice = get_user_confirmation(f"封面图画好啦！快看看喜不喜欢？(图片URL: {image_url}) (回复‘满意’/或提出修改要求，比如‘特征标注改短’)")
        if choice.lower() == '满意':
            generated_images.append(image_url)
            break
        else:
            # 迭代逻辑：根据用户反馈调整Prompt，此处简化为重新生成
            print(f"[小桃] 收到宝宝的指示‘{choice}’！我让画师重新画一张哦！")
            continue
            
    # 生成内容图
    for topic, summary in topics.items():
        while True:
            # 核心代码：拼接内容图Prompt
            content_prompt = content_prompt_template.format(pet_breed=breed, topic=f"{topic}: {summary}")
            print(f"\n[小桃] 正在为你生成关于‘{topic}’的科普图...🎨")
            process = subprocess.run(["python3", os.path.join(SKILL_DIR, "utils/image_generation.py"), "generate", content_prompt, IMAGE_GENERATOR_SCRIPT], capture_output=True, text=True)
            image_url = json.loads(process.stdout)['url']
            
            choice = get_user_confirmation(f"‘{topic}’的图画好啦！(图片URL: {image_url}) (回复‘满意’/或提出修改要求，比如‘换淡紫色底色’)")
            if choice.lower() == '满意':
                generated_images.append(image_url)
                break
            else:
                print(f"[小桃] 收到宝宝的指示‘{choice}’！我这就让画师改！")
                continue
                
    return generated_images

# --- 主流程 --- #
def run_skill():
    category = get_user_confirmation("宝宝，今天想了解哪一类小可爱呀？(比如 猫/狗/爬宠/异宠)")
    
    # 步骤1
    selected_breed = step1_breed_selection(category)
    print(f"[小桃] 太棒啦！我们就来深入了解一下‘{selected_breed}’！")
    
    # 步骤2
    selected_topics = step2_topic_selection(selected_breed)
    print(f"[小桃] 收到！我们将围绕这{len(selected_topics)}个点来创作图片。")
    
    # 步骤3
    final_images = step3_image_generation(category, selected_breed, selected_topics)
    
    print("\n[小桃] 任务完成！🎉 这是为你生成的全套‘" + selected_breed + "’科普图，请查收：")
    for url in final_images:
        print(url)

if __name__ == "__main__":
    run_skill()
