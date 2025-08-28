import re
from typing import List, Dict, Tuple, Any

def base_var_name(name: str) -> str:
    """Extract the left-most identifier (array/field safe)."""
    return re.split(r"[\[\].]", str(name).strip())[0]

def is_literal(tok: Any) -> bool:
    """Rough literal check: numbers, booleans, quoted strings, time literals."""
    if isinstance(tok, (int, float, bool)):
        return True
    if not isinstance(tok, str):
        return False
    s = tok.strip()
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", s):   # int/float
        return True
    if s.upper() in ("TRUE", "FALSE"):
        return True
    if re.fullmatch(r'"[^"]*"', s):
        return True
    if re.fullmatch(r"[A-Z]#.+", s, re.IGNORECASE):  # e.g., T#5s
        return True
    return False


def is_array(datatype: str) -> bool:
    return datatype.strip().upper().startswith("ARRAY")

def is_struct(datatype: str) -> bool:
    return datatype.strip().upper().startswith("STRUCT")

def is_string_type(datatype: str) -> bool:
    """Accept STRING, WSTRING, STRING[n], WSTRING[n] (case-insensitive)."""
    return bool(re.fullmatch(r"(STRING|WSTRING)(\[\d+\])?", datatype.strip(), re.IGNORECASE))

def _validate_array(datatype: str) -> Tuple[bool, str, str]:
    """
    Parses ARRAY[...] OF <base> and returns (ok, msg, base_type).
    Supports multi-dimensional bounds.
    """
    m = re.fullmatch(
        r"ARRAY\[\s*\d+\s*\.\.\s*\d+(?:\s*,\s*\d+\s*\.\.\s*\d+)*\s*\]\s+OF\s+(.+)",
        datatype.strip(),
        re.IGNORECASE
    )
    if not m:
        return False, f"Invalid ARRAY syntax: {datatype}", ""
    base_type = m.group(1).strip()
    return True, "", base_type

def validate_array_datatype(datatype: str, known_types: set) -> Tuple[bool, str]:
    ok, msg, base = _validate_array(datatype)
    if not ok:
        return False, msg
    return validate_datatype(base, known_types)

def _split_struct_fields(payload: str) -> List[str]:
    """
    Split 'Name: TYPE; Other: TYPE' into fields safely.
    (Semicolons only appear between fields in our grammar.)
    """
    parts = [p.strip() for p in payload.split(";")]
    return [p for p in parts if p]

def validate_struct_datatype(datatype: str, known_types: set) -> Tuple[bool, str]:
    m = re.fullmatch(r"STRUCT\((.+)\)", datatype.strip(), re.IGNORECASE | re.DOTALL)
    if not m:
        return False, f"Invalid STRUCT syntax: {datatype}"
    fields_blob = m.group(1)
    for field in _split_struct_fields(fields_blob):
        bits = [b.strip() for b in field.split(":")]
        if len(bits) != 2:
            return False, f"Invalid STRUCT field: '{field}'"
        f_type = bits[1]
        ok, msg = validate_datatype(f_type, known_types)
        if not ok:
            return False, f"STRUCT field type error in '{field}': {msg}"
    return True, ""

def validate_datatype(datatype: str, known_types: set) -> Tuple[bool, str]:
    dt = datatype.strip()
    if dt.upper() in known_types:
        return True, ""
    if is_string_type(dt):
        return True, ""
    if is_array(dt):
        return validate_array_datatype(dt, known_types)
    if is_struct(dt):
        return validate_struct_datatype(dt, known_types)
    # Allow user-defined FB types (added to known_types in pass 1).
    if dt in known_types:
        return True, ""
    return False, f"Unknown datatype {datatype}"


