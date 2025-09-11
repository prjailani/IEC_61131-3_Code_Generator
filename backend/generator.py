import json
import re
import sys
from typing import Any, Dict, List, Optional

INDENT = "    "

def st_bool(val: bool) -> str:
    return "TRUE" if val else "FALSE"

def is_identifier(s: str) -> bool:
    return re.match(r'^[A-Za-z_]\w*(?:[\.\[][\w\]\.]+)*$', s) is not None

def value_to_st(val: Any) -> str:
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return st_bool(val)
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        if val.startswith("T#"):
            return val
        if is_identifier(val):
            return val
        # expression
        if re.search(r'[\s\+\-\*\/\(\)]', val):
            return val
        return f'"{val}"'
    return json.dumps(val)

def indent_lines(lines: List[str], level: int) -> List[str]:
    return [(INDENT * level) + ln if ln else "" for ln in lines]

def parse_struct_datatype(datatype: str) -> Optional[List[Dict[str, str]]]:
    """
    Accepts a datatype like:
      "STRUCT(Name : STRING[20]; Value : REAL)"
    and returns list of fields: [{name, datatype}, ...]
    """
    m = re.match(r'^\s*STRUCT\s*\(\s*(.+)\s*\)\s*$', datatype, flags=re.IGNORECASE)
    if not m:
        return None
    inner = m.group(1)
    # split on semicolons, each like "Name : STRING[20]"
    parts = [p.strip() for p in inner.split(';') if p.strip()]
    fields = []
    for p in parts:
        mm = re.match(r'^([\w]+)\s*:\s*(.+)$', p)
        if mm:
            fname = mm.group(1)
            ftype = mm.group(2).strip()
            fields.append({"name": fname, "datatype": ftype})
    return fields

def emit_var_block(declarations: List[Dict[str, Any]]) -> List[str]:
    """
    Returns lines for VAR ... END_VAR block.
    declarations: list of {type, name, datatype, initialValue?}
    """
    if not declarations:
        return []

    lines = ["VAR"]
    for d in declarations:
        name = d.get("name")
        datatype = d.get("datatype", "ANY")
        init = d.get("initialValue", None)

        # STRUCT handling
        if isinstance(datatype, str) and datatype.strip().upper().startswith("STRUCT"):
            fields = parse_struct_datatype(datatype)
            if fields:
                lines.append(f"{INDENT}{name} : STRUCT")
                for f in fields:
                    lines.append(f"{INDENT*2}{f['name']} : {f['datatype']};")
                lines.append(f"{INDENT}END_STRUCT;")
                continue

        # Normal declaration
        if init is not None:
            st_init = value_to_st(init)
            lines.append(f"{INDENT}{name} : {datatype} := {st_init};")
        else:
            lines.append(f"{INDENT}{name} : {datatype};")

    lines.append("END_VAR")
    return lines

