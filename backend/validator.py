import re
from typing import List, Dict, Tuple, Any, Optional

# ====================== Utilities & Normalization ======================

IDENT = r"[A-Za-z_][A-Za-z0-9_]*"

def uc(s: Optional[str]) -> str:
    return (s or "").strip().upper()

def base_var_name(name: str) -> str:
    """Left-most identifier before any indexing or field access."""
    return re.split(r"[\[\].]", str(name).strip())[0]

# Heuristic: treat unknown bare words as string literal per user's legacy behavior
# (e.g., VANAKKAM -> STRING). This matches prior validator expectations.
BARE_WORD_AS_STRING = True

# ====================== Datatype helpers ======================

# Elementary + Generics
BASE_SCALAR_TYPES = {
    # Elementary
    "BOOL","SINT","INT","DINT","LINT","USINT","UINT","UDINT","ULINT",
    "REAL","LREAL","BYTE","WORD","DWORD","LWORD",
    "CHAR","WCHAR","STRING","WSTRING",
    "TIME","DATE","TIME_OF_DAY","DATE_AND_TIME",
    # Generic
    "ANY","ANY_DERIVED","ANY_ELEMENTARY","ANY_MAGNITUDE",
    "ANY_NUM","ANY_REAL","ANY_INT","ANY_BIT","ANY_STRING","ANY_DATE",
}

# Built-in FBs (known names)
BUILTIN_FB_TYPES = {
    "TON","TOF","TP","CTU","CTD","CTUD","R_TRIG","F_TRIG",
    "PID","PI","PD","MC_MOVEABSOLUTE","MC_MOVERELATIVE","MC_HOME","MC_STOP","MC_RESET",
    "TSEND","TRCV","TCON","TDISCON","READ_VAR","WRITE_VAR"
}

# Optional pin maps for a few common FBs (strict)
FB_PIN_TYPES: Dict[str, Dict[str, Dict[str, str]]] = {
    "TON": {
        "inputs": {"IN": "BOOL", "PT": "TIME"},
        "outputs": {"Q": "BOOL", "ET": "TIME"}
    },
    "TOF": {
        "inputs": {"IN": "BOOL", "PT": "TIME"},
        "outputs": {"Q": "BOOL", "ET": "TIME"}
    },
    "TP": {
        "inputs": {"IN": "BOOL", "PT": "TIME"},
        "outputs": {"Q": "BOOL", "ET": "TIME"}
    },
    "CTU": {
        "inputs": {"CU": "BOOL", "PV": "INT"},
        "outputs": {"Q": "BOOL", "CV": "INT"}
    },
    "CTD": {
        "inputs": {"CD": "BOOL", "PV": "INT"},
        "outputs": {"Q": "BOOL", "CV": "INT"}
    },
    "CTUD": {
        "inputs": {"CU": "BOOL", "CD": "BOOL", "PV": "INT"},
        "outputs": {"QU": "BOOL", "QD": "BOOL", "CV": "INT"}
    },
}

# Families
INT_FAMILY = {"SINT","INT","DINT","LINT","USINT","UINT","UDINT","ULINT","BYTE","WORD","DWORD","LWORD"}
REAL_FAMILY = {"REAL","LREAL"}
STRING_FAMILY = {"STRING","WSTRING"}
DATE_FAMILY  = {"DATE"}
TIME_FAMILY  = {"TIME"}
TOD_FAMILY   = {"TIME_OF_DAY"}
DT_FAMILY    = {"DATE_AND_TIME"}
CHAR_FAMILY  = {"CHAR","WCHAR"}
BOOL_FAMILY  = {"BOOL"}

# String with length
RE_STRING_T = re.compile(r"^(STRING|WSTRING)(\[(\d+)\])?$", re.IGNORECASE)

# ARRAY grammar: supports multi-dim and nested base type
RE_ARRAY_T = re.compile(r"^ARRAY\[\s*\d+\s*\.\.\s*\d+(?:\s*,\s*\d+\s*\.\.\s*\d+)*\s*\]\s+OF\s+(.+)$", re.IGNORECASE)

