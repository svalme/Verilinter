# src/pkg/rules/rule_runner.py
from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from ..vnodes.base_vnode import BaseVNode
from ..walk.context import Context
from .base_rule import Rule
from .rule_selection import RuleSelection


class RuleRunner:
    """Orchestrates checking syntax AST rules against walked nodes.

    Supports indexing rules by AST target node type (`dict[type, list[Rule]]`)
    with inheritance (MRO) traversal and lookup caching, replacing the linear
    scan with fast indexed dispatch. Also supports runner injectability with
    explicit rule lists.
    """

    def __init__(self, rules: Sequence[Rule | type[Rule]] | None = None) -> None:
        self._rules: list[Rule] = []
        self._untargeted_rules: list[Rule] = []
        self._indexed_rules: dict[type, list[Rule]] = defaultdict(list)
        self._cache: dict[tuple[type, type], list[Rule]] = {}
        if rules is not None:
            for item in rules:
                if isinstance(item, type):
                    self.register(item)
                else:
                    self.add_rule(item)

    def add_rule(self, rule: Rule) -> None:
        self._rules.append(rule)
        targets = getattr(rule, "target_node_types", None)
        if targets:
            for target_type in targets:
                self._indexed_rules[target_type].append(rule)
        else:
            self._untargeted_rules.append(rule)
        self._cache.clear()

    def register(self, rule_cls: type[Rule]) -> type[Rule]:
        rule = rule_cls()
        self.add_rule(rule)
        return rule_cls

    def _selected_rules(self, selection: RuleSelection | None) -> list[Rule]:
        if selection is None:
            return self._rules
        return [rule for rule in self._rules if selection.allows(rule)]

    def _get_applicable_rules(
        self,
        vnode: BaseVNode,
        selection: RuleSelection | None = None,
    ) -> list[Rule]:
        raw_type = type(getattr(vnode, "raw", None))
        vnode_type = type(vnode)
        key = (selection, raw_type, vnode_type)

        cached = self._cache.get(key)
        if cached is not None:
            return cached

        applicable: list[Rule] = [
            r for r in self._untargeted_rules
            if selection is None or selection.allows(r)
        ]
        seen_ids: set[int] = {id(r) for r in applicable}

        # Traverse MRO of raw node (pyslang syntax node / token)
        for cls in raw_type.__mro__:
            if cls in self._indexed_rules:
                for rule in self._indexed_rules[cls]:
                    if id(rule) not in seen_ids and (selection is None or selection.allows(rule)):
                        applicable.append(rule)
                        seen_ids.add(id(rule))

        # Traverse MRO of wrapper vnode (SyntaxVNode, TokenVNode, IdentifierVNode, etc.)
        for cls in vnode_type.__mro__:
            if cls in self._indexed_rules:
                for rule in self._indexed_rules[cls]:
                    if id(rule) not in seen_ids and (selection is None or selection.allows(rule)):
                        applicable.append(rule)
                        seen_ids.add(id(rule))

        self._cache[key] = applicable
        return applicable

    def check(
        self,
        vnode: BaseVNode,
        ctx: Context,
        selection: RuleSelection | None = None,
    ) -> list[dict[str, Any]]:
        candidate_rules = self._get_applicable_rules(vnode, selection)
        return [rule.report(vnode) for rule in candidate_rules if rule.applies(vnode, ctx)]

    def for_selection(self, selection: RuleSelection | None) -> RuleRunner:
        if selection is None:
            return self
        filtered_rules = [r for r in self._rules if selection.allows(r)]
        return RuleRunner(filtered_rules)

    def run(
        self,
        walk_results: list[tuple[BaseVNode, Context]],
        selection: RuleSelection | None = None,
    ) -> list[dict[str, Any]]:
        runner = self.for_selection(selection)
        diagnostics: list[dict[str, Any]] = []

        for vnode, ctx in walk_results:
            diagnostics.extend(runner.check(vnode, ctx))

        return diagnostics


rule_runner = RuleRunner()
