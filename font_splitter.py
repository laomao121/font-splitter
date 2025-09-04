#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里巴巴普惠体字体子集化脚本
将TTF字体按字符使用频率拆分为多个WOFF2子集文件
"""

import os
import argparse
import math
from fontTools.ttLib import TTFont
from fontTools.subset import main as subset_main
import subprocess
import sys
import unicodedata

def load_frequency_data(freq_file_path):
    """
    加载字符频率数据文件
    格式要求：每行一个字符和频率，用制表符或逗号分隔，如"的\t5000"或"的,5000"
    """
    char_freq = {}
    with open(freq_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # 支持制表符或逗号分隔
            if '\t' in line:
                parts = line.split('\t')
            else:
                parts = line.split(',')
                
            if len(parts) < 2:
                print(f"警告: 第{line_num}行格式不正确: {line}")
                continue
                
            char = parts[0]
            try:
                freq = int(parts[1])
                char_freq[char] = freq
            except ValueError:
                print(f"警告: 第{line_num}行频率值无效: {parts[1]}")
                continue
                
    return char_freq

def get_chars_from_font(font_path):
    """从字体文件中提取所有字符，过滤掉非法字符"""
    font = TTFont(font_path)
    chars = set()
    for table in font['cmap'].tables:
        for code_point in table.cmap.keys():
            try:
                char = chr(code_point)
                # 跳过空字符和控制字符
                if char == '\x00' or unicodedata.category(char).startswith('C'):
                    continue
                chars.add(char)
            except ValueError:
                continue
    font.close()
    return sorted(list(chars))

def create_unicode_range(codes):
    """创建unicode-range值"""
    if not codes:
        return ""
        
    codes.sort()
    ranges = []
    start = codes[0]
    end = start
    
    for code in codes[1:]:
        if code == end + 1:
            end = code
        else:
            if start == end:
                ranges.append(f"U+{start:04X}")
            else:
                ranges.append(f"U+{start:04X}-{end:04X}")
            start = code
            end = code
            
    if start == end:
        ranges.append(f"U+{start:04X}")
    else:
        ranges.append(f"U+{start:04X}-{end:04X}")
        
    return ", ".join(ranges)

def main():
    parser = argparse.ArgumentParser(description='字体子集化脚本：按频率拆分TTF字体为WOFF2子集')
    parser.add_argument('--input', '-i', default='AlibabaPuHuiTi-3-55-Regular.ttf', 
                       help='输入TTF字体文件路径')
    parser.add_argument('--freq', '-f', required=True, 
                       help='字符频率文件路径（字符和频率的映射）')
    parser.add_argument('--output-dir', '-o', default='subsets', 
                       help='输出目录')
    parser.add_argument('--groups', '-g', type=int, default=80, 
                       help='要生成的子集数量')
    parser.add_argument('--css', '-c', default='result.css', 
                       help='输出的CSS文件路径')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.isfile(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        sys.exit(1)
        
    if not os.path.isfile(args.freq):
        print(f"错误: 频率文件不存在: {args.freq}")
        sys.exit(1)
    
    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("步骤1: 加载字符频率数据...")
    freq_data = load_frequency_data(args.freq)
    
    print("步骤2: 从字体文件中提取所有字符...")
    all_chars = get_chars_from_font(args.input)
    print(f"字体中包含 {len(all_chars)} 个字符")
    
    print("步骤3: 按频率排序字符...")
    # 为字体中存在的字符创建频率列表
    char_freq_list = []
    for char in all_chars:
        freq = freq_data.get(char, 0)
        char_freq_list.append((char, freq))
    
    # 按频率降序排序
    char_freq_list.sort(key=lambda x: x[1], reverse=True)
    
    print("步骤4: 创建字符组...")
    # 将字符分成指定数量的组
    total_chars = len(char_freq_list)
    groups = []
    
    for i in range(args.groups):
        start = i * total_chars // args.groups
        end = (i + 1) * total_chars // args.groups
        group_chars = [char for char, freq in char_freq_list[start:end]]
        groups.append(group_chars)
    
    print("步骤5: 生成子集字体文件...")
    css_rules = []
    
    for i, group in enumerate(groups):
        if not group:
            continue
            
        subset_filename = f"AlibabaPuHuiTi-subset-{i:03d}.woff2"
        subset_path = os.path.join(args.output_dir, subset_filename)
        
        # 将字符组转换为文本
        text = "".join(group)
        
        # 使用pyftsubset生成子集
        try:
            # 方法1: 使用subprocess调用pyftsubset
            cmd = [
                'pyftsubset', args.input,
                f"--text={text}",
                f"--output-file={subset_path}",
                "--flavor=woff2",
                "--with-zopfli",
                "--desubroutinize",
                "--hinting-tables=*"
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 方法2: 使用API（备选）
            # subset_main([
            #     args.input,
            #     f"--text={text}",
            #     f"--output-file={subset_path}",
            #     "--flavor=woff2",
            #     "--with-zopfli",
            #     "--desubroutinize",
            #     "--hinting-tables=*"
            # ])
            
            # 获取文件大小
            file_size = os.path.getsize(subset_path) / 1024
            print(f"  子集 {i:03d}: {len(group)} 个字符, 文件大小: {file_size:.2f} KB")
            
            # 准备CSS规则
            codes = [ord(char) for char in group]
            unicode_range = create_unicode_range(codes)
            
            css_rule = f"""@font-face {{
  font-family: "Alibaba PuHuiTi 3.0";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("{os.path.join(args.output_dir, subset_filename)}") format("woff2");
  unicode-range: {unicode_range};
}}"""
            
            css_rules.append(css_rule)
            
        except (subprocess.CalledProcessError, Exception) as e:
            print(f"错误: 生成子集 {i} 失败: {e}")
            continue
    
    print("步骤6: 生成CSS文件...")
    with open(args.css, 'w', encoding='utf-8') as css_file:
        css_file.write("/* 阿里巴巴普惠体 3.0 子集化字体 */\n")
        css_file.write("/* 生成于: 2025-09-04 */\n")
        css_file.write("/* 包含 {} 个子集 */\n\n".format(len(css_rules)))
        css_file.write("\n\n".join(css_rules))
    
    print(f"完成! 生成了 {len(css_rules)} 个子集文件")
    print(f"CSS文件已保存至: {args.css}")

if __name__ == "__main__":
    main()