# STRUCT grammar: STRUCT(Name : TYPE; Value : TYPE)
RE_STRUCT_T = re.compile(r"^STRUCT\((.*)\)$", re.IGNORECASE | re.DOTALL)


def is_array(dt: str) -> bool:
    return bool(RE_ARRAY_T.match(dt.strip()))

def is_struct(dt: str) -> bool:
    return bool(RE_STRUCT_T.match(dt.strip()))

def is_string_type(dt: str) -> bool:
    return bool(RE_STRING_T.fullmatch(dt.strip()))


def parse_array(dt: str) -> Tuple[bool, str, str]:
    """Return (ok, msg, base_type) for ARRAY[...] OF base."""
    m = RE_ARRAY_T.fullmatch(dt.strip())
    if not m:
        return False, f"Invalid ARRAY syntax: {dt}", ""
    return True, "", m.group(1).strip()


def parse_struct_fields(dt: str) -> Tuple[bool, str, Dict[str, str]]:
    m = RE_STRUCT_T.fullmatch(dt.strip())
    if not m:
        return False, f"Invalid STRUCT syntax: {dt}", {}
    payload = m.group(1)
    fields: Dict[str, str] = {}
    # split by semicolons
    for part in [p.strip() for p in payload.split(";") if p.strip()]:
        bits = [b.strip() for b in part.split(":")]
        if len(bits) != 2:
            return False, f"Invalid STRUCT field: '{part}'", {}
        fname, ftype = bits[0], bits[1]
        fields[fname] = ftype
    return True, "", fields


def validate_datatype(dt: str, known_types: set) -> Tuple[bool, str]:
    s = dt.strip()
    U = uc(s)
    if U in BASE_SCALAR_TYPES or U in BUILTIN_FB_TYPES or s in known_types:
        return True, ""
    if is_string_type(s):
        return True, ""
    if is_array(s):
        ok, msg, base = parse_array(s)
        if not ok: return False, msg
        return validate_datatype(base, known_types)
    if is_struct(s):
        ok, msg, fields = parse_struct_fields(s)
        if not ok: return False, msg
        for f_t in fields.values():
            ok2, msg2 = validate_datatype(f_t, known_types)
            if not ok2: return False, f"STRUCT field type error: {msg2}"
        return True, ""
    return False, f"Unknown datatype {dt}"

# ====================== Literal recognition ======================

RE_INT = re.compile(r"^[+-]?\d+$")
RE_REAL = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?$")
RE_BOOL = re.compile(r"^(TRUE|FALSE)$", re.IGNORECASE)
RE_STR  = re.compile(r'^(?:\"[^\"\\]*(?:\\.[^\"\\]*)*\"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')$')
RE_TIME = re.compile(r"^(T|TIME)#[A-Za-z0-9_:+-]+$", re.IGNORECASE)
RE_DATE = re.compile(r"^(D|DATE)#[A-Za-z0-9_:+-]+$", re.IGNORECASE)
RE_TOD  = re.compile(r"^(TOD|TIME_OF_DAY)#[A-Za-z0-9_:+-]+$", re.IGNORECASE)
RE_DT   = re.compile(r"^(DT|DATE_AND_TIME)#[A-Za-z0-9_:+-]+$", re.IGNORECASE)

# IEC base-specific (hex, bin) e.g., 16#FF, 2#1010
RE_BASED_INT = re.compile(r"^(2|8|10|16)#[0-9A-Fa-f_]+$")


def literal_type(tok: str) -> Optional[str]:
    s = tok.strip()
    if RE_BOOL.fullmatch(s):
        return "BOOL"
    if RE_INT.fullmatch(s) or RE_BASED_INT.fullmatch(s):
        return "INT"  # widthless integer; assignable to any INT_FAMILY
    if RE_REAL.fullmatch(s):
        return "REAL"
    if RE_STR.fullmatch(s):
        # Choose STRING for both '\'...\'' and "..."
        return "STRING"
    if RE_TIME.fullmatch(s):
        return "TIME"
    if RE_DATE.fullmatch(s):
        return "DATE"
    if RE_TOD.fullmatch(s):
        return "TIME_OF_DAY"
    if RE_DT.fullmatch(s):
        return "DATE_AND_TIME"
    return None

