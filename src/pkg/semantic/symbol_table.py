# src/pkg/semantic/symbol_table.py
from __future__ import annotations

from ..vnodes.base_vnode import Location
from .hierarchical_resolver import HierarchicalNameResolver
from .models.instance_record import InstanceRecord
from .package_resolver import PackageResolver
from .resolution import UnresolvedReference
from .symbol import Symbol
from .scope import Scope
from .scope_kinds import ScopeKind


class SymbolTable:
    """Manages multiple scopes and provides symbol lookup across the hierarchy."""

    def __init__(self) -> None:
        self.packages: dict[str, list[Scope]] = {}  # package name -> all scopes defining it, across files
        self.global_scope: Scope = Scope(kind=ScopeKind.GLOBAL)
        self.global_scope.packages = self.packages
        self.scopes: list[Scope] = [self.global_scope]  # registry - all scopes ever created
        self._scope_stack: list[Scope] = [self.global_scope]  # traversal stack
        self.modules: dict[str, list[Scope]] = {}  # module name -> all scopes defining it, across files
        self.primitives: set[str] = set()  # user-defined primitive (UDP) names, across files
        self.module_ports: dict[str, list[dict]] = {}  # modules declared in other files: name -> [{file, ports}]
        self.module_references: list[tuple[str, Location]] = []
        self.instantiation_edges: list[tuple[str, str, Location]] = []  # (from_module, to_module, location)
        self.instantiations: list[InstanceRecord] = []
        self.reset_style_events: list[tuple[str, str, Location]] = []  # (module_name, "sync"|"async", location)
        self.combinational_driver_ids: set[str] = set()
        self.sequential_driver_ids: set[str] = set()
        self.initial_driver_ids: set[str] = set()
        self.tristate_driver_ids: set[str] = set()
        self.branch_constructs: dict[str, tuple[set[int] | None, tuple[tuple[str, int], ...]]] = {}
        self.pending_hierarchical_uses: list[tuple[Scope, list[str], str, Location | None, dict[str, object]]] = []
        self.unresolved_references: list[UnresolvedReference] = []  # names used with no declaration, in walk order
        self.current_file: str | None = None
        self._file_default_nettype_none: dict[str, bool] = {}

    def set_current_file(self, path: str) -> None:
        """Signal that a new file is about to be walked. Stamps all subsequent scopes."""
        self.current_file = path

    def set_current_file_default_nettype_none(self, enabled: bool) -> None:
        if self.current_file is None:
            raise RuntimeError("current_file must be set before default_nettype metadata")
        self._file_default_nettype_none[self.current_file] = enabled

    def current_file_uses_default_nettype_none(self) -> bool:
        if self.current_file is None:
            return False
        return self._file_default_nettype_none.get(self.current_file, False)

    def new_scope(
        self,
        kind: str,
        name: str | None = None,
        parent: Scope | None = None,
        location: Location | None = None,
    ) -> Scope:
        """Create a new scope, add it to the registry, and push it onto the traversal stack."""
        if parent is None:
            parent = self._scope_stack[-1] if self._scope_stack else None

        scope = Scope(kind=kind, name=name, location=location)
        scope.file = self.current_file
        scope.packages = self.packages
        scope.set_parent(parent)
        self.scopes.append(scope)
        self._scope_stack.append(scope)
        return scope

    def pop_scope(self) -> None:
        """Exit the current scope, returning to the parent."""
        assert len(self._scope_stack) > 1, (
            f"pop_scope called with only global scope on stack - "
            f"unbalanced push/pop in visitor (current: {self._scope_stack[-1]})"
        )
        self._scope_stack.pop()

    def register_module(self, name: str, scope: Scope) -> None:
        """Record a module definition. Appends if the name was already registered."""
        self.modules.setdefault(name, []).append(scope)

    def register_package(self, name: str, scope: Scope) -> None:
        """Record a package definition. Appends if the name was already registered.

        Kept separate from `modules` -- pyslang represents `package`/`module`
        declarations with the same wrapper class, distinguishable only by
        `.kind`, so a package must not be registered as a module or it would
        pollute UNDEFINED_MODULE/DUPLICATE_MODULE's module registry.
        """
        self.packages.setdefault(name, []).append(scope)

    def register_primitive(self, name: str) -> None:
        """Record a user-defined primitive (UDP) declaration by name."""
        self.primitives.add(name)

    def register_module_reference(self, name: str, location: Location) -> None:
        """Record an instantiation site referencing a module type by name."""
        self.module_references.append((name, location))

    def register_instantiation_edge(self, from_module: str, to_module: str, location: Location) -> None:
        """Record that `from_module` instantiates `to_module` at `location`, for hierarchy-cycle detection."""
        self.instantiation_edges.append((from_module, to_module, location))

    def register_instantiation(self, record: InstanceRecord | dict[str, object]) -> None:
        inst = record if isinstance(record, InstanceRecord) else InstanceRecord.from_dict(record)
        self.instantiations.append(inst)

    def register_reset_style_event(self, module_name: str, style: str, location: Location) -> None:
        """Record that a procedural block in `module_name` is edge-sensitive with
        reset style `style` ("sync" or "async"), for `NO_MIXED_RESET_STYLE`."""
        self.reset_style_events.append((module_name, style, location))

    def mark_combinational_driver(self, driver_id: str) -> None:
        """Record that `driver_id` (a continuous assign or combinational-style
        procedural block) drives combinationally, for `COMBINATIONAL_LOOP`."""
        self.combinational_driver_ids.add(driver_id)

    def mark_sequential_driver(self, driver_id: str) -> None:
        """Record that `driver_id` (an always_ff or clocked procedural block)
        drives sequentially, for sequential register segregation."""
        self.sequential_driver_ids.add(driver_id)

    def mark_initial_driver(self, driver_id: str) -> None:
        """Record that `driver_id` (an initial block) drives at time 0."""
        self.initial_driver_ids.add(driver_id)

    def mark_tristate_driver(self, driver_id: str) -> None:
        """Record that `driver_id` (a continuous assign) drives via a tri-state
        (`cond ? value : 'bz`) ternary, for `UNDRIVEN_TRISTATE_SIGNAL`."""
        self.tristate_driver_ids.add(driver_id)

    def register_branch_construct(
        self,
        construct_id: str,
        required_branches: set[int] | None,
        parent_signature: tuple[tuple[str, int], ...] = (),
    ) -> None:
        """Record branching construct metadata (required branches for exhaustiveness,
        and enclosing parent branch signature) for control-flow analysis."""
        self.branch_constructs[construct_id] = (required_branches, parent_signature)

    def record_hierarchical_use(
        self,
        scope: Scope,
        segments: list[str],
        member: str,
        location: Location | None,
        use_kwargs: dict[str, object],
    ) -> None:
        """Queue a read/write of `member` reached through the path `segments` written in `scope`.

        The path may name a block, instance, interface or module declared later in the file, so the use is
        applied by `resolve_hierarchical_uses` once the whole file has been walked."""
        self.pending_hierarchical_uses.append((scope, segments, member, location, use_kwargs))

    def resolve_hierarchical_uses(self) -> None:
        """Attach queued hierarchical uses to the symbols they name; a path that does not lead to a
        symbol in the walked files is dropped."""
        pending, self.pending_hierarchical_uses = self.pending_hierarchical_uses, []
        resolver = HierarchicalNameResolver(self)
        for scope, segments, member, location, use_kwargs in pending:
            target = resolver.resolve(scope, segments, member)
            if target is not None:
                target.scope.has_visible_interface_users = True
                target.symbol.add_use(location, **use_kwargs)  # type: ignore[arg-type]

    def lookup_module(self, name: str) -> Scope | None:
        """Return the first scope for a named module, or None if not yet seen."""
        scopes = self.modules.get(name)
        return scopes[0] if scopes else None

    def lookup_package(self, name: str) -> Scope | None:
        """Return the first scope for a named package, or None if no walked or seeded file declares it.
        Name resolution goes through `Scope.lookup_package_member`, which looks in every scope declaring
        the package; this returns one scope for callers that need the package itself (its subroutines)."""
        return self.package_resolver().scope(name)

    def package_resolver(self) -> PackageResolver:
        """The resolver over this table's package registry."""
        return PackageResolver(self.packages)

    def is_duplicate_module(self, name: str) -> bool:
        """Return True if more than one file defines a module with this name."""
        return len(self.modules.get(name, [])) > 1

    def lookup_from_scope(self, name: str, scope: Scope | None = None) -> Symbol | None:
        """Lookup a symbol starting from the given scope upwards, then through the imports in effect
        there (see `Scope.lookup_hierarchical`, which is the one implementation)."""
        if scope is None:
            return None
        return Scope.lookup_hierarchical(scope, name)

    def lookup_qualified(self, path: list[str]) -> Symbol | None:
        """Navigate scope tree by name path from global, then look up the final symbol.

        e.g. ["top", "sub", "clk"] -> navigate global->top->sub, look up "clk".
        """
        if not path:
            return None
        current: Scope | None = self.global_scope
        for segment in path[:-1]:
            current = next((c for c in current.children if c.name == segment), None)
            if current is None:
                return None
        return current.lookup(path[-1])

    def lookup_global(self, name: str) -> Symbol | None:
        """DFS from global scope through the entire scope tree."""
        visited: set[int] = set()

        def _search(scope: Scope, depth: int = 0) -> Symbol | None:
            if scope is None or depth >= 64:
                return None
            sid = id(scope)
            if sid in visited:
                return None
            visited.add(sid)

            lookup_fn = getattr(scope, "lookup", None)
            if callable(lookup_fn):
                found = lookup_fn(name)
                if found:
                    return found
            for child in getattr(scope, "children", ()):
                found = _search(child, depth + 1)
                if found:
                    return found
            return None

        return _search(self.global_scope)
