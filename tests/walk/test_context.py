import pytest

from src.pkg.walk.context import Context, ContextFlag
from src.pkg.vnodes.base_vnode import BaseVNode
from tests.support.fakes import fake_vnode


@pytest.fixture
def context() -> Context:
    """Fixture for a fresh Context instance."""
    return Context()


@pytest.fixture
def mock_vnode() -> BaseVNode:
    """Fixture for a mock vnode."""
    return fake_vnode(None)


class TestContext:
    """Test cases for the Context class."""

    def test_context_initializes_with_empty_stack(self, context: Context) -> None:
        """Test that Context initializes with an empty stack by default."""
        assert context.stack == []

    def test_context_initializes_with_empty_flags(self, context: Context) -> None:
        """Test that Context initializes with no flags by default."""
        assert context.flags == set()

    def test_context_can_be_initialized_with_flags(self) -> None:
        """Test that Context can be initialized with flags."""
        flags = {ContextFlag.ALWAYS}
        context = Context(flags=flags)
        
        assert context.flags == flags

    def test_push_adds_vnode_to_stack(self, context: Context, mock_vnode: BaseVNode) -> None:
        """Test that push() adds a vnode to the stack."""
        new_context = context.push(mock_vnode)
        
        assert new_context.stack == [mock_vnode]

    def test_push_preserves_existing_stack(self, context: Context, mock_vnode: BaseVNode) -> None:
        """Test that push() preserves existing stack items."""
        mock_vnode1 = fake_vnode(None)
        mock_vnode2 = fake_vnode(None)
        
        ctx = context.push(mock_vnode1)
        new_context = ctx.push(mock_vnode2)
        
        assert len(new_context.stack) == 2
        assert new_context.stack[0] == mock_vnode1
        assert new_context.stack[1] == mock_vnode2

    def test_push_preserves_flags(self, context: Context, mock_vnode: BaseVNode) -> None:
        """Test that push() preserves flags."""
        ctx = context.with_flag(ContextFlag.ALWAYS)
        new_context = ctx.push(mock_vnode)
        
        assert ContextFlag.ALWAYS in new_context.flags

    def test_push_returns_new_context(self, context: Context, mock_vnode: BaseVNode) -> None:
        """Test that push() returns a new Context instance."""
        new_context = context.push(mock_vnode)
        
        assert new_context is not context
        assert context.stack == []

    def test_with_flag_adds_flag(self, context: Context) -> None:
        """Test that with_flag() adds a flag."""
        new_context = context.with_flag(ContextFlag.ALWAYS)
        
        assert ContextFlag.ALWAYS in new_context.flags

    def test_with_flag_preserves_existing_flags(self, context: Context) -> None:
        """Test that with_flag() preserves existing flags."""
        ctx = context.with_flag(ContextFlag.ALWAYS)
        new_context = ctx.with_flag(ContextFlag.POSEDGE)
        
        assert ContextFlag.ALWAYS in new_context.flags
        assert ContextFlag.POSEDGE in new_context.flags

    def test_with_flag_preserves_stack(self, context: Context, mock_vnode: BaseVNode) -> None:
        """Test that with_flag() preserves the stack."""
        ctx = context.push(mock_vnode)
        new_context = ctx.with_flag(ContextFlag.ALWAYS)
        
        assert new_context.stack == [mock_vnode]

    def test_with_flag_returns_new_context(self, context: Context) -> None:
        """Test that with_flag() returns a new Context instance."""
        new_context = context.with_flag(ContextFlag.ALWAYS)
        
        assert new_context is not context
        assert context.flags == set()

    def test_has_returns_true_for_present_flag(self, context: Context) -> None:
        """Test that has() returns True for a flag that is set."""
        ctx = context.with_flag(ContextFlag.ALWAYS)
        
        assert ctx.has(ContextFlag.ALWAYS) is True

    def test_has_returns_false_for_absent_flag(self, context: Context) -> None:
        """Test that has() returns False for a flag that is not set."""
        assert context.has(ContextFlag.ALWAYS) is False

    def test_has_works_with_multiple_flags(self, context: Context) -> None:
        """Test that has() correctly identifies flags in a multi-flag context."""
        ctx = context.with_flag(ContextFlag.ALWAYS)
        ctx = ctx.with_flag(ContextFlag.POSEDGE)
        
        assert ctx.has(ContextFlag.ALWAYS) is True
        assert ctx.has(ContextFlag.POSEDGE) is True
        assert ctx.has(ContextFlag.NEGEDGE) is False

    def test_context_initializes_with_empty_data(self, context: Context) -> None:
        assert context.data == {}

    def test_with_data_adds_entry(self, context: Context) -> None:
        new_context = context.with_data("mix_trigger", "sentinel")

        assert new_context.data["mix_trigger"] == "sentinel"

    def test_with_data_preserves_existing_entries(self, context: Context) -> None:
        ctx = context.with_data("a", 1)
        new_context = ctx.with_data("b", 2)

        assert new_context.data == {"a": 1, "b": 2}

    def test_with_data_overwrites_same_key(self, context: Context) -> None:
        ctx = context.with_data("a", 1)
        new_context = ctx.with_data("a", 2)

        assert new_context.data == {"a": 2}

    def test_with_data_returns_new_context(self, context: Context) -> None:
        new_context = context.with_data("a", 1)

        assert new_context is not context
        assert context.data == {}

    def test_push_preserves_data(self, context: Context, mock_vnode: BaseVNode) -> None:
        ctx = context.with_data("a", 1)
        new_context = ctx.push(mock_vnode)

        assert new_context.data == {"a": 1}

    def test_data_set_after_push_does_not_leak_back_to_parent(self, context: Context, mock_vnode: BaseVNode) -> None:
        """Sibling-isolation guard: data set on a context derived from a push()
        must not be visible on the context it was pushed from, mirroring how the
        walker never lets a child's context updates leak into later siblings."""
        parent = context.push(mock_vnode)
        child = parent.with_data("a", 1)

        assert child.data == {"a": 1}
        assert parent.data == {}

    def test_with_flag_preserves_data(self, context: Context) -> None:
        ctx = context.with_data("a", 1)
        new_context = ctx.with_flag(ContextFlag.ALWAYS)

        assert new_context.data == {"a": 1}

    def test_context_chaining(self, context: Context, mock_vnode: BaseVNode) -> None:
        """Test that context operations can be chained."""
        mock_vnode1 = fake_vnode(None)
        mock_vnode2 = fake_vnode(None)
        
        ctx = context \
            .push(mock_vnode1) \
            .with_flag(ContextFlag.ALWAYS) \
            .push(mock_vnode2) \
            .with_flag(ContextFlag.POSEDGE)
        
        assert len(ctx.stack) == 2
        assert ctx.has(ContextFlag.ALWAYS)
        assert ctx.has(ContextFlag.POSEDGE)

    def test_iter_ancestors_empty_context(self, context: Context) -> None:
        assert list(context.iter_ancestors()) == []
        assert list(context.iter_ancestors(include_self=False)) == []

    def test_iter_ancestors_returns_innermost_first(self, context: Context) -> None:
        vnode1 = fake_vnode(None)
        vnode2 = fake_vnode(None)
        vnode3 = fake_vnode(None)
        ctx = context.push(vnode1).push(vnode2).push(vnode3)

        ancestors = list(ctx.iter_ancestors(include_self=True))
        assert ancestors == [vnode3, vnode2, vnode1]

        true_ancestors = list(ctx.iter_ancestors(include_self=False))
        assert true_ancestors == [vnode2, vnode1]

    def test_enclosing_returns_matching_ancestor(self, context: Context) -> None:
        vnode1 = fake_vnode(None)
        vnode2 = fake_vnode(None)
        vnode3 = fake_vnode(None)
        ctx = context.push(vnode1).push(vnode2).push(vnode3)

        found = ctx.enclosing(lambda v: v is vnode2)
        assert found is vnode2

        found_self = ctx.enclosing(lambda v: v is vnode3, include_self=True)
        assert found_self is vnode3

        not_found_self = ctx.enclosing(lambda v: v is vnode3, include_self=False)
        assert not_found_self is None

    def test_with_module_frame_populates_frame_and_backward_compatible_data(self, context: Context) -> None:
        from src.pkg.walk.context import ModuleFrame
        raw_mod = object()
        frame = ModuleFrame(module_raw=raw_mod, async_reset_signals=frozenset({"rst", "arst"}), cache={"k": "v"})
        ctx = context.with_module_frame(frame)

        assert ctx.module_frame is frame
        assert ctx.data["module_async_resets"] == {"rst", "arst"}
        assert ctx.data["module_cache"] == {"k": "v"}

        # Preserved across push
        child = ctx.push(fake_vnode(None))
        assert child.module_frame is frame
        assert child.data["module_async_resets"] == {"rst", "arst"}

    def test_with_block_frame_populates_frame_and_backward_compatible_data(self, context: Context) -> None:
        from src.pkg.walk.context import ProceduralBlockFrame
        raw_block = object()
        mix_trigger = object()
        frame = ProceduralBlockFrame(
            block_raw=raw_block,
            missing_sensitivity={"clk": object()},
            mix_trigger=mix_trigger,
            multiple_nonblocking_write_triggers={"q": object()},
            is_comb=True,
            async_reset_names=frozenset({"rst_n"}),
        )
        ctx = context.with_block_frame(frame)

        assert ctx.block_frame is frame
        assert ctx.data["mix_trigger"] is mix_trigger
        assert ctx.data["comb_always_block"] == (raw_block, True)
        assert ctx.data["block_async_reset_names"] == (raw_block, {"rst_n"})

        # Preserved across push
        child = ctx.push(fake_vnode(None))
        assert child.block_frame is frame
        assert child.data["mix_trigger"] is mix_trigger

    def test_with_case_frame_populates_frame_and_backward_compatible_data(self, context: Context) -> None:
        from src.pkg.walk.context import CaseStatementFrame
        raw_case = object()
        fake_model = object()
        frame = CaseStatementFrame(case_raw=raw_case, fsm_model=fake_model)
        ctx = context.with_case_frame(frame)

        assert ctx.case_frame is frame
        assert ctx.data["fsm_model"] == (raw_case, fake_model)

        # Preserved across push
        child = ctx.push(fake_vnode(None))
        assert child.case_frame is frame
        assert child.data["fsm_model"] == (raw_case, fake_model)


class TestContextFlag:
    """Test cases for the ContextFlag enum."""

    def test_context_flags_exist(self) -> None:
        """Test that all expected ContextFlags exist."""
        expected_flags = [
            'HAS_EVENT_CONTROL', 'POSEDGE', 'NEGEDGE',
            'ALWAYS', 'ALWAYS_COMB', 'ALWAYS_LATCH',
            'IN_EXPRESSION', 'IN_ASSIGNMENT',
            'BLOCKING_ASSIGN', 'NONBLOCKING_ASSIGN',
            'CASE_GENERATE', 'DEFAULT'
        ]
        
        for flag_name in expected_flags:
            assert hasattr(ContextFlag, flag_name)

    def test_context_flags_are_unique(self) -> None:
        """Test that each ContextFlag has a unique value."""
        flags = [
            ContextFlag.HAS_EVENT_CONTROL,
            ContextFlag.POSEDGE,
            ContextFlag.NEGEDGE,
            ContextFlag.ALWAYS,
            ContextFlag.ALWAYS_COMB,
        ]
        
        flag_values = [f.value for f in flags]
        assert len(flag_values) == len(set(flag_values))