# ====================== Expression Parsing / Typing ======================

# Operators by precedence (low to high split)
LOGICAL_OR = [" OR "]
LOGICAL_AND = [" AND "]
COMPARE_OPS = ["<=", ">=", "<>", "=", "<", ">"]
ADD_OPS = ["+", "-"]
MUL_OPS = ["*", "/"]
UNARY_OPS = ["NOT", "+", "-"]


def strip_parens(expr: str) -> str:
    e = expr.strip()
    while e.startswith("(") and e.endswith(")"):
        # ensure they match at top-level
        depth = 0
        ok = True
        for i,ch in enumerate(e):
            if ch == '(': depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0 and i != len(e)-1:
                    ok = False; break
        if ok: e = e[1:-1].strip()
        else: break
    return e


def split_top(expr: str, ops: List[str]) -> Optional[Tuple[str, str, str]]:
    """Split expr at the rightmost top-level operator among ops.
    Returns (left, op, right) or None.
    """
    e = expr
    depth_p = depth_b = 0
    i = len(e) - 1
    while i >= 0:
        ch = e[i]
        if ch == ')': depth_p += 1; i -= 1; continue
        if ch == '(': depth_p -= 1; i -= 1; continue
        if ch == ']': depth_b += 1; i -= 1; continue
        if ch == '[': depth_b -= 1; i -= 1; continue
        if depth_p == 0 and depth_b == 0:
            # try multi-char ops first by longest first
            for op in sorted(ops, key=len, reverse=True):
                if i - len(op) + 1 >= 0 and e[i-len(op)+1:i+1].upper() == op:
                    left = e[:i-len(op)+1].strip()
                    right = e[i+1:].strip()
                    return left, op.strip(), right
        i -= 1
    return None


def peel_array_once(dt: str) -> Optional[str]:
    """Given ARRAY[...] OF T -> T; else None."""
    ok, msg, base = parse_array(dt) if is_array(dt) else (False, "", "")
    return base if ok else None


def get_struct_field_type(dt: str, field: str) -> Optional[str]:
    ok, msg, fields = parse_struct_fields(dt) if is_struct(dt) else (False, "", {})
    if not ok: return None
    return fields.get(field)


def normalize_string_family(dt: str) -> str:
    m = RE_STRING_T.fullmatch(dt.strip())
    if m:
        return m.group(1).upper()  # STRING or WSTRING
    return dt.strip()


def is_numeric(dt: str) -> bool:
    U = uc(normalize_string_family(dt))
    return (U in INT_FAMILY) or (U in REAL_FAMILY)


def family_of(dt: str) -> str:
    U = uc(normalize_string_family(dt))
    if U in BOOL_FAMILY: return "BOOL"
    if U in INT_FAMILY:  return "INT"
    if U in REAL_FAMILY: return "REAL"
    if U in STRING_FAMILY: return "STRING"
    if U in DATE_FAMILY: return "DATE"
    if U in TIME_FAMILY: return "TIME"
    if U in TOD_FAMILY: return "TIME_OF_DAY"
    if U in DT_FAMILY: return "DATE_AND_TIME"
    if U in CHAR_FAMILY: return "CHAR"
    if is_array(U): return "ARRAY"
    if is_struct(U): return "STRUCT"
    return U


def type_assignable(expected: str, actual: str) -> bool:
    """Strict assignability across IEC families."""
    E = uc(normalize_string_family(expected))
    A = uc(normalize_string_family(actual))

    # ANY* generics accept anything
    if E in {"ANY","ANY_DERIVED","ANY_ELEMENTARY","ANY_MAGNITUDE","ANY_NUM","ANY_REAL","ANY_INT","ANY_BIT","ANY_STRING","ANY_DATE"}:
        return True

    # Exact or same family rules
    if E == A:
        return True

    # Integer family accepts any integer literal/var
    if E in INT_FAMILY and A in INT_FAMILY:
        return True

    # REAL/LREAL accept INT-family
    if E in REAL_FAMILY and (A in REAL_FAMILY or A in INT_FAMILY):
        return True

    # STRING[n] compatible with STRING
    if is_string_type(expected) and family_of(actual) == "STRING":
        return True

    # CHAR/WCHAR only self
    if E in CHAR_FAMILY and A in CHAR_FAMILY and E == A:
        return True

    # Date/Time exact types only
    if E in {"TIME","DATE","TIME_OF_DAY","DATE_AND_TIME"}:
        return E == A

    return False

