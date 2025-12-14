import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor
from parser import normalize_svg  # parser.py の関数を利用

results = {"success": [], "fail": []}

def process_file(input_path: str, output_dir: str):
    filename = os.path.basename(input_path)
    output_path = os.path.join(output_dir, filename)
    try:
        normalize_svg(input_path, output_path)
        results["success"].append(filename)
        print(f"✅ Normalized: {filename}")
    except Exception as e:
        results["fail"].append({"file": filename, "error": str(e)})
        print(f"❌ Error in {filename}: {e}")

def main(file_list, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(lambda f: process_file(f, output_dir), file_list)

    # 成功/失敗一覧を保存
    with open("summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python main.py <input1.svg> <input2.svg> ... <output_dir>")
        sys.exit(1)

    *files, output_dir = sys.argv[1:]
    main(files, output_dir)
