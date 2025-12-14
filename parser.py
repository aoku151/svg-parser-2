import sys
import re
from lxml import etree
from svgpathtools import parse_path

SVG_NS = "http://www.w3.org/2000/svg"

def normalize_svg(input_file: str, output_file: str) -> None:
    # SVG を読み込む
    tree = etree.parse(input_file)
    root = tree.getroot()

    # 全 path の座標範囲を計算
    min_x, min_y = float("inf"), float("inf")
    max_x, max_y = float("-inf"), float("-inf")
    paths = list(root.iter(f"{{{SVG_NS}}}path"))

    if not paths:
        # path がない場合はそのまま書き出し（rotationCenter コメントだけ削除）
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        _remove_rotation_center_comment_in_file(output_file)
        return

    for elem in paths:
        d = elem.attrib.get("d")
        if not d:
            continue
        path = parse_path(d)
        # 始点・終点だけだとベジェの中間が考慮されない場合があるが、最低限の範囲計算として扱う
        for seg in path:
            for pt in (seg.start, seg.end):
                x, y = pt.real, pt.imag
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    # 何らかの理由で範囲が取れなかった場合のガード
    if not all(map(_is_finite, (min_x, min_y, max_x, max_y))):
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        _remove_rotation_center_comment_in_file(output_file)
        return

    # 座標を最小値基準で原点に合わせる
    dx, dy = -min_x, -min_y
    for elem in paths:
        d = elem.attrib.get("d")
        if not d:
            continue
        path = parse_path(d)
        path = path.translated(complex(dx, dy))
        elem.attrib["d"] = path.d()

    # viewBox・width・height を更新（px 単位などは付けず数値で）
    width = max_x - min_x
    height = max_y - min_y
    root.attrib["viewBox"] = f"0 0 {width} {height}"
    root.attrib["width"] = _to_plain_number_str(root.attrib.get("width"), width)
    root.attrib["height"] = _to_plain_number_str(root.attrib.get("height"), height)

    # g 要素の transform を削除
    for g in root.iter(f"{{{SVG_NS}}}g"):
        if "transform" in g.attrib:
            del g.attrib["transform"]

    # 出力
    tree.write(output_file, encoding="utf-8", xml_declaration=True)

    # rotationCenter コメントを削除（ファイル全体から安全に削除）
    _remove_rotation_center_comment_in_file(output_file)


def _remove_rotation_center_comment_in_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # 1 行でも複数行でも安全に削除
    content = re.sub(r"<!--\s*rotationCenter[^>]*?-->", "", content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _to_plain_number_str(original: str | None, fallback: float) -> str:
    # 既存の width/height に単位が付いていても数値のみへ（例: "100px" -> "100"）
    if original is None:
        return str(fallback)
    m = re.match(r"^\s*([0-9]*\.?[0-9]+)", original)
    if m:
        return m.group(1)
    return str(fallback)


def _is_finite(v: float) -> bool:
    return v == v and v not in (float("inf"), float("-inf"))


# if __name__ == "__main__":
#     # 引数: input.svg output.svg
#     if len(sys.argv) < 3:
#         print("Usage: python normalize_svg.py <input.svg> <output.svg>")
#         sys.exit(1)
#
#     input_path = sys.argv[1]
#     output_path = sys.argv[2]
# 
#     try:
#         normalize_svg(input_path, output_path)
#         print(f"Normalized: {input_path} -> {output_path}")
#     except Exception as e:
#         print(f"Error: {e}")
#         sys.exit(2)
