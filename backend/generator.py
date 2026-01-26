"""
IEC 61131-3 Structured Text Generator

Converts JSON intermediate representation to IEC 61131-3 Structured Text code.
Supports programs, function blocks, and functions.
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

INDENT = "    "


class GeneratorError(Exception):
    """Custom exception for generator errors."""
    pass


def st_bool(val: bool) -> str:
    """Convert Python boolean to ST boolean literal."""
    return "TRUE" if val else "FALSE"


def is_identifier(s: str) -> bool:
    """Check if string is a valid ST identifier."""
    return re.match(r'^[A-Za-z_]\w*(?:[\.\[][\w\]\.]+)*$', s) is not None


def value_to_st(val: Any) -> str:
    """Convert Python value to ST representation."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return st_bool(val)
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        # Time literals
        if val.startswith("T#") or val.startswith("TIME#"):
            return val
        # Date literals
        if val.startswith("D#") or val.startswith("DATE#"):
            return val
        # DateTime literals
        if val.startswith("DT#") or val.startswith("DATE_AND_TIME#"):
            return val
        # TOD literals
        if val.startswith("TOD#") or val.startswith("TIME_OF_DAY#"):
            return val
        # Identifiers
        if is_identifier(val):
            return val
        # Expressions with operators
        if re.search(r'[\s\+\-\*\/\(\)]', val):
            return val
        # String literals
        return f'"{val}"'
    # For arrays/dicts, dump as JSON (rare for simple ST)
    return json.dumps(val)


def indent_lines(lines: List[str], level: int) -> List[str]:
    """Add indentation to a list of lines."""
    return [(INDENT * level) + ln if ln else "" for ln in lines]


def parse_struct_datatype(datatype: str) -> Optional[List[Dict[str, str]]]:
    """
    Parse a STRUCT datatype definition.
    
    Example:
        "STRUCT(Name : STRING[20]; Value : REAL)"
    
    Returns:
        List of field dictionaries: [{name, datatype}, ...]
    """
    m = re.match(r'^\s*STRUCT\s*\(\s*(.+)\s*\)\s*$', datatype, flags=re.IGNORECASE)
    if not m:
        return None
    inner = m.group(1)
    # Split on semicolons, each like "Name : STRING[20]"
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
    Generate lines for VAR ... END_VAR block.
    
    Args:
        declarations: List of {type, name, datatype, initialValue?}
    
    Returns:
        List of ST code lines
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


