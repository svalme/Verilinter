from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest

from src.pkg.parser.types import DeclaratorNode, HierarchicalInstanceNode, ModuleDeclarationNode
from src.pkg.rules.base_rule import Rule
from src.pkg.rules.rule_runner import RuleRunner
from src.pkg.rules.rule_selection import RuleSelection
from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.vnodes.syntax_vnode import SyntaxVNode
from src.pkg.vnodes.token_vnode import TokenVNode
from src.pkg.walk.context import Context


class BaseDummyNode:
    pass


class DummyChildNode(BaseDummyNode):
    pass


class DummyOtherNode:
    pass


class MockVNode(BaseVNode):
    def __init__(self, raw: Any) -> None:
        self.raw = raw
        self.tree = Mock()

    def snippet(self) -> str:
        return ""


class TestIndexedRuleDispatch:
    def test_untargeted_rule_runs_on_any_node(self) -> None:
        calls = []

        class UniversalRule(Rule):
            code = "UNIVERSAL"

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                calls.append(vnode.raw)
                return True

        runner = RuleRunner([UniversalRule()])
        ctx = Mock(spec=Context)

        runner.check(MockVNode(DummyChildNode()), ctx)
        runner.check(MockVNode(DummyOtherNode()), ctx)

        assert len(calls) == 2

    def test_targeted_rule_only_invoked_on_matching_raw_node(self) -> None:
        targeted_calls = []
        untargeted_calls = []

        class TargetedRule(Rule):
            code = "TARGETED"
            target_node_types = (DummyChildNode,)

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                targeted_calls.append(vnode.raw)
                return True

        class UntargetedRule(Rule):
            code = "UNTARGETED"

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                untargeted_calls.append(vnode.raw)
                return False

        runner = RuleRunner([TargetedRule(), UntargetedRule()])
        ctx = Mock(spec=Context)

        node_child = MockVNode(DummyChildNode())
        node_other = MockVNode(DummyOtherNode())

        # Check on DummyOtherNode: TargetedRule must NOT even be called
        diags = runner.check(node_other, ctx)
        assert len(targeted_calls) == 0
        assert len(untargeted_calls) == 1
        assert len(diags) == 0

        # Check on DummyChildNode: TargetedRule applies and generates diagnostic
        diags = runner.check(node_child, ctx)
        assert len(targeted_calls) == 1
        assert len(untargeted_calls) == 2
        assert len(diags) == 1
        assert diags[0]["code"] == "TARGETED"

    def test_mro_inheritance_matching(self) -> None:
        calls = []

        class BaseTargetedRule(Rule):
            code = "BASE_TARGETED"
            target_node_types = (BaseDummyNode,)

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                calls.append(vnode.raw)
                return True

        runner = RuleRunner([BaseTargetedRule()])
        ctx = Mock(spec=Context)

        # DummyChildNode subclasses BaseDummyNode -> should match
        runner.check(MockVNode(DummyChildNode()), ctx)
        assert len(calls) == 1

        # DummyOtherNode does not subclass BaseDummyNode -> should not match
        runner.check(MockVNode(DummyOtherNode()), ctx)
        assert len(calls) == 1

    def test_multiple_target_node_types(self) -> None:
        calls = []

        class MultiTargetRule(Rule):
            code = "MULTI_TARGET"
            target_node_types = (DummyChildNode, DummyOtherNode)

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                calls.append(vnode.raw)
                return True

        runner = RuleRunner([MultiTargetRule()])
        ctx = Mock(spec=Context)

        runner.check(MockVNode(DummyChildNode()), ctx)
        runner.check(MockVNode(DummyOtherNode()), ctx)
        runner.check(MockVNode("unrelated_string"), ctx)

        assert len(calls) == 2

    def test_dispatch_by_vnode_type(self) -> None:
        calls = []

        class TokenOnlyRule(Rule):
            code = "TOKEN_ONLY"
            target_node_types = (TokenVNode,)

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                calls.append(vnode)
                return True

        runner = RuleRunner([TokenOnlyRule()])
        ctx = Mock(spec=Context)

        class CustomTokenVNode(TokenVNode):
            def __init__(self) -> None:
                self.raw = Mock()
                self.tree = Mock()

        class CustomSyntaxVNode(SyntaxVNode):
            def __init__(self) -> None:
                self.raw = Mock()
                self.tree = Mock()

        token_vnode = CustomTokenVNode()
        syntax_vnode = CustomSyntaxVNode()

        runner.check(token_vnode, ctx)
        assert len(calls) == 1

        runner.check(syntax_vnode, ctx)
        assert len(calls) == 1

    def test_cache_cleared_on_rule_registration(self) -> None:
        runner = RuleRunner()
        ctx = Mock(spec=Context)
        node = MockVNode(DummyChildNode())

        runner.check(node, ctx)
        assert len(runner._cache) == 1

        class NewRule(Rule):
            code = "NEW"
            target_node_types = (DummyChildNode,)

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                return True

        runner.register(NewRule)
        assert len(runner._cache) == 0  # Cleared

        diags = runner.check(node, ctx)
        assert len(runner._cache) == 1  # Re-cached
        assert len(diags) == 1
        assert diags[0]["code"] == "NEW"

    def test_runner_injectability_and_isolation(self) -> None:
        class IsolatedRule(Rule):
            code = "ISOLATED"

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                return True

        # Custom runner initialized with isolated rule
        custom_runner = RuleRunner([IsolatedRule])
        assert len(custom_runner._rules) == 1

        # Global rule_runner should not have IsolatedRule
        from src.pkg.rules.rule_runner import rule_runner

        assert not any(r.code == "ISOLATED" for r in rule_runner._rules)

    def test_for_selection_creates_pre_filtered_indexed_runner(self) -> None:
        class CatARule(Rule):
            code = "CAT_A"
            category = "cat_a"
            target_node_types = (DummyChildNode,)

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                return True

        class CatBRule(Rule):
            code = "CAT_B"
            category = "cat_b"
            target_node_types = (DummyChildNode,)

            def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
                return True

        runner = RuleRunner([CatARule(), CatBRule()])
        filtered_runner = runner.for_selection(RuleSelection(enabled_categories=frozenset({"cat_a"})))

        assert len(filtered_runner._rules) == 1
        assert filtered_runner._rules[0].code == "CAT_A"

        ctx = Mock(spec=Context)
        diags = filtered_runner.check(MockVNode(DummyChildNode()), ctx)
        assert len(diags) == 1
        assert diags[0]["code"] == "CAT_A"
