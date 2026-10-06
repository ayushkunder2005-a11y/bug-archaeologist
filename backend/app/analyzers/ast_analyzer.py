"""Python AST analyzer — extracts functions, classes, complexity, and code smells."""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """Extracted metadata about a single function/method."""
    name: str
    line_number: int
    end_line_number: int
    length_lines: int
    parameter_count: int
    complexity: int
    nested_depth: int
    has_docstring: bool
    has_error_handling: bool
    decorators: list[str] = field(default_factory=list)
    code_smells: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """Extracted metadata about a class."""
    name: str
    line_number: int
    methods: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)


@dataclass
class FileAnalysisResult:
    """Complete analysis of a single Python file."""
    file_path: str
    total_lines: int = 0
    code_lines: int = 0
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    avg_complexity: float = 0.0
    max_complexity: float = 0.0
    code_smells: list[str] = field(default_factory=list)


class ASTAnalyzer:
    """Analyzes Python source code using the ast module."""

    # ── Thresholds for code smells ──────────────────────────────
    MAX_FUNCTION_LENGTH = 50   # lines
    MAX_PARAMETERS = 5
    MAX_NESTING_DEPTH = 4
    HIGH_COMPLEXITY = 10

    def analyze_source(self, source: str, file_path: str = "<unknown>") -> FileAnalysisResult:
        """Analyze a Python source code string."""
        result = FileAnalysisResult(file_path=file_path)
        lines = source.split("\n")
        result.total_lines = len(lines)
        result.code_lines = sum(
            1 for line in lines if line.strip() and not line.strip().startswith("#")
        )

        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError as e:
            logger.warning("Syntax error in %s: %s", file_path, e)
            return result

        # Extract top-level imports
        result.imports = self._extract_imports(tree)

        # Extract classes
        result.classes = self._extract_classes(tree)

        # Extract functions (top-level + methods)
        result.functions = self._extract_functions(tree)

        # Aggregate complexity
        if result.functions:
            complexities = [f.complexity for f in result.functions]
            result.avg_complexity = sum(complexities) / len(complexities)
            result.max_complexity = max(complexities)

        # Collect code smells
        result.code_smells = self._collect_file_smells(result)

        return result

    # ── Import extraction ───────────────────────────────────────

    @staticmethod
    def _extract_imports(tree: ast.Module) -> list[str]:
        """Extract all import names."""
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports

    # ── Class extraction ────────────────────────────────────────

    @staticmethod
    def _extract_classes(tree: ast.Module) -> list[ClassInfo]:
        """Extract class definitions."""
        classes: list[ClassInfo] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(ast.dump(base))
                classes.append(ClassInfo(
                    name=node.name,
                    line_number=node.lineno,
                    methods=methods,
                    bases=bases,
                ))
        return classes

    # ── Function extraction ─────────────────────────────────────

    def _extract_functions(self, tree: ast.Module) -> list[FunctionInfo]:
        """Extract all function/method definitions with metrics."""
        functions: list[FunctionInfo] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = self._analyze_function(node)
                functions.append(func)
        return functions

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
        """Compute metrics for a single function."""
        end_line = getattr(node, "end_lineno", node.lineno)
        length = end_line - node.lineno + 1

        # Parameter count (excluding self/cls)
        args = node.args
        param_count = len(args.args) + len(args.kwonlyargs)
        if args.args and args.args[0].arg in ("self", "cls"):
            param_count -= 1

        # Complexity
        complexity = self._cyclomatic_complexity(node)

        # Nesting depth
        nested_depth = self._max_nesting_depth(node)

        # Docstring
        has_docstring = (
            isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Constant, ast.Str))
            if node.body else False
        )

        # Error handling
        has_error_handling = any(
            isinstance(n, ast.ExceptHandler) for n in ast.walk(node)
        )

        # Decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)

        # Code smells
        smells: list[str] = []
        if length > self.MAX_FUNCTION_LENGTH:
            smells.append(f"Function too long ({length} lines)")
        if param_count > self.MAX_PARAMETERS:
            smells.append(f"Too many parameters ({param_count})")
        if nested_depth > self.MAX_NESTING_DEPTH:
            smells.append(f"Deep nesting ({nested_depth} levels)")
        if complexity > self.HIGH_COMPLEXITY:
            smells.append(f"High complexity ({complexity})")
        if not has_docstring:
            smells.append("Missing docstring")

        # Bare except
        for n in ast.walk(node):
            if isinstance(n, ast.ExceptHandler) and n.type is None:
                smells.append("Bare except clause")
                break

        return FunctionInfo(
            name=node.name,
            line_number=node.lineno,
            end_line_number=end_line,
            length_lines=length,
            parameter_count=param_count,
            complexity=complexity,
            nested_depth=nested_depth,
            has_docstring=has_docstring,
            has_error_handling=has_error_handling,
            decorators=decorators,
            code_smells=smells,
        )

    # ── Cyclomatic complexity ───────────────────────────────────

    @staticmethod
    def _cyclomatic_complexity(node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity of an AST node.
        Counts decision points: if, elif, for, while, except, with,
        assert, and, or, ternary (IfExp).
        """
        complexity = 1  # Base complexity
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
                # Each 'and'/'or' adds a decision point
                complexity += len(child.values) - 1
        return complexity

    # ── Nesting depth ───────────────────────────────────────────

    @staticmethod
    def _max_nesting_depth(node: ast.AST) -> int:
        """Calculate maximum nesting depth of control structures."""
        nesting_types = (ast.If, ast.For, ast.While, ast.With, ast.Try)

        def _depth(n: ast.AST, current: int) -> int:
            max_d = current
            for child in ast.iter_child_nodes(n):
                if isinstance(child, nesting_types):
                    max_d = max(max_d, _depth(child, current + 1))
                else:
                    max_d = max(max_d, _depth(child, current))
            return max_d

        return _depth(node, 0)

    # ── File-level code smells ──────────────────────────────────

    @staticmethod
    def _collect_file_smells(result: FileAnalysisResult) -> list[str]:
        """Aggregate code smells at file level."""
        smells: list[str] = []
        if result.total_lines > 500:
            smells.append(f"Large file ({result.total_lines} lines)")
        if len(result.imports) > 20:
            smells.append(f"Too many imports ({len(result.imports)})")
        for func in result.functions:
            smells.extend(func.code_smells)
        return smells
