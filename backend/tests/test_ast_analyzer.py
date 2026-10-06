"""AST analyzer tests."""

import pytest
from app.analyzers.ast_analyzer import ASTAnalyzer


@pytest.fixture
def analyzer():
    return ASTAnalyzer()


SAMPLE_CODE = '''
import os
from pathlib import Path

class DataProcessor:
    """Processes data files."""

    def __init__(self, path):
        self.path = path

    def process(self, data, validate=True):
        """Process the data."""
        if validate:
            if not data:
                raise ValueError("Empty data")
        try:
            result = []
            for item in data:
                if item > 0:
                    result.append(item * 2)
                elif item == 0:
                    result.append(0)
                else:
                    result.append(abs(item))
            return result
        except TypeError:
            return []

def helper_function(x, y, z, a, b, c):
    return x + y + z + a + b + c
'''


def test_analyze_source(analyzer):
    """Analyzes Python source and extracts structure."""
    result = analyzer.analyze_source(SAMPLE_CODE, "test.py")
    assert result.total_lines > 0
    assert result.code_lines > 0


def test_extract_imports(analyzer):
    """Extracts imports from source."""
    result = analyzer.analyze_source(SAMPLE_CODE, "test.py")
    assert "os" in result.imports
    assert any("Path" in imp for imp in result.imports)


def test_extract_classes(analyzer):
    """Extracts class definitions."""
    result = analyzer.analyze_source(SAMPLE_CODE, "test.py")
    assert len(result.classes) == 1
    assert result.classes[0].name == "DataProcessor"
    assert "process" in result.classes[0].methods
    assert "__init__" in result.classes[0].methods


def test_extract_functions(analyzer):
    """Extracts functions with metrics."""
    result = analyzer.analyze_source(SAMPLE_CODE, "test.py")
    assert len(result.functions) >= 3  # __init__, process, helper_function

    # Find the process function
    process_func = next(f for f in result.functions if f.name == "process")
    assert process_func.complexity > 1  # Has branching
    assert process_func.has_error_handling is True
    assert process_func.has_docstring is True


def test_complexity_calculation(analyzer):
    """Complexity increases with branching."""
    simple = 'def f():\n    return 1\n'
    complex_code = '''
def f(x):
    if x > 0:
        if x > 10:
            for i in range(x):
                if i % 2 == 0:
                    pass
    elif x == 0:
        pass
    else:
        try:
            pass
        except:
            pass
'''
    r1 = analyzer.analyze_source(simple, "simple.py")
    r2 = analyzer.analyze_source(complex_code, "complex.py")

    assert r2.max_complexity > r1.max_complexity


def test_code_smells(analyzer):
    """Detects code smells."""
    result = analyzer.analyze_source(SAMPLE_CODE, "test.py")
    helper = next(f for f in result.functions if f.name == "helper_function")
    assert any("Too many parameters" in s for s in helper.code_smells)


def test_nesting_depth(analyzer):
    """Calculates nesting depth."""
    result = analyzer.analyze_source(SAMPLE_CODE, "test.py")
    process_func = next(f for f in result.functions if f.name == "process")
    assert process_func.nested_depth >= 2


def test_syntax_error_handling(analyzer):
    """Handles syntax errors gracefully."""
    result = analyzer.analyze_source("def broken(:\n    pass", "broken.py")
    assert result.total_lines > 0
    assert result.functions == []


def test_bare_except_detection(analyzer):
    """Detects bare except clauses."""
    code = '''
def risky():
    try:
        pass
    except:
        pass
'''
    result = analyzer.analyze_source(code, "risky.py")
    func = result.functions[0]
    assert any("Bare except" in s for s in func.code_smells)
