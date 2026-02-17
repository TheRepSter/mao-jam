"""
Scans all *_strategies.py files (except all_strategies.py and my_strategies.py)
and regenerates all_strategies.py with all Strategy subclasses found.
"""

import ast
import glob
import os
import sys

EXCLUDED = {"all_strategies.py", "my_strategies.py"}
OUTPUT_FILE = "all_strategies.py"

# Base strategy classes that should not be re-imported as user strategies
BASE_CLASSES = {"Strategy", "FirstStrategy", "RandomStrategy", "BaseStrategy"}


def get_strategy_classes(filepath: str) -> list[str]:
    """Return names of classes that extend Strategy in the given file."""
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError as e:
            print(f"⚠️  Syntax error in {filepath}: {e}", file=sys.stderr)
            return []

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Include if it inherits from anything (crude but effective here)
            # Exclude if it's a known base class
            if node.name not in BASE_CLASSES and node.bases:
                classes.append(node.name)
    return classes


def module_name_from_path(filepath: str) -> str:
    """Convert a filepath like 'foo/bar_strategies.py' to 'foo.bar_strategies'."""
    module = filepath.replace(os.sep, ".").replace("/", ".")
    if module.endswith(".py"):
        module = module[:-3]
    return module


def main():
    # Find all *_strategies.py files inside the strategies/ folder
    pattern = "strategies/**/*_strategies.py"
    all_files = sorted(glob.glob(pattern, recursive=True))
    all_files = [
        f for f in all_files
        if os.path.basename(f) not in EXCLUDED
    ]

    print(f"Found {len(all_files)} strategy file(s):")
    for f in all_files:
        print(f"  - {f}")

    imports = []
    strategy_class_names = []

    for filepath in all_files:
        classes = get_strategy_classes(filepath)
        if not classes:
            print(f"  ⚠️  No strategy classes found in {filepath}, skipping.")
            continue
        module = module_name_from_path(filepath)
        imports.append(f"from {module} import {', '.join(classes)}")
        strategy_class_names.extend(classes)
        print(f"  ✅ {filepath}: {classes}")

    lines = [
        "# This file is auto-generated. Do not edit manually.",
        "# Run scripts/update_all_strategies.py to regenerate.",
        "",
        "from base.classes import FirstStrategy, RandomStrategy",
        "",
    ]

    if imports:
        lines += imports
    else:
        lines.append("# No user strategies found.")

    lines += [
        "",
        "strategies = [",
        "    FirstStrategy,",
        "    RandomStrategy,",
    ]

    for cls in strategy_class_names:
        lines.append(f"    {cls},")

    lines += [
        "]",
        "",
    ]

    output = "\n".join(lines)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n✅ '{OUTPUT_FILE}' updated with {len(strategy_class_names)} user strategy class(es).")


if __name__ == "__main__":
    main()