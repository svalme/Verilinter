from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ...parser.syntax import (
    evaluate_constant_expression,
    is_named_parameter_override,
    is_ordered_parameter_override,
    named_parameter_override_name,
    node_location,
    parameter_override_expression,
    parameter_override_list,
    source_text_for_node,
)
from ...semantic.models import ParameterOverride

if TYPE_CHECKING:
    from ...semantic.scope import Scope


class ParameterOverrideExtractor:
    """Extracts typed parameter override records and style from an instantiation syntax node."""

    def __init__(
        self,
        evaluator: Callable[..., Any] | None = None,
    ) -> None:
        self.evaluator = evaluator if evaluator is not None else evaluate_constant_expression

    def extract(
        self,
        raw_node: Any,
        tree: Any,
        scope: Scope | None = None,
    ) -> tuple[list[ParameterOverride], str]:
        parameter_overrides: list[ParameterOverride] = []
        parameter_override_kinds: set[str] = set()

        for param in parameter_override_list(raw_node):
            expr = parameter_override_expression(param)
            expr_text = source_text_for_node(expr, tree) if expr is not None else None
            expr_value = self.evaluator(expr, scope=scope) if expr is not None else None

            if is_named_parameter_override(param):
                parameter_overrides.append(
                    ParameterOverride(
                        kind="named",
                        param_name=named_parameter_override_name(param),
                        location=node_location(param, tree),
                        expr_text=expr_text,
                        expr_value=expr_value,
                    )
                )
                parameter_override_kinds.add("named")
            elif is_ordered_parameter_override(param):
                parameter_overrides.append(
                    ParameterOverride(
                        kind="ordered",
                        location=node_location(param, tree),
                        expr_text=expr_text,
                        expr_value=expr_value,
                    )
                )
                parameter_override_kinds.add("ordered")

        parameter_override_style = (
            "mixed"
            if len(parameter_override_kinds) > 1
            else next(iter(parameter_override_kinds), "none")
        )

        return parameter_overrides, parameter_override_style
