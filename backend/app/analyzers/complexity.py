"""Cyclomatic complexity calculator — standalone utility used by analyzers."""

from __future__ import annotations

import ast
import logging

logger = logging.getLogger(__name__)


class ComplexityCalculator:
    """Calculate code complexity metrics for Python source."""

    @staticmethod
    def file_complexity(source: str) -> dict:
        """
        Calculate overall complexity metrics for a Python source string.
        Returns dict with avg_complexity, max_complexity, total_functions, etc.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return {"avg_complexity": 0.0, "max_complexity": 0.0, "total_functions": 0}

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cc = ComplexityCalculator._cyclomatic(node)
                functions.append({"name": node.name, "complexity": cc, "line": node.lineno})

        if not functions:
            return {"avg_complexity": 0.0, "max_complexity": 0.0, "total_functions": 0}

        complexities = [f["complexity"] for f in functions]
        return {
            "avg_complexity": sum(complexities) / len(complexities),
            "max_complexity": max(complexities),
            "total_functions": len(functions),
            "functions": functions,
        }

    @staticmethod
    def compare_complexity(source_before: str, source_after: str) -> dict:
        """
        Compare complexity between two versions of a file.
        Returns a delta dict showing what changed.
        """
        before = ComplexityCalculator.file_complexity(source_before)
        after = ComplexityCalculator.file_complexity(source_after)

        return {
            "avg_complexity_before": before["avg_complexity"],
            "avg_complexity_after": after["avg_complexity"],
            "max_complexity_before": before["max_complexity"],
            "max_complexity_after": after["max_complexity"],
            "complexity_delta": after["avg_complexity"] - before["avg_complexity"],
            "functions_before": before["total_functions"],
            "functions_after": after["total_functions"],
            "increased": after["avg_complexity"] > before["avg_complexity"],
        }

    @staticmethod
    def _cyclomatic(node: ast.AST) -> int:
        """Cyclomatic complexity of a single AST node."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.IfExp)):
                complexity += 1
            elif isinstance(child, ast.For):
                complexity += 1
            elif isinstance(child, ast.While):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