# ----------------------
# Statement conversion (recursive)
# ----------------------
def convert_statement(stmt: Dict[str, Any], level: int = 0) -> List[str]:
    """
    Convert one statement JSON to ST lines.
    """
    t = stmt.get("type")
    lines: List[str] = []

    if t == "assignment":
        target = stmt["target"]
        expr = stmt["expression"]
        lines.append(f"{target} := {expr};")

    elif t == "if":
        cond = stmt["condition"]
        lines.append(f"IF {cond} THEN")
        # then block
        for s in stmt.get("then", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        # else block
        else_block = stmt.get("else")
        if else_block:
            lines.append("ELSE")
            for s in else_block:
                lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_IF;")

    elif t == "case":
        selector = stmt["selector"]
        lines.append(f"CASE {selector} OF")
        for c in stmt.get("cases", []):
            val = c.get("value")
            # value may be string or number
            val_repr = value_to_st(val) if not isinstance(val, (int, float)) else str(val)
            lines.append(f"{INDENT}{val_repr}:")
            for s in c.get("statements", []):
                lines += indent_lines(convert_statement(s, level+2), level+2)
        # else
        else_stmts = stmt.get("else")
        if else_stmts:
            lines.append("ELSE")
            for s in else_stmts:
                lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_CASE;")

    elif t == "for":
        it = stmt["iterator"]
        frm = stmt.get("from")
        to = stmt.get("to")
        by = stmt.get("by", None)
        by_part = f" BY {by}" if by is not None else ""
        lines.append(f"FOR {it} := {frm} TO {to}{by_part} DO")
        for s in stmt.get("body", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_FOR;")

    elif t == "while":
        cond = stmt["condition"]
        lines.append(f"WHILE {cond} DO")
        for s in stmt.get("body", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_WHILE;")

    elif t == "repeat":
        lines.append("REPEAT")
        for s in stmt.get("body", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        until = stmt.get("until")
        if until:
            lines.append(f"UNTIL {until}")
        lines.append("END_REPEAT;")

    elif t == "functionCall":
        name = stmt["name"]
        args = stmt.get("arguments", [])
        args_str = ", ".join(map(str, args))
        # In ST function call as statement: Name(args);
        lines.append(f"{name}({args_str});")

    elif t == "fbCall":
        # name is usually instance name; inputs/outputs are dicts mapping port->expr
        name = stmt["name"]
        inputs = stmt.get("inputs", {})
        outputs = stmt.get("outputs", {})  # rarely used directly in call
        call_parts = []
        for k, v in (inputs.items() if isinstance(inputs, dict) else []):
            call_parts.append(f"{k} := {value_to_st(v)}")
        # some users provide outputs map to variables to be assigned; we don't auto-emit those assignments here,
        # because many FBs use internal outputs that are accessed as instance.member afterwards.
        call_text = ", ".join(call_parts)
        lines.append(f"{name}({call_text});")
        # if there are explicit output mappings, optionally note them as comments or simple assignments
        if outputs:
            # If outputs map like { "Q": "T1.Q", ... }, we can't "call" them; usually outputs are read later.
            # We'll emit a comment to remind about outputs mapping.
            out_comment = ", ".join(f"{k} => {v}" for k, v in outputs.items())
            lines.append(f"(* outputs: {out_comment} *)")

    else:
        # unknown/unsupported node type: emit comment
        lines.append(f"(* Unsupported statement type: {t} -- full node: {json.dumps(stmt)} *)")

    return lines

def convert_statements(stmts: List[Dict[str, Any]], level: int = 0) -> List[str]:
    out: List[str] = []
    for s in stmts:
        out += indent_lines(convert_statement(s, level), level)
    return out

# ----------------------
# Top-level converters: Program / FunctionBlock / Function
# ----------------------
def convert_program(obj: Dict[str, Any]) -> str:
    prog = obj.get("program")
    if not prog:
        raise ValueError("No 'program' key found")
    name = prog.get("name", "Program")
    declarations = prog.get("declarations", [])
    statements = prog.get("statements", [])

    lines: List[str] = []
    lines.append(f"PROGRAM {name}")
    # VAR block
    var_lines = emit_var_block(declarations)
    if var_lines:
        lines += indent_lines(var_lines, 0)
    lines.append("")  # blank line between decls and body if any

    # Body statements (top-level)
    if statements:
        for s in statements:
            lines += convert_statement(s, 0 if not var_lines else 0)
    lines.append("")
    lines.append(f"END_PROGRAM")
    return "\n".join(lines)

def convert_function_block(obj: Dict[str, Any]) -> str:
    fb = obj.get("functionBlock")
    if not fb:
        raise ValueError("No 'functionBlock' key found")
    name = fb.get("name", "FB")
    inputs = fb.get("inputs", [])
    outputs = fb.get("outputs", [])
    locals_ = fb.get("locals", [])
    body = fb.get("body", [])

    lines: List[str] = []
    lines.append(f"FUNCTION_BLOCK {name}")

    # VAR_INPUT
    if inputs:
        lines.append("VAR_INPUT")
        for inp in inputs:
            lines.append(f"{INDENT}{inp['name']} : {inp['datatype']};")
        lines.append("END_VAR")

    # VAR_OUTPUT
    if outputs:
        lines.append("VAR_OUTPUT")
        for outp in outputs:
            lines.append(f"{INDENT}{outp['name']} : {outp['datatype']};")
        lines.append("END_VAR")

    # VAR (locals)
    if locals_:
        lines.append("VAR")
        for l in locals_:
            init = l.get("initialValue")
            if init is not None:
                lines.append(f"{INDENT}{l['name']} : {l['datatype']} := {value_to_st(init)};")
            else:
                lines.append(f"{INDENT}{l['name']} : {l['datatype']};")
        lines.append("END_VAR")

    lines.append("")

    # body statements
    for s in body:
        lines += convert_statement(s, 0)

    lines.append("")
    lines.append("END_FUNCTION_BLOCK")
    return "\n".join(lines)

def convert_function(obj: Dict[str, Any]) -> str:
    """
    Convert a 'function' JSON object into IEC-61131-3 FUNCTION ... END_FUNCTION block.
    JSON example:
    {
      "function": {
        "name": "AddNumbers",
        "returnType": "INT",
        "inputs": [{ "name": "a", "datatype": "INT" }, ...],
        "locals": [...],
        "body": [ { "type": "return", "expression": "a + b" } ]
      }
    }
    Note: 'return' statements in body are converted to:
          FunctionName := expression;
          RETURN;
    """
    fn = obj.get("function")
    if not fn:
        raise ValueError("No 'function' key found")
    name = fn.get("name", "Function")
    return_type = fn.get("returnType", "ANY")
    inputs = fn.get("inputs", [])
    locals_ = fn.get("locals", [])
    body = fn.get("body", [])

    lines: List[str] = []
    lines.append(f"FUNCTION {name} : {return_type}")

    # VAR_INPUT
    if inputs:
        lines.append("VAR_INPUT")
        for inp in inputs:
            lines.append(f"{INDENT}{inp['name']} : {inp['datatype']};")
        lines.append("END_VAR")

    # VAR (locals)
    if locals_:
        lines.append("VAR")
        for l in locals_:
            init = l.get("initialValue")
            if init is not None:
                lines.append(f"{INDENT}{l['name']} : {l['datatype']} := {value_to_st(init)};")
            else:
                lines.append(f"{INDENT}{l['name']} : {l['datatype']};")
        lines.append("END_VAR")

    lines.append("")  # blank line before body

    # body statements (with special handling for "return")
    for s in body:
        if s.get("type") == "return":
            expr = s.get("expression", "0")
            # Assign to function name and emit RETURN;
            lines.append(f"{name} := {expr};")
            lines.append("RETURN;")
        else:
            lines += convert_statement(s, 0)

    lines.append("")
    lines.append("END_FUNCTION")
    return "\n".join(lines)

# ----------------------
# Convenience: handle top-level object(s)
# ----------------------
def convert_top(obj: Any) -> str:
    """
    obj may be:
      - dict with 'program'
      - dict with 'functionBlock'
      - dict with 'function'
      - list of such dicts
    """
    outputs = []
    if isinstance(obj, list):
        for element in obj:
            outputs.append(convert_top(element))
        return "\n\n".join(outputs)

    if isinstance(obj, dict):
        if "program" in obj:
            outputs.append(convert_program(obj))
        if "functionBlock" in obj:
            outputs.append(convert_function_block(obj))
        if "function" in obj:
            outputs.append(convert_function(obj))
        # If keys are directly the program or functionBlock or function contents (user may pass without wrapper)
        if "name" in obj and "declarations" in obj and "statements" in obj:
            # assume it's a program object itself
            outputs.append(convert_program({"program": obj}))
        if "name" in obj and "returnType" in obj and "body" in obj:
            # assume it's a function object itself
            outputs.append(convert_function({"function": obj}))
        if not outputs:
            raise ValueError("Input dict doesn't look like a program/functionBlock/function. Keys: " + ", ".join(obj.keys()))
        return "\n\n".join(outputs)

    raise ValueError("Unsupported top-level JSON type: " + str(type(obj)))

def generator(data):
    try:
        st_text = convert_top(data)
    except Exception as e:
        print(f"Error converting JSON -> ST: {e}", file=sys.stderr)
        sys.exit(2)

    return st_text