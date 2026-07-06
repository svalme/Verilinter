# src/pkg/rules/syntax/rule_runner.py

from typing import Any
from ..base_rule import Rule

class RuleRunner:
    def __init__(self):
        self._rules: list[Rule] = []

    def register(self, rule_cls):
        self._rules.append(rule_cls())
        return rule_cls

    def check(self, vnode, ctx) -> list[dict[str, Any]]:
        return [rule.report(vnode) for rule in self._rules if rule.applies(vnode, ctx)]

    def run(self, walk_results: list[tuple]) -> list[dict[str, Any]]:
        diagnostics = []

        for vnode, ctx in walk_results:
            diagnostics.extend(self.check(vnode, ctx))

        return diagnostics

rule_runner = RuleRunner()
