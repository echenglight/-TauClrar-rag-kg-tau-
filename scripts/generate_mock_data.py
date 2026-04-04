"""生成 TauClear 平台的 Mock 图谱数据。

用法：
    python scripts/generate_mock_data.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    source_file = project_root / "backend" / "data" / "mock_data.json"
    target_file = project_root / "backend" / "data" / "mock_data.generated.json"

    with source_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # 这里可扩展为规则生成，目前先做标准化复制，确保前后端开发时有稳定数据基线。
    with target_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Mock 数据已生成：{target_file}")
    print(f"节点数量：{len(data.get('nodes', []))}，关系数量：{len(data.get('edges', []))}")


if __name__ == "__main__":
    main()