def stmtChecker(stmt: dict,
                vars_in_scope: set,
                functions: Dict[str, Dict[str, Any]]) -> Tuple[bool, str]:
    typ = stmt.get("type")

    if typ == "assignment":
        target = stmt.get("target")
        if target is None:
            return False, "Assignment missing target"
        base = base_var_name(target)
        if base not in vars_in_scope:
            return False, f"Variable {target} not declared"
        return True, ""

    if typ == "if":
        if "condition" not in stmt:
            return False, "If without condition"
        for s in stmt.get("then", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions)
            if not ok: return ok, msg
        for s in stmt.get("else", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions)
            if not ok: return ok, msg
        return True, ""

    if typ == "case":
        if "selector" not in stmt or "cases" not in stmt:
            return False, "Case missing selector/cases"
        for case in stmt["cases"]:
            for s in case.get("statements", []):
                ok, msg = stmtChecker(s, vars_in_scope, functions)
                if not ok: return ok, msg
        for s in stmt.get("else", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions)
            if not ok: return ok, msg
        return True, ""

    if typ == "for":
        it = stmt.get("iterator")
        loop_scope = set(vars_in_scope)
        if it:
            loop_scope.add(it)
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, loop_scope, functions)
            if not ok: return ok, msg
        return True, ""

    if typ == "while":
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions)
            if not ok: return ok, msg
        return True, ""

    if typ == "repeat":
        if "until" not in stmt:
            return False, "Repeat missing until"
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions)
            if not ok: return ok, msg
        return True, ""

    if typ == "functionCall":
        fname = stmt.get("name")
        args = stmt.get("arguments", [])
        if fname not in functions:
            return False, f"Function '{fname}' not defined"
        expected = functions[fname]["inputs"]
        if len(args) != len(expected):
            return False, f"Function '{fname}' arg count mismatch (got {len(args)}, expected {len(expected)})"
        # Optionally check each arg token base is declared or literal
        for a in args:
            if is_literal(a):
                continue
            base = base_var_name(a)
            if base not in vars_in_scope:
                return False, f"Function '{fname}' arg '{a}' not declared"
        return True, ""

    if typ == "fbCall":
        # Basic structural validation is done in program validation where we know the instance type.
        return True, ""

    if typ == "return":
        if "expression" not in stmt:
            return False, "Return without expression"
        return True, ""

    return False, f"Unknown statement type {typ}"

# ----------------------- Main Validator -----------------------

