# 前提
1. python环境
2. pip install fonttools brotli zopfli

# 步骤
1. 执行deepseek_freq.py生成通用文字频率表（有的话忽略）
2. 执行命令python font_splitter.py --input AlibabaPuHuiTi-3-55-Regular.ttf --freq frequency.txt --groups 80 --output-dir subsets --css result.css

# 注意 实际使用时需修改result.css中的文件路径