# ---------------- Variable / Member Type Resolution ----------------

MEMBER_TOKEN = re.compile(r"(\.[A-Za-z_][A-Za-z0-9_]*)|(\[[^\]]*\])")


def resolve_member_type(var_name: str, var_types: Dict[str, str]) -> Optional[str]:
    """Resolve type of an expression like matrix[i][j] or Sensor.Value.
    Starts with declared base type and peels arrays/fields accordingly.
    """
    s = var_name.strip()
    m0 = re.match(rf"^({IDENT})", s)
    if not m0:
        return None
    base = m0.group(1)
    if base not in var_types:
        return None
    t = var_types[base]
    rest = s[len(base):]
    # Iterate over .field or [index]
    for m in MEMBER_TOKEN.finditer(rest):
        token = m.group(0)
        if token.startswith("["):
            # index -> peel one array dimension
            elem = peel_array_once(t)
            if not elem:
                return None
            t = elem
        elif token.startswith("."):
            field = token[1:]
            ftype = get_struct_field_type(t, field)
            if not ftype:
                return None
            t = ftype
    return t

# ---------------- Expression Type Inference ----------------

def infer_expr_type(expr: str, var_types: Dict[str, str], functions: Dict[str, Dict[str, Any]]) -> Optional[str]:
    e = strip_parens(expr)
    if not e:
        return None

    # literals
    lit = literal_type(e)
    if lit:
        return lit

    # binary splits by precedence
    for ops in (LOGICAL_OR, LOGICAL_AND, COMPARE_OPS, ADD_OPS, MUL_OPS):
        sp = split_top(e, ops)
        if sp:
            L, op, R = sp
            lt = infer_expr_type(L, var_types, functions)
            rt = infer_expr_type(R, var_types, functions)
            if lt is None or rt is None:
                return None
            uop = op.upper()
            if uop in ("OR", "AND"):
                return "BOOL" if (lt == "BOOL" and rt == "BOOL") else None
            if uop in ("<=", ">=", "<>", "=", "<", ">"):
                # comparisons
                # numeric compare or string-equality or bool-equality allowed
                if (is_numeric(lt) and is_numeric(rt)):
                    return "BOOL"
                if family_of(lt) == family_of(rt) and family_of(lt) in {"STRING","BOOL","TIME","DATE","TIME_OF_DAY","DATE_AND_TIME","CHAR"}:
                    return "BOOL"
                return None
            if uop in ("+", "-", "*", "/"):
                # numeric arithmetic
                if is_numeric(lt) and is_numeric(rt):
                    if lt in REAL_FAMILY or rt in REAL_FAMILY or lt == "REAL" or rt == "REAL":
                        return "REAL"
                    # both integer families -> keep integer
                    return "INT"
                # string concatenation
                if uop == "+" and family_of(lt) == family_of(rt) == "STRING":
                    return "STRING"
                return None

    # unary NOT / +/-
    ue = e
    for u in ("NOT", "+", "-"):
        if ue.upper().startswith(u + " "):
            rest = ue[len(u):].strip()
            t = infer_expr_type(rest, var_types, functions)
            if t is None:
                return None
            if u == "NOT":
                return "BOOL" if t == "BOOL" else None
            # +/- numeric only
            return t if is_numeric(t) else None

    # function call in expression: name(args)
    mfunc = re.match(rf"^({IDENT})\((.*)\)$", e)
    if mfunc:
        fname = mfunc.group(1)
        if fname in functions:
            return functions[fname].get("returnType")
        # Unknown function -> cannot infer
        return None

    # variable/member reference
    mvar = re.match(rf"^{IDENT}(?:\[[^\]]*\]|\.[A-Za-z_][A-Za-z0-9_]*)*\s*$", e)
    if mvar:
        t = resolve_member_type(e, var_types)
        # If not resolvable but base exists, return its type
        if t: return t
        base = base_var_name(e)
        if base in var_types:
            return var_types[base]
        # Heuristic: unknown bare word -> STRING (to match legacy behavior)
        if BARE_WORD_AS_STRING:
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", e) and base not in var_types:
                return "STRING"
        return None

    # Fallback: unknown token -> if heuristic on, STRING
    if BARE_WORD_AS_STRING:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", e):
            return "STRING"

    return None