def validator(intermediate: List[Dict[str, Any]]) -> Tuple[bool, str]:
    # Base/IEC & built-in FB types
    base_scalar_types = {
        # Elementary
        "BOOL","SINT","INT","DINT","LINT","USINT","UINT","UDINT","ULINT",
        "REAL","LREAL","BYTE","WORD","DWORD","LWORD",
        "CHAR","WCHAR","STRING","WSTRING",
        "TIME","DATE","TIME_OF_DAY","DATE_AND_TIME",
        # Generic (allow as names)
        "ANY","ANY_DERIVED","ANY_ELEMENTARY","ANY_MAGNITUDE",
        "ANY_NUM","ANY_REAL","ANY_INT","ANY_BIT","ANY_STRING","ANY_DATE",
    }
    builtin_fb_types = {
        "TON","TOF","TP","CTU","CTD","CTUD","R_TRIG","F_TRIG",
        "PID","PI","PD","MC_MOVEABSOLUTE","MC_MOVERELATIVE","MC_HOME","MC_STOP","MC_RESET",
        "TSEND","TRCV","TCON","TDISCON","READ_VAR","WRITE_VAR"
    }

    # Pass 1: collect signatures for functions and function blocks
    functions: Dict[str, Dict[str, Any]] = {}
    fb_defs: Dict[str, Dict[str, Any]] = {}
    for block in intermediate:
        key = list(block.keys())[0]
        if key == "function":
            f = block["function"]
            fname = f.get("name")
            inputs = [i["name"] for i in f.get("inputs", [])]
            if fname:
                functions[fname] = {"inputs": inputs, "returnType": f.get("returnType")}
        elif key == "functionBlock":
            fb = block["functionBlock"]
            fbname = fb.get("name")
            if fbname:
                fb_defs[fbname] = {
                    "inputs": [i["name"] for i in fb.get("inputs", [])],
                    "outputs": [o["name"] for o in fb.get("outputs", [])],
                    "locals": [l["name"] for l in fb.get("locals", [])],
                }

    # Known type names (uppercased for scalars; keep FB names case-sensitive)
    known_types = set(t.upper() for t in base_scalar_types) | set(builtin_fb_types) | set(fb_defs.keys())

    # Pass 2: validate blocks
    for block in intermediate:
        blockType = list(block.keys())[0]
        if blockType not in ("function", "functionBlock", "program"):
            return False, f"Invalid block type: {blockType}"

        if blockType == "function":
            f = block["function"]
            if "name" not in f or "returnType" not in f:
                return False, "Function missing name/returnType"
            # Validate input datatypes
            for inp in f.get("inputs", []):
                ok, msg = validate_datatype(inp["datatype"], known_types)
                if not ok:
                    return False, f"Function '{f['name']}' input '{inp['name']}': {msg}"
            # Validate body (scope = inputs only)
            scope = set(i["name"] for i in f.get("inputs", []))
            for s in f.get("body", []):
                ok, msg = stmtChecker(s, scope, functions)
                if not ok: return False, msg

        elif blockType == "functionBlock":
            fb = block["functionBlock"]
            if "name" not in fb or "body" not in fb:
                return False, "FunctionBlock missing name/body"
            # Validate interface/locals datatypes
            for arr in ("inputs", "outputs", "locals"):
                for item in fb.get(arr, []):
                    ok, msg = validate_datatype(item["datatype"], known_types)
                    if not ok:
                        return False, f"FunctionBlock '{fb['name']}' {arr[:-1]} '{item['name']}': {msg}"
            # Scope = inputs + outputs + locals
            scope = set(n for n in fb_defs[fb["name"]]["inputs"])
            scope |= set(n for n in fb_defs[fb["name"]]["outputs"])
            scope |= set(n for n in fb_defs[fb["name"]]["locals"])
            for s in fb["body"]:
                ok, msg = stmtChecker(s, scope, functions)
                if not ok: return False, msg

        elif blockType == "program":
            prog = block["program"]
            if "declarations" not in prog:
                return False, f"Program '{prog.get('name','<unnamed>')}' missing declarations"
            # Build symbol table for program
            scope = set()
            var_types: Dict[str, str] = {}
            for decl in prog.get("declarations", []):
                name = decl["name"]
                dtype = decl["datatype"]
                ok, msg = validate_datatype(dtype, known_types)
                if not ok:
                    return False, f"Program '{prog['name']}' declaration '{name}': {msg}"
                scope.add(name)
                var_types[name] = dtype

            # Validate statements
            for s in prog.get("statements", []):
                if s.get("type") == "fbCall":
                    inst = s.get("name")
                    if inst not in scope:
                        return False, f"fbCall instance '{inst}' is not declared"
                    inst_type = var_types.get(inst)
                    if inst_type not in fb_defs and inst_type.upper() not in builtin_fb_types:
                        return False, f"fbCall instance '{inst}' has unknown FB type '{inst_type}'"
                    # If user-defined FB, check IO maps
                    if inst_type in fb_defs:
                        fb_sig = fb_defs[inst_type]
                        # Check input keys exist
                        for k, v in s.get("inputs", {}).items():
                            if k not in fb_sig["inputs"]:
                                return False, f"fbCall '{inst}': unknown input '{k}' for FB '{inst_type}'"
                            if not is_literal(v):
                                base = base_var_name(v)
                                if base not in scope:
                                    return False, f"fbCall '{inst}': input '{k}' maps to undeclared '{v}'"
                        # Check output keys exist and targets declared
                        for k, v in s.get("outputs", {}).items():
                            if k not in fb_sig["outputs"]:
                                return False, f"fbCall '{inst}': unknown output '{k}' for FB '{inst_type}'"
                            base = base_var_name(v)
                            if base not in scope:
                                return False, f"fbCall '{inst}': output '{k}' maps to undeclared '{v}'"
                    # Built-in FBs: do lightweight checks only
                else:
                    ok, msg = stmtChecker(s, scope, functions)
                    if not ok: return False, msg

    return True, "Build Success ✅"