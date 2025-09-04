from fontTools.ttLib import TTFont

font_path = "AlibabaPuHuiTi-3-55-Regular.ttf"
font = TTFont(font_path)
chars = set()
for table in font['cmap'].tables:
    for code_point in table.cmap.keys():
        try:
            char = chr(code_point)
            chars.add(char)
        except ValueError:
            continue
font.close()

with open("freq.txt", "w", encoding="utf-8") as f:
    for char in sorted(chars):
        f.write(f"{char}\t1\n")