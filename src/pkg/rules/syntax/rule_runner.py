# src/pkg/rules/syntax/rule_runner.py
from typing import Any

from ...vnodes.base_vnode import BaseVNode
from ...walk.context import Context
from ..base_rule import Rule
from ..rule_selection import RuleSelection


class RuleRunner:
    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def register(self, rule_cls: type[Rule]) -> type[Rule]:
        self._rules.append(rule_cls())
        return rule_cls

    def _selected_rules(self, selection: RuleSelection | None) -> list[Rule]:
        if selection is None:
            return self._rules
        return [rule for rule in self._rules if selection.allows(rule)]

    def check(
        self,
        vnode: BaseVNode,
        ctx: Context,
        selection: RuleSelection | None = None,
    ) -> list[dict[str, Any]]:
        return [rule.report(vnode) for rule in self._selected_rules(selection) if rule.applies(vnode, ctx)]

    def run(
        self,
        walk_results: list[tuple[BaseVNode, Context]],
        selection: RuleSelection | None = None,
    ) -> list[dict[str, Any]]:
        diagnostics: list[dict[str, Any]] = []

        for vnode, ctx in walk_results:
            diagnostics.extend(self.check(vnode, ctx, selection))

        return diagnostics


rule_runner = RuleRunner()
