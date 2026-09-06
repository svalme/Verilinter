from ..types import SystemNameNode

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
        DISPLAY_SYSTEM_TASK_NAMES
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
