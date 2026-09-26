from ..syntax_kinds import (
    ARGUMENT_LIST_KIND,
    INVOCATION_EXPRESSION_KIND,
    NAMED_ARGUMENT_KIND,
    ORDERED_ARGUMENT_KIND,
)
from ..types import SyntaxNode, SystemNameNode

READMEM_SYSTEM_TASK_NAMES = {"$readmemh", "$readmemb"}

DISPLAY_SYSTEM_TASK_NAMES = {
    "$display", "$displayb", "$displayh", "$displayo",
    "$write", "$writeb", "$writeh", "$writeo",
    "$monitor", "$monitorb", "$monitorh", "$monitoro",
    "$strobe", "$strobeb", "$strobeh", "$strobeo",
}

SIMULATION_CONTROL_TASK_NAMES = {"$stop", "$finish"}

RANDOM_SYSTEM_FUNCTION_NAMES = {"$random", "$urandom", "$urandom_range"}

TIME_SYSTEM_FUNCTION_NAMES = {"$time", "$realtime", "$stime"}

VCD_DUMP_TASK_NAMES = {
    "$dumpfile", "$dumpvars", "$dumpon", "$dumpoff", "$dumpall", "$dumpflush", "$dumplimit",
}

FILE_IO_SYSTEM_TASK_NAMES = {
    "$fopen", "$fclose",
    "$fdisplay", "$fdisplayb", "$fdisplayh", "$fdisplayo",
    "$fwrite", "$fwriteb", "$fwriteh", "$fwriteo",
    "$fstrobe", "$fstrobeb", "$fstrobeh", "$fstrobeo",
    "$fmonitor", "$fmonitorb", "$fmonitorh", "$fmonitoro",
    "$fscanf", "$fgets", "$fgetc", "$fread",
    "$fflush", "$feof", "$ferror", "$ftell", "$fseek", "$rewind", "$ungetc",
}

PLUSARGS_SYSTEM_FUNCTION_NAMES = {"$test$plusargs", "$value$plusargs"}

ASSERTION_CONTROL_TASK_NAMES = {
    "$assertoff", "$asserton", "$assertkill", "$assertcontrol",
    "$assertpasson", "$assertpassoff", "$assertfailon", "$assertfailoff",
    "$assertnonvacuouson", "$assertvacuousoff",
}


ALL_SYSTEM_TASK_NAMES = {
    name.lstrip("$")
    for name in (
        READMEM_SYSTEM_TASK_NAMES
        | DISPLAY_SYSTEM_TASK_NAMES
        | SIMULATION_CONTROL_TASK_NAMES
        | RANDOM_SYSTEM_FUNCTION_NAMES
        | TIME_SYSTEM_FUNCTION_NAMES
        | VCD_DUMP_TASK_NAMES
        | FILE_IO_SYSTEM_TASK_NAMES
        | PLUSARGS_SYSTEM_FUNCTION_NAMES
        | ASSERTION_CONTROL_TASK_NAMES
    )
    if name.lstrip("$")
}

# 0-based index of the by-reference "output" argument this project specially
# recognizes for a handful of system tasks/functions that populate an
# argument rather than reading it -- `identifier_access_modes` has no notion
# of a system-task argument at all, so without this, that argument's
# identifier falls through to the default plain-read classification and a
# variable populated only this way looks permanently undriven. Deliberately
# narrow: only single, unambiguous by-reference arguments are covered, not a
# variadic one like `$fscanf`/`$sscanf`'s trailing argument list.
SYSTEM_TASK_OUTPUT_ARGUMENT_INDEX = {
    "$readmemh": 1,
    "$readmemb": 1,
    "$value$plusargs": 1,
}


def system_task_name(raw: object) -> str | None:
    if not isinstance(raw, SystemNameNode):
        return None
    identifier = getattr(raw, "systemIdentifier", None)
    value = getattr(identifier, "valueText", None)
    return value if isinstance(value, str) and value else None


def is_display_system_task(raw: object) -> bool:
    return system_task_name(raw) in DISPLAY_SYSTEM_TASK_NAMES


def is_simulation_control_task(raw: object) -> bool:
    return system_task_name(raw) in SIMULATION_CONTROL_TASK_NAMES


def is_random_system_function(raw: object) -> bool:
    return system_task_name(raw) in RANDOM_SYSTEM_FUNCTION_NAMES


def is_time_system_function(raw: object) -> bool:
    return system_task_name(raw) in TIME_SYSTEM_FUNCTION_NAMES


def is_vcd_dump_task(raw: object) -> bool:
    return system_task_name(raw) in VCD_DUMP_TASK_NAMES


def is_file_io_system_task(raw: object) -> bool:
    return system_task_name(raw) in FILE_IO_SYSTEM_TASK_NAMES


def is_plusargs_system_function(raw: object) -> bool:
    return system_task_name(raw) in PLUSARGS_SYSTEM_FUNCTION_NAMES


def is_assertion_control_task(raw: object) -> bool:
    return system_task_name(raw) in ASSERTION_CONTROL_TASK_NAMES


def system_task_argument_list(raw: object) -> list[object]:
    items = getattr(raw, "parameters", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


def is_system_task_output_argument(raw: object) -> bool:
    """True if `raw` is (a descendant of) the by-reference output argument of
    a system task/function this project specially recognizes (see
    `SYSTEM_TASK_OUTPUT_ARGUMENT_INDEX`) -- e.g. `firmware_file` in
    `$readmemh(firmware_file, memory)` or `x` in `$value$plusargs("...", x)`.
    These populate that argument rather than reading it."""
    if not isinstance(raw, SyntaxNode):
        return False
    node = raw
    parent = getattr(node, "parent", None)
    depth = 0
    while parent is not None and getattr(parent, "kind", None) not in (
        ORDERED_ARGUMENT_KIND,
        NAMED_ARGUMENT_KIND,
    ) and depth < 64:
        depth += 1
        node = parent
        parent = getattr(parent, "parent", None)
    if parent is None or depth >= 64:
        return False
    arg_node = parent

    arg_list = getattr(arg_node, "parent", None)
    if getattr(arg_list, "kind", None) != ARGUMENT_LIST_KIND:
        return False
    items = system_task_argument_list(arg_list)
    try:
        index = next(i for i, item in enumerate(items) if item is arg_node)
    except StopIteration:
        return False

    invocation = getattr(arg_list, "parent", None)
    if getattr(invocation, "kind", None) != INVOCATION_EXPRESSION_KIND:
        return False
    callee = getattr(invocation, "left", None)
    if not isinstance(callee, SystemNameNode):
        return False
    return SYSTEM_TASK_OUTPUT_ARGUMENT_INDEX.get(system_task_name(callee)) == index