def convert_statement(stmt: Dict[str, Any], level: int = 0) -> List[str]:
    """
    Convert one statement JSON to ST lines.
    
    Args:
        stmt: Statement dictionary with 'type' key
        level: Indentation level
    
    Returns:
        List of ST code lines
    """
    t = stmt.get("type")
    lines: List[str] = []

    if t == "assignment":
        target = stmt.get("target", "")
        expr = stmt.get("expression", "")
        if not target:
            logger.warning("Assignment statement missing target")
            lines.append("(* ERROR: Assignment missing target *)")
        else:
            lines.append(f"{target} := {expr};")

    elif t == "if":
        cond = stmt.get("condition", "TRUE")
        lines.append(f"IF {cond} THEN")
        # Then block
        for s in stmt.get("then", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        # Else-if blocks (if present)
        for elif_block in stmt.get("elsif", []):
            elif_cond = elif_block.get("condition", "TRUE")
            lines.append(f"ELSIF {elif_cond} THEN")
            for s in elif_block.get("then", []):
                lines += indent_lines(convert_statement(s, level+1), level+1)
        # Else block
        else_block = stmt.get("else")
        if else_block:
            lines.append("ELSE")
            for s in else_block:
                lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_IF;")

    elif t == "case":
        selector = stmt.get("selector", "0")
        lines.append(f"CASE {selector} OF")
        for c in stmt.get("cases", []):
            val = c.get("value")
            # Value may be string or number
            val_repr = value_to_st(val) if not isinstance(val, (int, float)) else str(val)
            lines.append(f"{INDENT}{val_repr}:")
            for s in c.get("statements", []):
                lines += indent_lines(convert_statement(s, level+2), level+2)
        # Else clause
        else_stmts = stmt.get("else")
        if else_stmts:
            lines.append("ELSE")
            for s in else_stmts:
                lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_CASE;")

    elif t == "for":
        it = stmt.get("iterator", "i")
        frm = stmt.get("from", 0)
        to = stmt.get("to", 0)
        by = stmt.get("by", None)
        by_part = f" BY {by}" if by is not None else ""
        lines.append(f"FOR {it} := {frm} TO {to}{by_part} DO")
        for s in stmt.get("body", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_FOR;")

    elif t == "while":
        cond = stmt.get("condition", "TRUE")
        lines.append(f"WHILE {cond} DO")
        for s in stmt.get("body", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        lines.append("END_WHILE;")

    elif t == "repeat":
        lines.append("REPEAT")
        for s in stmt.get("body", []):
            lines += indent_lines(convert_statement(s, level+1), level+1)
        until = stmt.get("until", "TRUE")
        lines.append(f"UNTIL {until}")
        lines.append("END_REPEAT;")

    elif t == "functionCall":
        name = stmt.get("name", "UnknownFunction")
        args = stmt.get("arguments", [])
        args_str = ", ".join(str(arg) for arg in args)
        lines.append(f"{name}({args_str});")

    elif t == "fbCall":
        # Function block call with named parameters
        name = stmt.get("name", "UnknownFB")
        inputs = stmt.get("inputs", {})
        outputs = stmt.get("outputs", {})
        
        call_parts = []
        if isinstance(inputs, dict):
            for k, v in inputs.items():
                call_parts.append(f"{k} := {value_to_st(v)}")
        
        call_text = ", ".join(call_parts)
        lines.append(f"{name}({call_text});")
        
        # Add output mappings as comments if present
        if outputs and isinstance(outputs, dict):
            out_comment = ", ".join(f"{k} => {v}" for k, v in outputs.items())
            lines.append(f"(* outputs: {out_comment} *)")

    elif t == "return":
        # Return statement (for functions)
        expr = stmt.get("expression")
        if expr:
            lines.append(f"(* Return value set via function name assignment *)")
        else:
            lines.append("RETURN;")

    elif t == "exit":
        lines.append("EXIT;")

    elif t == "continue":
        lines.append("CONTINUE;")

    else:
        # Unknown/unsupported node type
        logger.warning(f"Unsupported statement type: {t}")
        lines.append(f"(* Unsupported statement type: {t} *)")

    return lines


def convert_statements(stmts: List[Dict[str, Any]], level: int = 0) -> List[str]:
    """Convert a list of statements to ST lines."""
    out: List[str] = []
    for s in stmts:
        out += indent_lines(convert_statement(s, level), level)
    return out


def convert_program(obj: Dict[str, Any]) -> str:
    """
    Convert a 'program' JSON object to IEC 61131-3 PROGRAM ... END_PROGRAM block.
    """
    prog = obj.get("program")
    if not prog:
        raise GeneratorError("No 'program' key found in object")
    
    name = prog.get("name", "Program")
    declarations = prog.get("declarations", [])
    statements = prog.get("statements", [])

    lines: List[str] = []
    lines.append(f"PROGRAM {name}")
    
    # VAR block
    var_lines = emit_var_block(declarations)
    if var_lines:
        lines += indent_lines(var_lines, 0)
    lines.append("")  # Blank line between declarations and body

    # Body statements
    if statements:
        for s in statements:
            lines += convert_statement(s, 0)
    
    lines.append("")
    lines.append("END_PROGRAM")
    return "\n".join(lines)


def convert_function_block(obj: Dict[str, Any]) -> str:
    """
    Convert a 'functionBlock' JSON object to IEC 61131-3 FUNCTION_BLOCK ... END_FUNCTION_BLOCK.
    """
    fb = obj.get("functionBlock")
    if not fb:
        raise GeneratorError("No 'functionBlock' key found in object")
    
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
            inp_name = inp.get("name", "unknown")
            inp_type = inp.get("datatype", "ANY")
            lines.append(f"{INDENT}{inp_name} : {inp_type};")
        lines.append("END_VAR")

    # VAR_OUTPUT
    if outputs:
        lines.append("VAR_OUTPUT")
        for outp in outputs:
            out_name = outp.get("name", "unknown")
            out_type = outp.get("datatype", "ANY")
            lines.append(f"{INDENT}{out_name} : {out_type};")
        lines.append("END_VAR")

    # VAR (locals)
    if locals_:
        lines.append("VAR")
        for loc in locals_:
            loc_name = loc.get("name", "unknown")
            loc_type = loc.get("datatype", "ANY")
            init = loc.get("initialValue")
            if init is not None:
                lines.append(f"{INDENT}{loc_name} : {loc_type} := {value_to_st(init)};")
            else:
                lines.append(f"{INDENT}{loc_name} : {loc_type};")
        lines.append("END_VAR")

    lines.append("")

    # Body statements
    for s in body:
        lines += convert_statement(s, 0)

    lines.append("")
    lines.append("END_FUNCTION_BLOCK")
    return "\n".join(lines)


def convert_function(obj: Dict[str, Any]) -> str:
    """
    Convert a 'function' JSON object to IEC 61131-3 FUNCTION ... END_FUNCTION block.
    
    Note: 'return' statements in body are converted to:
        FunctionName := expression;
        RETURN;
    """
    fn = obj.get("function")
    if not fn:
        raise GeneratorError("No 'function' key found in object")
    
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
            inp_name = inp.get("name", "unknown")
            inp_type = inp.get("datatype", "ANY")
            lines.append(f"{INDENT}{inp_name} : {inp_type};")
        lines.append("END_VAR")

    # VAR (locals)
    if locals_:
        lines.append("VAR")
        for loc in locals_:
            loc_name = loc.get("name", "unknown")
            loc_type = loc.get("datatype", "ANY")
            init = loc.get("initialValue")
            if init is not None:
                lines.append(f"{INDENT}{loc_name} : {loc_type} := {value_to_st(init)};")
            else:
                lines.append(f"{INDENT}{loc_name} : {loc_type};")
        lines.append("END_VAR")

    lines.append("")  # Blank line before body

    # Body statements (with special handling for "return")
    for s in body:
        if s.get("type") == "return":
            expr = s.get("expression", "0")
            # Assign to function name and emit RETURN
            lines.append(f"{name} := {expr};")
            lines.append("RETURN;")
        else:
            lines += convert_statement(s, 0)

    lines.append("")
    lines.append("END_FUNCTION")
    return "\n".join(lines)


def convert_top(obj: Any) -> str:
    """
    Convert top-level JSON object(s) to ST code.
    
    Args:
        obj: Can be:
            - dict with 'program'
            - dict with 'functionBlock'
            - dict with 'function'
            - list of such dicts
    
    Returns:
        Generated ST code as string
    
    Raises:
        GeneratorError: If input format is invalid
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
        
        # Handle unwrapped objects (user may pass without wrapper key)
        if "name" in obj and "declarations" in obj and "statements" in obj:
            outputs.append(convert_program({"program": obj}))
        if "name" in obj and "returnType" in obj and "body" in obj:
            outputs.append(convert_function({"function": obj}))
        
        if not outputs:
            raise GeneratorError(
                f"Input dict doesn't look like a program/functionBlock/function. "
                f"Keys: {', '.join(obj.keys())}"
            )
        return "\n\n".join(outputs)

    raise GeneratorError(f"Unsupported top-level JSON type: {type(obj)}")


def generator(data: Any) -> str:
    """
    Main entry point for code generation.
    
    Args:
        data: JSON data representing the intermediate code
    
    Returns:
        Generated IEC 61131-3 Structured Text code
    
    Raises:
        GeneratorError: If generation fails
    """
    try:
        st_text = convert_top(data)
        return st_text
    except GeneratorError:
        raise
    except Exception as e:
        logger.error(f"Error converting JSON to ST: {e}", exc_info=True)
        raise GeneratorError(f"Failed to generate code: {e}")
