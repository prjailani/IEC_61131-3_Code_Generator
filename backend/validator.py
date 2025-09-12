
import re
from typing import List, Dict, Tuple, Any, Optional

import json
import os

IDENT = r"[A-Za-z_][A-Za-z0-9_]*"

def uc(s: Optional[str]) -> str:
    return (s or "").strip().upper()

def base_var_name(name: str) -> str:
    """Left-most identifier before any indexing or field access."""
    return re.split(r"[\[\].]", str(name).strip())[0]

# Heuristic: treat unknown bare words as string literal per user's legacy behavior
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


# # ====================== Literal recognition ======================

RE_INT = re.compile(r"^[+-]?\d+$")
RE_REAL = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?$")
RE_BOOL = re.compile(r"^(TRUE|FALSE)$", re.IGNORECASE)
RE_STR  = re.compile(r'^(?:"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')$')

# Strict IEC-61131 literals
# TIME: optional sign, one or more duration components (D, H, M, S, MS)
RE_TIME = re.compile(
    r"^(T|TIME)#[+-]?(?:\d+D)?(?:\d+H)?(?:\d+M)?(?:\d+S)?(?:\d+MS)?$", re.IGNORECASE
)

# DATE: YYYY-MM-DD
RE_DATE = re.compile(
    r"^(D|DATE)#[0-9]{4}-[0-9]{2}-[0-9]{2}$", re.IGNORECASE
)

RE_TOD = re.compile(
    r"^(TOD|TIME_OF_DAY)#(?:[01]?\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d{1,3})?$",
    re.IGNORECASE,
)

# DATE_AND_TIME: YYYY-MM-DD-HH:MM:SS(.mmm optional)
RE_DT = re.compile(
    r"^(DT|DATE_AND_TIME)#[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-2][0-9]:[0-5][0-9]:[0-5][0-9](?:\.\d{1,3})?$",
    re.IGNORECASE,
)

# IEC base-specific (hex, bin) e.g., 16#FF, 2#1010
RE_BASED_INT = re.compile(r"^(2|8|10|16)#[0-9A-Fa-f_]+$")


def literal_type(tok: str) -> Optional[str]:
    s = tok.strip()
    if RE_BOOL.fullmatch(s):
        return "BOOL"
    if RE_INT.fullmatch(s) or RE_BASED_INT.fullmatch(s):
        return "INT"
    if RE_REAL.fullmatch(s):
        return "REAL"
    if RE_STR.fullmatch(s):
        
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

LOGICAL_OR = ["OR"]
LOGICAL_AND = ["AND"]

COMPARE_OPS = ["<=", ">=", "<>", "!=", "=", "<", ">"]
ADD_OPS = ["+", "-"]
MUL_OPS = ["*", "/"]
UNARY_OPS = ["NOT", "+", "-"]  


def normalize_expr(text: str) -> str:
    if text is None:
        return ""
    e = str(text)

    if "?" in e and ":" in e:
        raise ValueError("Ternary operator ('?:') not allowed in expressions/conditions")

    e = e.replace("==", "=")

    e = e.replace("!=", "<>")

    e = e.replace("&&", " AND ").replace("||", " OR ")
    
    e = e.replace("&", " AND ").replace("|", " OR ")

    e = re.sub(r'(?<![<>=:])!(?![=])', ' NOT ', e)

    
    e = re.sub(r"\s+", " ", e).strip()
    return e

