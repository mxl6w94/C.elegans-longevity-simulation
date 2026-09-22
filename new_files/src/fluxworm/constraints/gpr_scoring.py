"""Evaluates a reaction's Gene-Protein-Reaction (GPR) rule over continuous
gene expression scores, following the standard convention used by E-Flux
and GIMME-family methods:

    AND (enzyme complex, every subunit required) -> min(scores)
    OR  (isozymes, either one suffices)          -> max(scores)

cobrapy (>=0.29) parses each reaction's gene_reaction_rule into a `GPR`
object whose `.body` is a Python `ast` expression tree (`ast.BoolOp` /
`ast.Name`, or `None` for reactions with no gene association -- exchanges,
transport, spontaneous reactions, and the biomass reaction itself all have
`body is None` in iCEL1314). This module walks that tree directly; cobrapy's
own public API only evaluates GPRs to booleans (for knockouts), not to a
continuous score, so a small custom evaluator is necessary here.

A gene absent from the provided score dict (no expression evidence, or not
represented on the array) is treated as score 1.0 -- neutral, i.e. it does
not pull an AND-complex's score down nor unfairly inflate an OR-group's
score. This is a deliberate choice: absence of evidence is not evidence of
knockdown.
"""

from __future__ import annotations

import ast

import cobra


def evaluate_gpr_score(gpr_body: ast.AST | None, gene_scores: dict[str, float]) -> float | None:
    """Return the reaction-level score for a GPR AST node, or None if the
    reaction has no gene association at all (gpr_body is None) -- callers
    must treat None as "leave this reaction's bounds unscaled", not as a
    score of any particular value.
    """
    if gpr_body is None:
        return None
    return _eval_node(gpr_body, gene_scores)


def _eval_node(node: ast.AST, gene_scores: dict[str, float]) -> float:
    if isinstance(node, ast.Name):
        return gene_scores.get(node.id, 1.0)
    if isinstance(node, ast.BoolOp):
        child_scores = [_eval_node(child, gene_scores) for child in node.values]
        if isinstance(node.op, ast.And):
            return min(child_scores)
        if isinstance(node.op, ast.Or):
            return max(child_scores)
        raise TypeError(f"Unexpected boolean operator in GPR: {node.op}")
    raise TypeError(f"Unexpected GPR AST node type: {type(node)}")


def score_all_reactions(model: cobra.Model, gene_scores: dict[str, float]) -> dict[str, float | None]:
    """Return {reaction_id: score_or_None} for every reaction in the model."""
    return {rxn.id: evaluate_gpr_score(rxn.gpr.body, gene_scores) for rxn in model.reactions}
