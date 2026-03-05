#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
import subprocess

def generate_image(prompt, generator_script_path):
    """
    调用真正的生图Skill的run.sh脚本生成图片。
    """
    print(f"收到生图任务，正在调用真正的画师小精灵...\nPrompt: {prompt}", file=sys.stderr)
    
    try:
        # 真正执行生图脚本，并设置超时
        command = [generator_script_path, prompt]
        process = subprocess.run(command, capture_output=True, text=True, timeout=90, check=True)
        
        # 从返回的JSON结果中解析出图片URL
        output = json.loads(process.stdout)
        image_url = output['data']['imageGenResultDTOList'][0]['url']
        
        print(f"图片生成成功！URL: {image_url}", file=sys.stderr)
        return image_url
    except subprocess.TimeoutExpired:
        print("错误：生图任务超时了！QAQ", file=sys.stderr)
        return "error_timeout"
    except (json.JSONDecodeError, KeyError, IndexError, subprocess.CalledProcessError) as e:
        print(f"错误：解析生图结果失败: {e}", file=sys.stderr)
        # 在出错时返回一个不会被误认为是有效链接的错误标识
        return "error_parsing_failed"

def read_prompt_template(file_path):
    """
    从指定路径读取prompt模板文件内容。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

if __name__ == "__main__":
    action = sys.argv[1]
    
    if action == "generate":
        prompt_text = sys.argv[2]
        script_path = sys.argv[3]
        result_url = generate_image(prompt_text, script_path)
        print(json.dumps({"url": result_url}))
        
    elif action == "read_template":
        template_path = sys.argv[2]
        template_content = read_prompt_template(template_path)
        print(json.dumps({"template": template_content}))