def strip_parens(expr: str) -> str:
    e = expr.strip()
    while e.startswith("(") and e.endswith(")"):
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
    """Split expr at the rightmost top-level operator among ops (token-aware).
    Returns (left, op, right) or None.
    """
    e = expr
    depth_p = depth_b = 0
    i = len(e) - 1

    def is_boundary(idx: int, length: int) -> bool:
        start = idx - length + 1
        before = e[start-1] if start-1 >= 0 else ""
        after = e[idx+1] if idx+1 < len(e) else ""
        def is_id_char(ch: str) -> bool:
            return ch.isalnum() or ch == "_"
        
        if is_id_char(before):
            return False
        
        if is_id_char(after):
            return False
        
        if before == ':' or after == ':':
            return False
        return True

    while i >= 0:
        ch = e[i]
        if ch == ')': depth_p += 1; i -= 1; continue
        if ch == '(': depth_p -= 1; i -= 1; continue
        if ch == ']': depth_b += 1; i -= 1; continue
        if ch == '[': depth_b -= 1; i -= 1; continue
        if depth_p == 0 and depth_b == 0:
            for op in sorted(ops, key=len, reverse=True):
                L = len(op)
                start = i - L + 1
                if start >= 0 and e[start:i+1].upper() == op and is_boundary(i, L):
                    left = e[:start].strip()
                    right = e[i+1:].strip()
                    return left, op.strip(), right
        i -= 1
    return None


def peel_array_once(dt: str) -> Optional[str]:
    """Given ARRAY[...] OF T -> T; else None."""
    ok, msg, base = parse_array(dt) if is_array(dt) else (False, "", "")
    return base if ok else None


def get_struct_field_type(dt: str, field: str, fb_defs: Dict[str, Dict[str, Any]]) -> Optional[str]:
    
    if is_struct(dt):
        ok, msg, fields = parse_struct_fields(dt)
        if not ok:
            return None
        return fields.get(field)
    
    if dt in fb_defs:
        
        if field in fb_defs[dt]["outputs"]:
            return fb_defs[dt]["outputTypes"].get(field)
        if field in fb_defs[dt]["inputs"]:
            return fb_defs[dt]["inputTypes"].get(field)
    return None


def normalize_string_family(dt: str) -> str:
    m = RE_STRING_T.fullmatch(dt.strip())
    if m:
        return m.group(1).upper() 
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

    
    if E in {"ANY","ANY_DERIVED","ANY_ELEMENTARY","ANY_MAGNITUDE",
             "ANY_NUM","ANY_REAL","ANY_INT","ANY_BIT","ANY_STRING","ANY_DATE"}:
        return True

    
    if E == A:
        return True

    
    if E in INT_FAMILY and A in INT_FAMILY:
        return True

    
    if E in REAL_FAMILY and (A in REAL_FAMILY or A in INT_FAMILY):
        return True

    if is_string_type(expected) and family_of(actual) == "STRING":
        return True

    if E in CHAR_FAMILY and A in CHAR_FAMILY and E == A:
        return True

    
    if E in {"TIME","DATE","TIME_OF_DAY","DATE_AND_TIME"}:
        return E == A

    return False

# ---------------- Variable / Member Type Resolution ----------------

MEMBER_TOKEN = re.compile(r"(\.[A-Za-z_][A-Za-z0-9_]*)|(\[[^\]]*\])")


def resolve_member_type(var_name: str, var_types: Dict[str, str], fb_defs: Dict[str, Dict[str, Any]]) -> Optional[str]:
   
    s = var_name.strip()
    m0 = re.match(rf"^({IDENT})", s)
    if not m0:
        return None
    base = m0.group(1)
    if base not in var_types:
        return None
    t = var_types[base]
    rest = s[len(base):]
    for m in MEMBER_TOKEN.finditer(rest):
        token = m.group(0)
        if token.startswith("["):
            
            elem = peel_array_once(t)
            if not elem:
                return None
            t = elem
        elif token.startswith("."):
            field = token[1:]
            
            ftype = get_struct_field_type(t, field, fb_defs)
            if not ftype:
                return None
            t = ftype
    return t

# ---------------- Expression Type Inference ----------------