# ---------------- Statement Checker ----------------

def expected_type_from_target(target: str, var_types: Dict[str, str]) -> Optional[str]:
    """Compute the expected type for an assignment target (handles array index and struct fields)."""
    return resolve_member_type(target, var_types)


def stmtChecker(stmt: dict,
                vars_in_scope: set,
                functions: Dict[str, Dict[str, Any]],
                fb_defs: Dict[str, Dict[str, Any]],
                var_types: Dict[str, str]) -> Tuple[bool, str]:
    typ = stmt.get("type")

    if typ == "assignment":
        target = stmt.get("target")
        if not target:
            return False, "Assignment missing target"
        base = base_var_name(target)
        if base not in vars_in_scope:
            return False, f"Variable {target} not declared"
        expected = expected_type_from_target(target, var_types)
        if expected is None:
            return False, f"Cannot resolve target type for '{target}'"
        expr = stmt.get("expression")
        if expr is None:
            return False, "Assignment missing expression"
        et = infer_expr_type(expr, var_types, functions)
        if et is None:
            return False, f"Unresolvable expression type for '{expr}'"
        if not type_assignable(expected, et):
            return False, f"Type mismatch: expected {expected}, got {et} in expression '{expr}'"
        return True, ""

    if typ == "if":
        cond_t = infer_expr_type(stmt.get("condition", ""), var_types, functions)
        if cond_t != "BOOL":
            return False, "If condition must be BOOL"
        for s in stmt.get("then", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        for s in stmt.get("else", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        return True, ""

    if typ == "case":
        # selector can be INT-family, BOOL, STRING, etc. We'll just ensure it is typable
        sel_t = infer_expr_type(stmt.get("selector", ""), var_types, functions)
        if sel_t is None:
            return False, "Case selector has unknown type"
        for c in stmt.get("cases", []):
            for s in c.get("statements", []):
                ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
                if not ok: return ok, msg
        for s in stmt.get("else", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        return True, ""

    if typ == "for":
        it = stmt.get("iterator")
        loop_scope = set(vars_in_scope)
        if it:
            loop_scope.add(it)
            # iterator is INT-family (commonly INT); we add as INT for typing of expressions using it
            if it not in var_types:
                var_types[it] = "INT"
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, loop_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        return True, ""

    if typ == "while":
        cond_t = infer_expr_type(stmt.get("condition", ""), var_types, functions)
        if cond_t != "BOOL":
            return False, "While condition must be BOOL"
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        return True, ""

    if typ == "repeat":
        until_t = infer_expr_type(stmt.get("until", ""), var_types, functions)
        if until_t != "BOOL":
            return False, "Repeat 'until' must be BOOL"
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
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
        # Type-check args against declared input types when available
        in_types = functions[fname].get("inputTypes", [])
        for a, et in zip(args, in_types):
            at = infer_expr_type(a, var_types, functions)
            if at is None:
                base = base_var_name(a)
                if base not in var_types and not literal_type(a):
                    return False, f"Function '{fname}' arg '{a}' not declared"
            else:
                if not type_assignable(et, at):
                    return False, f"Function '{fname}' arg type mismatch: expected {et}, got {at}"
        return True, ""

    if typ == "fbCall":
        inst = stmt.get("name")
        if inst not in vars_in_scope:
            return False, f"fbCall instance '{inst}' is not declared"
        inst_type = var_types.get(inst)
        U = uc(inst_type)
        # User-defined FB
        if inst_type in fb_defs:
            sig = fb_defs[inst_type]
            # inputs
            for k, v in stmt.get("inputs", {}).items():
                if k not in sig["inputs"]:
                    return False, f"fbCall '{inst}': unknown input '{k}' for FB '{inst_type}'"
                # type check if we know input type
                etype = sig["inputTypes"].get(k)
                if etype:
                    at = infer_expr_type(v, var_types, functions)
                    if at is None:
                        base = base_var_name(v)
                        if base not in vars_in_scope and not literal_type(v):
                            return False, f"fbCall '{inst}': input '{k}' maps to undeclared '{v}'"
                    else:
                        if not type_assignable(etype, at):
                            return False, f"fbCall '{inst}': input '{k}' expects {etype}, got {at}"
            # outputs
            for k, v in stmt.get("outputs", {}).items():
                if k not in sig["outputs"]:
                    return False, f"fbCall '{inst}': unknown output '{k}' for FB '{inst_type}'"
                base = base_var_name(v)
                if base not in vars_in_scope:
                    return False, f"fbCall '{inst}': output '{k}' maps to undeclared '{v}'"
                # type check if we know output type
                otype = sig["outputTypes"].get(k)
                if otype:
                    t_target = resolve_member_type(v, var_types)
                    if t_target is None:
                        return False, f"fbCall '{inst}': cannot resolve output target '{v}'"
                    if not type_assignable(t_target, otype):
                        return False, f"fbCall '{inst}': output '{k}' of type {otype} not assignable to {t_target}"
            return True, ""
        # Built-in FB – if we know pins, enforce
        if U in FB_PIN_TYPES:
            pins = FB_PIN_TYPES[U]
            for k, v in stmt.get("inputs", {}).items():
                if k not in pins["inputs"]:
                    return False, f"fbCall '{inst}': unknown input '{k}' for FB '{inst_type}'"
                etype = pins["inputs"][k]
                at = infer_expr_type(v, var_types, functions)
                if at is None:
                    base = base_var_name(v)
                    if base not in vars_in_scope and not literal_type(v):
                        return False, f"fbCall '{inst}': input '{k}' maps to undeclared '{v}'"
                else:
                    if not type_assignable(etype, at):
                        return False, f"fbCall '{inst}': input '{k}' expects {etype}, got {at}"
            for k, v in stmt.get("outputs", {}).items():
                if k not in pins["outputs"]:
                    return False, f"fbCall '{inst}': unknown output '{k}' for FB '{inst_type}'"
                otype = pins["outputs"][k]
                base = base_var_name(v)
                if base not in vars_in_scope:
                    return False, f"fbCall '{inst}': output '{k}' maps to undeclared '{v}'"
                t_target = resolve_member_type(v, var_types)
                if t_target is None:
                    return False, f"fbCall '{inst}': cannot resolve output target '{v}'"
                if not type_assignable(t_target, otype):
                    return False, f"fbCall '{inst}': output '{k}' of type {otype} not assignable to {t_target}"
            return True, ""
        # Unknown built-in – only existence checks
        for k, v in stmt.get("inputs", {}).items():
            if not literal_type(v):
                base = base_var_name(v)
                if base not in vars_in_scope:
                    return False, f"fbCall '{inst}': input '{k}' maps to undeclared '{v}'"
        for k, v in stmt.get("outputs", {}).items():
            base = base_var_name(v)
            if base not in vars_in_scope:
                return False, f"fbCall '{inst}': output '{k}' maps to undeclared '{v}'"
        return True, ""

    if typ == "return":
        # Return expression typing will be verified in function validation with expected type
        return True, ""

    # Unknown or empty -> allow (future constructs)
    return True, ""

# ---------------- Main Validator ----------------

def validator(intermediate: List[Dict[str, Any]]) -> Tuple[bool, str]:
    functions: Dict[str, Dict[str, Any]] = {}
    fb_defs: Dict[str, Dict[str, Any]] = {}

    # Pass 1: collect signatures (functions + FBs)
    for block in intermediate:
        key = list(block.keys())[0]
        if key == "function":
            f = block["function"]
            fname = f.get("name")
            if not fname or not f.get("returnType"):
                return False, "Function missing name/returnType"
            input_names = [i["name"] for i in f.get("inputs", [])]
            input_types = [i["datatype"] for i in f.get("inputs", [])]
            functions[fname] = {"inputs": input_names, "inputTypes": input_types, "returnType": f["returnType"]}
        elif key == "functionBlock":
            fb = block["functionBlock"]
            fbname = fb.get("name")
            if not fbname:
                return False, "FunctionBlock missing name"
            # map pins -> types
            fb_defs[fbname] = {
                "inputs": [i["name"] for i in fb.get("inputs", [])],
                "outputs": [o["name"] for o in fb.get("outputs", [])],
                "locals": [l["name"] for l in fb.get("locals", [])],
                "inputTypes": {i["name"]: i["datatype"] for i in fb.get("inputs", [])},
                "outputTypes": {o["name"]: o["datatype"] for o in fb.get("outputs", [])},
            }

    known_types = set(BASE_SCALAR_TYPES) | set(BUILTIN_FB_TYPES) | set(fb_defs.keys())

    # Pass 2: validate blocks
    for block in intermediate:
        blockType = list(block.keys())[0]
        if blockType not in ("function","functionBlock","program"):
            return False, f"Invalid block type: {blockType}"

        if blockType == "function":
            f = block["function"]
            # validate input types + return type
            for dt in [*f.get("inputs", []), {"datatype": f.get("returnType")}]:
                ok, msg = validate_datatype(dt["datatype"], known_types)
                if not ok:
                    return False, f"Function '{f['name']}' type error: {msg}"
            scope = {i["name"] for i in f.get("inputs", [])}
            var_types = {i["name"]: i["datatype"] for i in f.get("inputs", [])}
            # body
            for s in f.get("body", []):
                if s.get("type") == "return":
                    t = infer_expr_type(s.get("expression",""), var_types, functions)
                    if t is None or not type_assignable(f.get("returnType"), t):
                        return False, f"Return type mismatch: expected {f.get('returnType')}, got {t}"
                else:
                    ok, msg = stmtChecker(s, scope, functions, fb_defs, var_types)
                    if not ok: return False, msg

        elif blockType == "functionBlock":
            fb = block["functionBlock"]
            # validate interface/locals types
            for arr, label in (("inputs","input"),("outputs","output"),("locals","local")):
                for item in fb.get(arr, []):
                    ok, msg = validate_datatype(item["datatype"], known_types)
                    if not ok:
                        return False, f"FunctionBlock '{fb['name']}' {label} '{item['name']}': {msg}"
            scope = set([*(n for n in fb_defs[fb["name"]]["inputs"]), *(n for n in fb_defs[fb["name"]]["outputs"]), *(n for n in fb_defs[fb["name"]]["locals"])])
            var_types = {}
            for arr in ("inputs","outputs","locals"):
                for item in fb.get(arr, []):
                    var_types[item["name"]] = item["datatype"]
            for s in fb.get("body", []):
                ok, msg = stmtChecker(s, scope, functions, fb_defs, var_types)
                if not ok: return False, msg

        elif blockType == "program":
            prog = block["program"]
            if "declarations" not in prog:
                return False, f"Program '{prog.get('name','<unnamed>')}' missing declarations"
            scope: set = set()
            var_types: Dict[str, str] = {}
            for d in prog.get("declarations", []):
                ok, msg = validate_datatype(d["datatype"], known_types)
                if not ok:
                    return False, f"Program '{prog['name']}' declaration '{d['name']}': {msg}"
                scope.add(d["name"])
                var_types[d["name"]] = d["datatype"]
            for s in prog.get("statements", []):
                ok, msg = stmtChecker(s, scope, functions, fb_defs, var_types)
                if not ok: return False, msg

    return True, "Build Success ✅"