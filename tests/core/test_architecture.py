"""아키텍처 제약 테스트 -- TC-154."""

import ast
import os

import pytest


class TestArchitecture:
    """TC-154: app/core/ 내에 PyQt6 import가 없어야 합니다."""

    def test_tc154_core_no_pyqt6_import(self):
        core_dir = os.path.join(os.path.dirname(__file__), "..", "..", "app", "core")
        core_dir = os.path.normpath(core_dir)

        violations = []
        for root, dirs, files in os.walk(core_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read())
                    except SyntaxError:
                        continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if "PyQt6" in alias.name:
                                violations.append(f"{fpath}:{node.lineno} -- import {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "PyQt6" in node.module:
                            violations.append(f"{fpath}:{node.lineno} -- from {node.module}")

        assert violations == [], f"Core에 PyQt6 의존 발견:\n" + "\n".join(violations)
