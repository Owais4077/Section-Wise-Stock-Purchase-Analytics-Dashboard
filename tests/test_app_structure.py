import ast
from pathlib import Path


def test_every_plotly_chart_has_a_unique_explicit_key():
    tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "plotly_chart"
    ]
    keys = [
        next((keyword.value.value for keyword in call.keywords if keyword.arg == "key" and isinstance(keyword.value, ast.Constant)), None)
        for call in calls
    ]

    assert calls
    assert all(keys)
    assert len(keys) == len(set(keys))