def infer_expr_type(expr: str, var_types: Dict[str, str], functions: Dict[str, Dict[str, Any]], fb_defs: Dict[str, Dict[str, Any]]) -> Optional[str]:
    try:
        e_norm = normalize_expr(expr)
    except ValueError:
        return None
    e = strip_parens(e_norm)
    if not e:
        return None

    
    lit = literal_type(e)
    if lit:
        return lit

    for ops in (LOGICAL_OR, LOGICAL_AND, COMPARE_OPS, ADD_OPS, MUL_OPS):
        sp = split_top(e, ops)
        if sp:
            L, op, R = sp
            lt = infer_expr_type(L, var_types, functions, fb_defs)
            rt = infer_expr_type(R, var_types, functions, fb_defs)
            if lt is None or rt is None:
                return None
            uop = op.upper()
            if uop in ("OR", "AND"):
                return "BOOL" if (lt == "BOOL" and rt == "BOOL") else None
            if uop in ("<=", ">=", "<>", "!", "!=", "=", "<", ">"):
                if (is_numeric(lt) and is_numeric(rt)):
                    return "BOOL"
                fam_l = family_of(lt)
                fam_r = family_of(rt)
                
                if fam_l == fam_r and fam_l in {"STRING","BOOL","TIME","DATE","TIME_OF_DAY","DATE_AND_TIME","CHAR"}:
                    return "BOOL"
                return None
            if uop in ("+", "-", "*", "/"):
                if is_numeric(lt) and is_numeric(rt):
                    if lt in REAL_FAMILY or rt in REAL_FAMILY or lt == "REAL" or rt == "REAL":
                        return "REAL"
                    
                    return "INT"
                if uop == "+" and family_of(lt) == family_of(rt) == "STRING":
                    return "STRING"
                return None

    m_not = re.match(r"^(?i:NOT)\b(.*)$", e)
    if m_not:
        rest = m_not.group(1).strip()
        t = infer_expr_type(rest, var_types, functions, fb_defs)
        return "BOOL" if t == "BOOL" else None
    
    if e.startswith("+") or e.startswith("-"):
        rest = e[1:].strip()
        t = infer_expr_type(rest, var_types, functions, fb_defs)
        return t if (t is not None and is_numeric(t)) else None

    
    mfunc = re.match(rf"^({IDENT})\((.*)\)$", e)
    if mfunc:
        fname = mfunc.group(1)
        if fname in functions:
            return functions[fname].get("returnType")
        
        return None

    
    mvar = re.match(rf"^{IDENT}(?:\[[^\]]*\]|\.[A-Za-z_][A-Za-z0-9_]*)*\s*$", e)
    if mvar:
        t = resolve_member_type(e, var_types, fb_defs)
        
        if t: return t
        base = base_var_name(e)
        if base in var_types:
            return var_types[base]
        
        if BARE_WORD_AS_STRING:
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", e) and base not in var_types:
                return "STRING"
        return None

    if BARE_WORD_AS_STRING:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", e):
            return "STRING"

    return None

# ---------------- Condition Validator (comparisons and BOOL rules) ----------------

def _is_time_family(f: str) -> bool:
    return f in {"TIME","DATE","TIME_OF_DAY","DATE_AND_TIME"}


