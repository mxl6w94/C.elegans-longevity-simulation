import ast

from fluxworm.constraints.gpr_scoring import evaluate_gpr_score


def _parse(expr: str) -> ast.AST:
    return ast.parse(expr, mode="eval").body


def test_and_takes_min():
    body = _parse("a and b")
    assert evaluate_gpr_score(body, {"a": 2.0, "b": 0.5}) == 0.5


def test_or_takes_max():
    body = _parse("a or b")
    assert evaluate_gpr_score(body, {"a": 2.0, "b": 0.5}) == 2.0


def test_missing_gene_defaults_to_neutral_score():
    body = _parse("a")
    assert evaluate_gpr_score(body, {}) == 1.0


def test_none_body_returns_none():
    assert evaluate_gpr_score(None, {"a": 2.0}) is None


def test_nested_boolop():
    body = _parse("(a and b) or c")
    assert evaluate_gpr_score(body, {"a": 4.0, "b": 2.0, "c": 0.1}) == 2.0
