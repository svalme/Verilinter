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
