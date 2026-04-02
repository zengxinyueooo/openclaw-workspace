#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os

# 画布尺寸
W, H = 1080, 1440
BG_COLOR = (250, 248, 245)  # 米白背景
DARK = (30, 30, 30)
ACCENT = (80, 80, 80)
ARROW_COLOR = (40, 40, 40)

canvas = Image.new("RGB", (W, H), BG_COLOR)
draw = ImageDraw.Draw(canvas)

# 字体
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FONT_REG  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

font_title   = ImageFont.truetype(FONT_BOLD, 58)
font_sub     = ImageFont.truetype(FONT_BOLD, 38)
font_breed   = ImageFont.truetype(FONT_BOLD, 64)
font_breed_en= ImageFont.truetype(FONT_REG,  36)
font_label   = ImageFont.truetype(FONT_REG,  26)

# ── 顶部装饰条 ──
draw.rectangle([0, 0, W, 10], fill=(180, 160, 140))

# ── 顶部标题 ──
title = "每周认识一种猫"
bb = draw.textbbox((0,0), title, font=font_title)
tw = bb[2] - bb[0]
draw.text(((W-tw)//2, 40), title, fill=DARK, font=font_title)

# 细线分隔
draw.line([(80, 120), (W-80, 120)], fill=(200,190,180), width=2)

# ── 猫咪图（主体，居中放大） ──
cat = Image.open("/root/.openclaw/workspace/cat_only.png").convert("RGBA")
cat_w, cat_h = cat.size
# 目标高度 720px
target_h = 720
scale = target_h / cat_h
target_w = int(cat_w * scale)
cat = cat.resize((target_w, target_h), Image.LANCZOS)

# 白底合并（去除透明）
cat_bg = Image.new("RGB", (target_w, target_h), BG_COLOR)
cat_bg.paste(cat, (0,0), mask=cat.split()[3])

# 居中粘贴，y从140开始
cat_x = (W - target_w) // 2
cat_y = 145
canvas.paste(cat_bg, (cat_x, cat_y))

# ── 箭头标注 ──
# 标注点 (相对于猫咪图的比例位置 -> 实际像素)
annotations = [
    (0.50, 0.08, "right",  "银白渐变短毛，光泽感强"),
    (0.85, 0.30, "right",  "绿色杏仁眼，清澈有神"),
    (0.15, 0.55, "left",   "中等体型，骨架匀称优雅"),
    (0.70, 0.85, "right",  "四肢修长，步态轻盈"),
]

for (rx, ry, side, label) in annotations:
    px = cat_x + int(rx * target_w)
    py = cat_y + int(ry * target_h)

    if side == "right":
        lx1, ly1 = px + 18, py
        lx2, ly2 = px + 90, py
        tx, ty = lx2 + 8, ly2 - 16
    else:
        lx1, ly1 = px - 18, py
        lx2, ly2 = px - 90, py
        tx, ty = None, ly2 - 16  # 右对齐

    # 圆点
    draw.ellipse([px-6, py-6, px+6, py+6], fill=ARROW_COLOR)
    # 线
    draw.line([(lx1,ly1),(lx2,ly2)], fill=ARROW_COLOR, width=2)
    # 箭头小三角
    if side == "right":
        draw.polygon([(lx2,ly2), (lx2-8,ly2-5), (lx2-8,ly2+5)], fill=ARROW_COLOR)
    else:
        draw.polygon([(lx2,ly2), (lx2+8,ly2-5), (lx2+8,ly2+5)], fill=ARROW_COLOR)

    # 文字
    if side == "right":
        draw.text((tx, ty), label, fill=DARK, font=font_label)
    else:
        bb2 = draw.textbbox((0,0), label, font=font_label)
        lw = bb2[2] - bb2[0]
        draw.text((lx2 - 8 - lw, ty), label, fill=DARK, font=font_label)

# ── 分隔线 ──
sep_y = cat_y + target_h + 30
draw.line([(80, sep_y), (W-80, sep_y)], fill=(200,190,180), width=2)

# ── 底部品种名 ──
breed_cn = "波米拉猫"
bb3 = draw.textbbox((0,0), breed_cn, font=font_breed)
bw = bb3[2] - bb3[0]
draw.text(((W-bw)//2, sep_y + 25), breed_cn, fill=DARK, font=font_breed)

breed_en = "Burmilla"
bb4 = draw.textbbox((0,0), breed_en, font=font_breed_en)
ew = bb4[2] - bb4[0]
draw.text(((W-ew)//2, sep_y + 100), breed_en, fill=ACCENT, font=font_breed_en)

# ── 底部装饰条 ──
draw.rectangle([0, H-10, W, H], fill=(180, 160, 140))

# 保存
out = "/root/.openclaw/workspace/pillow_cover.png"
canvas.save(out, "PNG")
print(f"saved: {out}")