def validate_condition_expr(expr: str, var_types: Dict[str, str], functions: Dict[str, Dict[str, Any]], fb_defs: Dict[str, Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Validate that expr is a BOOL, with strict comparison rules:
     - Comparisons (=, <>, <, >, <=, >=) must yield BOOL.
     - TIME/DATE/TOD/DT comparisons require both sides to be the same family; if a literal is used, it must be the matching typed literal (e.g., T#... for TIME).
     - INT comparisons may use integer or real literals (e.g., 10, 18, 18.00).
     - REAL comparisons allow decimals (e.g., 18.0, 0.5).
     - STRING comparisons require quoted strings.
     - Reject invalid mixed-type comparisons (e.g., TIME = 18.00).
    """
    try:
        e_norm = normalize_expr(expr)
    except ValueError as exc:
        return False, str(exc)

    e = strip_parens(e_norm)

    sp = split_top(e, LOGICAL_OR)
    if sp:
        l, _, r = sp
        ok, msg = validate_condition_expr(l, var_types, functions, fb_defs)
        if not ok: return False, msg
        ok, msg = validate_condition_expr(r, var_types, functions, fb_defs)
        if not ok: return False, msg
        return True, ""
    sp = split_top(e, LOGICAL_AND)
    if sp:
        l, _, r = sp
        ok, msg = validate_condition_expr(l, var_types, functions, fb_defs)
        if not ok: return False, msg
        ok, msg = validate_condition_expr(r, var_types, functions, fb_defs)
        if not ok: return False, msg
        return True, ""

    sp = split_top(e, COMPARE_OPS)
    if sp:
        L, op, R = sp
        lt = infer_expr_type(L, var_types, functions, fb_defs)
        rt = infer_expr_type(R, var_types, functions, fb_defs)
        if lt is None or rt is None:
            return False, f"Cannot resolve types in comparison '{L} {op} {R}'"

        fam_l = family_of(lt)
        fam_r = family_of(rt)

        if _is_time_family(fam_l) or _is_time_family(fam_r):
            if fam_l != fam_r:
                l_lit = literal_type(strip_parens(L))
                r_lit = literal_type(strip_parens(R))
                
                if _is_time_family(fam_l) and (r_lit is None or family_of(r_lit) != fam_l):
                    return False, f"{fam_l} comparison requires a {fam_l} literal (e.g., T#1S) or {fam_l}-typed expression"
                if _is_time_family(fam_r) and (l_lit is None or family_of(l_lit) != fam_r):
                    return False, f"{fam_r} comparison requires a {fam_r} literal (e.g., T#1S) or {fam_r}-typed expression"
                return False, f"Incompatible types for comparison: {lt} {op} {rt}"
            return True, ""

        if fam_l == "STRING" or fam_r == "STRING":
            l_lit = literal_type(strip_parens(L))
            r_lit = literal_type(strip_parens(R))
            if (l_lit and family_of(l_lit) != "STRING") or (r_lit and family_of(r_lit) != "STRING"):
                return False, "STRING comparison requires a quoted string literal"
            if fam_l == fam_r == "STRING":
                return True, ""
            return False, f"Incompatible types for comparison: {lt} {op} {rt}"


        if is_numeric(lt) and is_numeric(rt):
            return True, ""

        
        if fam_l == fam_r and fam_l in {"BOOL","CHAR"}:
            return True, ""

        return False, f"Incompatible types for comparison: {lt} {op} {rt}"

    
    t = infer_expr_type(e, var_types, functions, fb_defs)
    if t == "BOOL":
        return True, ""
    return False, "Condition must be BOOL"

# ---------------- Statement Checker ----------------

def expected_type_from_target(target: str, var_types: Dict[str, str], fb_defs: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """Compute the expected type for an assignment target (handles array index and struct fields)."""
    return resolve_member_type(target, var_types, fb_defs)


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
        expected = expected_type_from_target(target, var_types, fb_defs)
        if expected is None:
            return False, f"Cannot resolve target type for '{target}'"
        expr = stmt.get("expression")
        if expr is None:
            return False, "Assignment missing expression"
        et = infer_expr_type(expr, var_types, functions, fb_defs)
        if et is None:
            return False, f"Unresolvable expression type for '{expr}'"
        if not type_assignable(expected, et):
            return False, f"Type mismatch: expected {expected}, got {et} in expression '{expr}'"
        return True, ""

    if typ == "if":
        ok, msg = validate_condition_expr(stmt.get("condition", ""), var_types, functions, fb_defs)
        if not ok:
            return False, msg
        for s in stmt.get("then", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        for s in stmt.get("else", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        return True, ""

    if typ == "case":
        sel_t = infer_expr_type(stmt.get("selector", ""), var_types, functions, fb_defs)
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
            if it not in var_types:
                var_types[it] = "INT"
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, loop_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        return True, ""

    if typ == "while":
        ok, msg = validate_condition_expr(stmt.get("condition", ""), var_types, functions, fb_defs)
        if not ok:
            return False, msg
        for s in stmt.get("body", []):
            ok, msg = stmtChecker(s, vars_in_scope, functions, fb_defs, var_types)
            if not ok: return ok, msg
        return True, ""

    if typ == "repeat":
        ok, msg = validate_condition_expr(stmt.get("until", ""), var_types, functions, fb_defs)
        if not ok:
            return False, msg
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
        
        in_types = functions[fname].get("inputTypes", [])
        for a, et in zip(args, in_types):
            at = infer_expr_type(a, var_types, functions, fb_defs)
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
        inst_is_var = inst in vars_in_scope
        if inst_is_var:
            inst_type = var_types.get(inst)
            fb_name = inst_type
        elif inst in fb_defs:
            fb_name = inst 
            inst_type = None
        else:
            return False, f"fbCall instance '{inst}' is not declared and no FB type named '{inst}' found"

        U = uc(fb_name) if fb_name else uc(inst_type or "")


        if fb_name in fb_defs:
            sig = fb_defs[fb_name]
            
            for k, v in stmt.get("inputs", {}).items():
                if k not in sig["inputs"]:
                    return False, f"fbCall '{inst}': unknown input '{k}' for FB '{fb_name}'"
                
                etype = sig["inputTypes"].get(k)
                if etype:
                    at = infer_expr_type(v, var_types, functions, fb_defs)
                    if at is None:
                        base = base_var_name(v)
                        if base not in vars_in_scope and not literal_type(v):
                            return False, f"fbCall '{inst}': input '{k}' maps to undeclared '{v}'"
                    else:
                        if not type_assignable(etype, at):
                            return False, f"fbCall '{inst}': input '{k}' expects {etype}, got {at}"
            
            for k, v in stmt.get("outputs", {}).items():
                if k not in sig["outputs"]:
                    return False, f"fbCall '{inst}': unknown output '{k}' for FB '{fb_name}'"
                base = base_var_name(v)
                
                if base not in vars_in_scope:
                    
                    if not (inst_is_var and base == inst):
                        return False, f"fbCall '{inst}': output '{k}' maps to undeclared '{v}'"
                
                otype = sig["outputTypes"].get(k)
                if otype:
                    t_target = resolve_member_type(v, var_types, fb_defs)
                    if t_target is None:
                        return False, f"fbCall '{inst}': cannot resolve output target '{v}'"
                    if not type_assignable(t_target, otype):
                        return False, f"fbCall '{inst}': output '{k}' of type {otype} not assignable to {t_target}"
            return True, ""

        if U in FB_PIN_TYPES:
            pins = FB_PIN_TYPES[U]
            for k, v in stmt.get("inputs", {}).items():
                if k not in pins["inputs"]:
                    return False, f"fbCall '{inst}': unknown input '{k}' for FB '{inst_type or fb_name}'"
                etype = pins["inputs"][k]
                at = infer_expr_type(v, var_types, functions, fb_defs)
                if at is None:
                    base = base_var_name(v)
                    if base not in vars_in_scope and not literal_type(v):
                        return False, f"fbCall '{inst}': input '{k}' maps to undeclared '{v}'"
                else:
                    if not type_assignable(etype, at):
                        return False, f"fbCall '{inst}': input '{k}' expects {etype}, got {at}"
            for k, v in stmt.get("outputs", {}).items():
                if k not in pins["outputs"]:
                    return False, f"fbCall '{inst}': unknown output '{k}' for FB '{inst_type or fb_name}'"
                otype = pins["outputs"][k]
                base = base_var_name(v)
                if base not in vars_in_scope:
                    return False, f"fbCall '{inst}': output '{k}' maps to undeclared '{v}'"
                t_target = resolve_member_type(v, var_types, fb_defs)
                if t_target is None:
                    return False, f"fbCall '{inst}': cannot resolve output target '{v}'"
                if not type_assignable(t_target, otype):
                    return False, f"fbCall '{inst}': output '{k}' of type {otype} not assignable to {t_target}"
            return True, ""

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
        return True, ""
    return True, ""


def load_device_variables() -> Dict[str, str]:
    """Load device variables from a local JSON file using the absolute path."""
    
    file_path = r"./AI_Integration/kb/templates/variables.json"
    vars_from_file = {}

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: The file '{file_path}' does not exist.")
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            for item in data:
                name = item.get("deviceName")
                datatype = item.get("dataType")
                if name and datatype:
                    vars_from_file[name.strip()] = datatype.upper()

    except FileNotFoundError as e:
        print(e)
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON file.")
        return {}
    return vars_from_file


def validator(intermediate: List[Dict[str, Any]]) -> Tuple[bool, str]:

    device_vars = load_device_variables()
    if not device_vars:
        return False, "No device variables found in DB. Cannot validate."

    functions: Dict[str, Dict[str, Any]] = {}
    fb_defs: Dict[str, Dict[str, Any]] = {}
    known_types = set(BASE_SCALAR_TYPES) | set(BUILTIN_FB_TYPES)

    # ---------------- Pass 1: Collects signatures (functions + FBs + add FB names to known_types) ----------------
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
            fb_defs[fbname] = {
                "inputs": [i["name"] for i in fb.get("inputs", [])],
                "outputs": [o["name"] for o in fb.get("outputs", [])],
                "locals": [l["name"] for l in fb.get("locals", [])],
                "inputTypes": {i["name"]: i["datatype"] for i in fb.get("inputs", [])},
                "outputTypes": {o["name"]: o["datatype"] for o in fb.get("outputs", [])},
            }
            known_types.add(fbname)

    # ---------------- Pass 2: Validates blocks ----------------
    for block in intermediate:
        blockType = list(block.keys())[0]
        if blockType not in ("function", "functionBlock", "program"):
            return False, f"Invalid block type: {blockType}"

        if blockType == "function":
            f = block["function"]
            for dt in [*f.get("inputs", []), {"datatype": f.get("returnType")}]:
                ok, msg = validate_datatype(dt["datatype"], known_types)
                if not ok:
                    return False, f"Function '{f['name']}' type error: {msg}"

            scope = {i["name"] for i in f.get("inputs", [])}
            var_types = {i["name"]: i["datatype"] for i in f.get("inputs", [])}

            for s in f.get("body", []):
                if s.get("type") == "return":
                    t = infer_expr_type(s.get("expression", ""), var_types, functions, fb_defs)
                    if t is None or not type_assignable(f.get("returnType"), t):
                        return False, f"Return type mismatch: expected {f.get('returnType')}, got {t}"
                else:
                    ok, msg = stmtChecker(s, scope, functions, fb_defs, var_types)
                    if not ok:
                        return False, msg

        elif blockType == "functionBlock":
            fb = block["functionBlock"]
            for arr, label in (("inputs", "input"), ("outputs", "output"), ("locals", "local")):
                for item in fb.get(arr, []):
                    ok, msg = validate_datatype(item["datatype"], known_types)
                    if not ok:
                        return False, f"FunctionBlock '{fb['name']}' {label} '{item['name']}': {msg}"

            scope = set([*(n for n in fb_defs[fb["name"]]["inputs"]),
                         *(n for n in fb_defs[fb["name"]]["outputs"]),
                         *(n for n in fb_defs[fb["name"]]["locals"])])

            var_types = {}
            for arr in ("inputs", "outputs", "locals"):
                for item in fb.get(arr, []):
                    var_types[item["name"]] = item["datatype"]

            for s in fb.get("body", []):
                ok, msg = stmtChecker(s, scope, functions, fb_defs, var_types)
                if not ok:
                    return False, msg

        elif blockType == "program":
            prog = block["program"]
            if "declarations" not in prog:
                return False, f"Program '{prog.get('name','<unnamed>')}' missing declarations"

            scope: set = set()
            var_types: Dict[str, str] = {}
            for d in prog.get("declarations", []):
                vname, vtype = d["name"], d["datatype"]

                ok, msg = validate_datatype(vtype, known_types)
                if not ok:
                    return False, f"Program '{prog['name']}' declaration '{vname}': {msg}"

                if vname not in device_vars:
                    return False, f"Variable '{vname}' not found in device specifications"

                if device_vars[vname] != vtype.upper():
                    return False, f"Type mismatch for '{vname}': DB has {device_vars[vname]}, JSON declares {vtype}"

                scope.add(vname)
                var_types[vname] = device_vars[vname]

            for s in prog.get("statements", []):
                ok, msg = stmtChecker(s, scope, functions, fb_defs, var_types)
                if not ok:
                    return False, msg

    return True, "Build Success✅"