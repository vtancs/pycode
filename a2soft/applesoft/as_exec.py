"""Expression evaluation and statement execution. Port of expr.c + exec.c
(as_internal.h's AsMachine is this module's AsMachine class).

Deviation from the C original: every error path (as_fail in C) raises
AsError(code) in Python instead of threading a return code through every
caller. as_fail's side effects (status text, ON ERR GOTO redirect) are
reproduced in AsMachine.fail() before it raises, and AsMachine.exec_one()
is the single place that turns a caught AsError back into the numeric
status code the rest of the machine (and the GUI) expects -- mirroring
finish_stmt()'s `m->redirect` check in the C source exactly.
"""

import math
import re
import time

from .as_common import (
    AsError, AsValue, AS_OK, AS_NUM, AS_STR, AS_T_FLOAT, AS_T_INT, AS_T_STR,
    AS_ERR_NEXT_WITHOUT_FOR, AS_ERR_SYNTAX, AS_ERR_RETURN_WITHOUT_GOSUB,
    AS_ERR_OUT_OF_DATA, AS_ERR_ILLEGAL_QUANTITY, AS_ERR_OVERFLOW, AS_ERR_OUT_OF_MEMORY,
    AS_ERR_UNDEF_STATEMENT, AS_ERR_BAD_SUBSCRIPT, AS_ERR_REDIMD_ARRAY, AS_ERR_DIVISION_BY_ZERO,
    AS_ERR_ILLEGAL_DIRECT, AS_ERR_TYPE_MISMATCH, AS_ERR_STRING_TOO_LONG, AS_ERR_FORMULA_TOO_COMPLEX,
    AS_ERR_CANT_CONTINUE, AS_ERR_UNDEF_FUNCTION, AS_ERR_CALL, AS_ERR_NOT_SUPPORTED,
    AS_STOPPED, AS_PAUSED, AS_END, AS_INPUT, AS_GET, AS_DELAY, as_error_text,
)
from .as_token import (
    TK_END, TK_FOR, TK_NEXT, TK_DATA, TK_INPUT, TK_DEL, TK_DIM, TK_READ,
    TK_GR, TK_TEXT, TK_PR, TK_IN, TK_CALL, TK_PLOT, TK_HLIN, TK_VLIN,
    TK_HGR2, TK_HGR, TK_HCOLOR, TK_HPLOT, TK_DRAW, TK_XDRAW, TK_HTAB, TK_HOME,
    TK_ROT, TK_SCALE, TK_SHLOAD, TK_TRACE, TK_NOTRACE, TK_NORMAL, TK_INVERSE, TK_FLASH,
    TK_COLOR, TK_POP, TK_VTAB, TK_HIMEM, TK_LOMEM, TK_ONERR, TK_RESUME, TK_RECALL,
    TK_STORE, TK_SPEED, TK_LET, TK_GOTO, TK_RUN, TK_IF, TK_RESTORE, TK_AMP,
    TK_GOSUB, TK_RETURN, TK_REM, TK_STOP, TK_ON, TK_WAIT, TK_LOAD, TK_SAVE,
    TK_DEF, TK_POKE, TK_PRINT, TK_CONT, TK_LIST, TK_CLEAR, TK_GET, TK_NEW,
    TK_TAB, TK_TO, TK_FN, TK_SPC, TK_THEN, TK_AT, TK_NOT, TK_STEP,
    TK_PLUS, TK_MINUS, TK_STAR, TK_SLASH, TK_CARET, TK_AND, TK_OR, TK_GT,
    TK_EQ, TK_LT, TK_SGN, TK_INT, TK_ABS, TK_USR, TK_FRE, TK_SCRN,
    TK_PDL, TK_POS, TK_SQR, TK_RND, TK_LOG, TK_EXP, TK_COS, TK_SIN,
    TK_TAN, TK_ATN, TK_PEEK, TK_LEN, TK_STR, TK_VAL, TK_ASC, TK_CHR,
    TK_LEFT, TK_RIGHT, TK_MID,
)
from .as_vars import AsVars, AsRef, as_name_index
from .as_program import AsLine
from .as_tokenize import as_tokenize, as_detokenize, AsTokenized

AS_STACK = 128


def _format_num(v):
    if v == 0:
        body = "0"
    else:
        body = "%.9g" % abs(v)
        if 'e' in body:
            body = body.replace('e', 'E')
    return ("-" + body) if v < 0 else (" " + body)


def _cmp_mem(a, b):
    n = min(len(a), len(b))
    c = 0
    if n:
        if a[:n] < b[:n]:
            c = -1
        elif a[:n] > b[:n]:
            c = 1
    if c < 0:
        return -1
    if c > 0:
        return 1
    if len(a) < len(b):
        return -1
    if len(a) > len(b):
        return 1
    return 0


def _bin_prec(c):
    if c == TK_OR:
        return 0x46
    if c == TK_AND:
        return 0x50
    if c in (TK_PLUS, TK_MINUS):
        return 0x79
    if c in (TK_STAR, TK_SLASH):
        return 0x7B
    if c == TK_CARET:
        return 0x7D
    return -1


_VAL_RE = re.compile(r'\s*[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?')


class AsFrame:
    __slots__ = ("kind", "name", "vtype", "limit", "step", "line", "pc")

    def __init__(self, kind, name=-1, vtype=AS_T_FLOAT, limit=0.0, step=1.0, line=None, pc=0):
        self.kind = kind  # 0 = FOR, 1 = GOSUB
        self.name = name
        self.vtype = vtype
        self.limit = limit
        self.step = step
        self.line = line
        self.pc = pc


class AsMachine:
    def __init__(self, program, screen):
        self.prog = program
        self.screen = screen
        self.vars = AsVars()
        self.line = None
        self.pc = 0
        self.at_line_start = 0
        self.break_skip = 0
        self.running = 0
        self.paused = 0
        self.step = 0
        self.check = 0
        self.redirect = 0
        self.trace = 0
        self.error = 0
        self.err_pc = 0
        self.status = ""
        self.stack = []
        self.data_line = None
        self.data_pc = 0
        self.data_ready = 0
        self.fn = [None] * 26
        self.onerr = 0
        self.onerr_line = 0
        self.in_onerr = 0
        self.resume_line = None
        self.resume_pc = 0
        self.can_cont = 0
        self.cont_line = None
        self.cont_pc = 0
        self.wait = 0
        self.wait_until = 0.0
        self.tone_hz = 0.0
        self.wait_frozen = 0
        self.input_shown = 0
        self.input_ready = 0
        self.input_line = ""
        self.key_ready = 0
        self.got_key = 0
        self.depth = 0
        self.rnd_state = 1
        self.rnd_last = 0.5
        self.rnd_have = 0
        self._jumps = {}
        self.stmt_line = None
        self.stmt_pc = 0
        self.direct_line = AsLine(0, b"")

    # -- token stream -------------------------------------------------
    def peekc(self):
        if not self.line or self.pc >= len(self.line.tokens):
            return 0
        return self.line.tokens[self.pc]

    def getc(self):
        c = self.peekc()
        if self.line and self.pc < len(self.line.tokens):
            self.pc += 1
        return c

    def at_end(self):
        c = self.peekc()
        return c == 0 or c == ord(':')

    def _in_direct(self):
        return self.line is self.direct_line

    def _expect(self, tok):
        if self.peekc() != tok:
            self.fail(AS_ERR_SYNTAX)
        self.getc()

    # -- error handling -------------------------------------------------
    def fail(self, err):
        self.err_pc = self.pc
        self._raise_err(err)

    def _raise_err(self, err):
        self.error = err
        if self.check:
            raise AsError(err)
        if self.onerr and not self.in_onerr and self._jumps:
            dest = self._jumps.get(self.onerr_line)
            if dest is not None:
                self.in_onerr = 1
                self.resume_line = self.stmt_line
                self.resume_pc = self.stmt_pc
                self.line = dest
                self.pc = 0
                self.at_line_start = 1
                self.redirect = 1
                raise AsError(err)
        self._show_error(err)
        self.running = 0
        self.paused = 0
        if self.screen:
            self.screen.cursor_on = 0
        raise AsError(err)

    def _show_error(self, err):
        ln = self.stmt_line if self.stmt_line else self.line
        if ln and ln is not self.direct_line:
            self.status = "?%s IN %d" % (as_error_text(err), ln.number)
        else:
            self.status = "?%s" % as_error_text(err)
        if self.screen and not self.check:
            self.screen.puts(self.status)
            self.screen.putc(ord('\r'))

    def _vcall(self, fn, *a):
        try:
            return fn(*a)
        except AsError as e:
            self.fail(e.code)

    # ================================================================
    # Expression evaluation (expr.c)
    # ================================================================
    def _fit_byte(self, v):
        if not math.isfinite(v) or v < 0 or v >= 256:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        return int(math.trunc(v))

    def parse_number(self):
        buf = []
        while len(buf) < 78:
            c = self.peekc()
            if (ord('0') <= c <= ord('9')) or c == ord('.'):
                buf.append(chr(self.getc()))
                continue
            break
        if buf and self.peekc() == ord('E'):
            buf.append('E')
            self.getc()
            if len(buf) < 78 and self.peekc() in (TK_PLUS, TK_MINUS):
                buf.append('-' if self.peekc() == TK_MINUS else '+')
                self.getc()
            while len(buf) < 78 and ord('0') <= self.peekc() <= ord('9'):
                buf.append(chr(self.getc()))
        text = ''.join(buf)
        try:
            if text in ('', '.', 'E', '-', '+') or not re.match(r'^[+-]?(\d+\.?\d*|\.\d+)([Ee][+-]?\d+)?$', text):
                raise ValueError
            v = float(text)
        except ValueError:
            self.fail(AS_ERR_SYNTAX)
        if not math.isfinite(v):
            self.fail(AS_ERR_OVERFLOW)
        return AsValue.of_num(v)

    def parse_string(self):
        self.getc()
        buf = bytearray()
        while self.peekc() and self.peekc() != ord('"'):
            if len(buf) >= 255:
                self.fail(AS_ERR_STRING_TOO_LONG)
            buf.append(self.getc())
        if self.peekc() == ord('"'):
            self.getc()
        return AsValue.of_str(bytes(buf))

    def parse_ref(self):
        c1 = self.peekc()
        if not (ord('A') <= c1 <= ord('Z')):
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        c2 = 0
        n = self.peekc()
        if (ord('A') <= n <= ord('Z')) or (ord('0') <= n <= ord('9')):
            c2 = n
            self.getc()
            while True:
                e = self.peekc()
                if (ord('A') <= e <= ord('Z')) or (ord('0') <= e <= ord('9')):
                    self.getc()
                else:
                    break
        ref_type = AS_T_FLOAT
        if self.peekc() == ord('$'):
            self.getc()
            ref_type = AS_T_STR
        elif self.peekc() == ord('%'):
            self.getc()
            ref_type = AS_T_INT
        name = as_name_index(c1, c2)
        if name < 0:
            self.fail(AS_ERR_SYNTAX)
        ref = AsRef(is_array=False, type=ref_type, name=name, ndims=0, subs=[])
        if self.peekc() == ord('('):
            self.getc()
            ref.is_array = True
            while True:
                s = self.eval_num()
                if ref.ndims >= 8:
                    self.fail(AS_ERR_BAD_SUBSCRIPT)
                if not math.isfinite(s) or s < 0 or s > 32767:
                    self.fail(AS_ERR_ILLEGAL_QUANTITY)
                ref.subs.append(int(math.trunc(s)))
                ref.ndims += 1
                if self.peekc() == ord(','):
                    self.getc()
                    continue
                break
            if self.getc() != ord(')'):
                self.fail(AS_ERR_SYNTAX)
        return ref

    def fn_call(self):
        letter = self.peekc()
        if not (ord('A') <= letter <= ord('Z')):
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        while (ord('A') <= self.peekc() <= ord('Z')) or (ord('0') <= self.peekc() <= ord('9')):
            self.getc()
        if self.getc() != ord('('):
            self.fail(AS_ERR_SYNTAX)
        arg = self.eval_num()
        if self.getc() != ord(')'):
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AsValue.of_num(0)
        fn = self.fn[letter - ord('A')]
        if fn is None:
            self.fail(AS_ERR_UNDEF_FUNCTION)
        saved = self._vcall(self.vars.get_scalar, fn['ptype'], fn['pname'])
        self._vcall(self.vars.set_scalar, fn['ptype'], fn['pname'], arg)
        tmp = AsLine(self.line.number if self.line else 0, fn['body'])
        save_line, save_pc = self.line, self.pc
        self.line = tmp
        self.pc = 0
        try:
            out = self.eval()
        finally:
            self.line = save_line
            self.pc = save_pc
            self._vcall(self.vars.set_scalar, fn['ptype'], fn['pname'], saved)
        return out

    def string_fn(self, token):
        if self.getc() != ord('('):
            self.fail(AS_ERR_SYNTAX)
        src = self.eval()
        if src.type != AS_STR:
            self.fail(AS_ERR_TYPE_MISMATCH)
        if self.getc() != ord(','):
            self.fail(AS_ERR_SYNTAX)
        a = self.eval_num()
        has_len = False
        b = 0.0
        if token == TK_MID and self.peekc() == ord(','):
            self.getc()
            b = self.eval_num()
            has_len = True
        if self.getc() != ord(')'):
            self.fail(AS_ERR_SYNTAX)
        data = src.str
        if token == TK_MID:
            if not math.isfinite(a) or a < 1 or a >= 256:
                self.fail(AS_ERR_ILLEGAL_QUANTITY)
            start = int(math.trunc(a))
            if not has_len:
                count = 255
            else:
                if not math.isfinite(b) or b < 0 or b >= 256:
                    self.fail(AS_ERR_ILLEGAL_QUANTITY)
                count = int(math.trunc(b))
            if start > len(data):
                return AsValue.of_str(b"")
            frm = start - 1
            ncopy = len(data) - frm
            if ncopy > count:
                ncopy = count
        else:
            if not math.isfinite(a) or a < 0 or a >= 256:
                self.fail(AS_ERR_ILLEGAL_QUANTITY)
            count = int(math.trunc(a))
            if count > len(data):
                count = len(data)
            ncopy = count
            frm = len(data) - ncopy if token == TK_RIGHT else 0
        return AsValue.of_str(data[frm:frm + ncopy])

    def _rnd(self, v):
        if v < 0:
            a = abs(v)
            self.rnd_state = int(a) & 0xFFFFFFFF
            if self.rnd_state == 0:
                self.rnd_state = 1
        if v != 0 or not self.rnd_have:
            self.rnd_state = (self.rnd_state * 1664525 + 1013904223) & 0xFFFFFFFF
            self.rnd_last = ((self.rnd_state >> 8) & 0xFFFFFF) / 16777216.0
            if self.rnd_last <= 0:
                self.rnd_last = 1.0 / 16777216.0
            self.rnd_have = 1
        return self.rnd_last

    def one_fn(self, token):
        if token == TK_USR:
            if self.getc() != ord('('):
                self.fail(AS_ERR_SYNTAX)
            self.eval_num()
            if self.getc() != ord(')'):
                self.fail(AS_ERR_SYNTAX)
            if self.check:
                return AsValue.of_num(0)
            self.fail(AS_ERR_NOT_SUPPORTED)
        if token == TK_SCRN:
            # NOTE: SCRN( already absorbs its opening paren during tokenization
            # (same as TAB( / SPC(), so unlike the other TK_SGN..TK_MID
            # functions there is no separate '(' left to consume here.
            v = self.eval_num()
            if self.getc() != ord(','):
                self.fail(AS_ERR_SYNTAX)
            yv = self.eval_num()
            if self.getc() != ord(')'):
                self.fail(AS_ERR_SYNTAX)
            if not math.isfinite(v) or not math.isfinite(yv):
                self.fail(AS_ERR_OVERFLOW)
            x, y = int(math.trunc(v)), int(math.trunc(yv))
            color = 0
            if self.screen:
                rc, color = self.screen.scrn(x, y)
                if rc != AS_OK:
                    self.fail(rc)
            return AsValue.of_num(color)
        if self.getc() != ord('('):
            self.fail(AS_ERR_SYNTAX)
        if token in (TK_LEN, TK_VAL, TK_ASC):
            sv = self.eval()
            if self.getc() != ord(')'):
                self.fail(AS_ERR_SYNTAX)
            if sv.type != AS_STR:
                self.fail(AS_ERR_TYPE_MISMATCH)
            if token == TK_LEN:
                return AsValue.of_num(len(sv.str))
            if token == TK_ASC:
                if len(sv.str) < 1:
                    self.fail(AS_ERR_ILLEGAL_QUANTITY)
                return AsValue.of_num(sv.str[0])
            text = sv.str.decode('latin-1')
            m = _VAL_RE.match(text)
            if not m or not m.group(0).strip():
                return AsValue.of_num(0)
            try:
                return AsValue.of_num(float(m.group(0)))
            except ValueError:
                return AsValue.of_num(0)
        v = self.eval_num()
        if self.getc() != ord(')'):
            self.fail(AS_ERR_SYNTAX)
        if not math.isfinite(v) and token not in (TK_FRE, TK_POS):
            self.fail(AS_ERR_OVERFLOW)
        if token == TK_SGN:
            return AsValue.of_num(-1 if v < 0 else (1 if v > 0 else 0))
        if token == TK_INT:
            return AsValue.of_num(math.floor(v))
        if token == TK_ABS:
            return AsValue.of_num(abs(v))
        if token == TK_FRE:
            return AsValue.of_num(32000)
        if token == TK_PDL:
            byte = self._fit_byte(v)
            if self.check:
                return AsValue.of_num(0)
            return AsValue.of_num(self.do_pdl(byte))
        if token == TK_POS:
            return AsValue.of_num(self.screen.cur_x if self.screen else 0)
        if token == TK_SQR:
            if v < 0:
                self.fail(AS_ERR_ILLEGAL_QUANTITY)
            return AsValue.of_num(math.sqrt(v))
        if token == TK_RND:
            return AsValue.of_num(self._rnd(v))
        if token == TK_LOG:
            if v <= 0:
                self.fail(AS_ERR_ILLEGAL_QUANTITY)
            return AsValue.of_num(math.log(v))
        if token == TK_EXP:
            try:
                r = math.exp(v)
            except OverflowError:
                r = math.inf
            if not math.isfinite(r):
                self.fail(AS_ERR_OVERFLOW)
            return AsValue.of_num(r)
        if token == TK_COS:
            return AsValue.of_num(math.cos(v))
        if token == TK_SIN:
            return AsValue.of_num(math.sin(v))
        if token == TK_TAN:
            r = math.tan(v)
            if not math.isfinite(r):
                self.fail(AS_ERR_OVERFLOW)
            return AsValue.of_num(r)
        if token == TK_ATN:
            return AsValue.of_num(math.atan(v))
        if token == TK_PEEK:
            if v < 0 or v > 65535:
                self.fail(AS_ERR_ILLEGAL_QUANTITY)
            return AsValue.of_num(self.do_peek(int(math.trunc(v))))
        if token == TK_STR:
            return AsValue.of_str(_format_num(v).encode('ascii'))
        if token == TK_CHR:
            byte = self._fit_byte(v)
            return AsValue.of_str(bytes([byte]))
        self.fail(AS_ERR_SYNTAX)

    def parse_primary(self):
        c = self.peekc()
        if c == TK_PLUS:
            self.getc()
            return self.parse_primary()
        if c == TK_MINUS or c == TK_NOT:
            neg = (c == TK_MINUS)
            self.getc()
            v = self.parse_expr(0x7F)
            if v.type != AS_NUM:
                self.fail(AS_ERR_TYPE_MISMATCH)
            if neg:
                r = -v.num
                if not math.isfinite(r):
                    self.fail(AS_ERR_OVERFLOW)
                return AsValue.of_num(r)
            return AsValue.of_num(1 if v.num == 0 else 0)
        if c == ord('"'):
            return self.parse_string()
        if c == ord('('):
            self.getc()
            v = self.parse_expr(0)
            if self.getc() != ord(')'):
                self.fail(AS_ERR_SYNTAX)
            return v
        if c == ord('.') or (ord('0') <= c <= ord('9')):
            return self.parse_number()
        if c == TK_FN:
            self.getc()
            return self.fn_call()
        if TK_SGN <= c <= TK_MID:
            token = self.getc()
            if TK_LEFT <= token <= TK_MID:
                return self.string_fn(token)
            return self.one_fn(token)
        if ord('A') <= c <= ord('Z'):
            ref = self.parse_ref()
            if self.check:
                if ref.type == AS_T_STR:
                    return AsValue.of_str(b"")
                return AsValue.of_num(0)
            return self._vcall(self.vars.load, ref)
        self.fail(AS_ERR_SYNTAX)

    def take_rel(self):
        bits = 0
        while True:
            c = self.peekc()
            bit = 0
            if c == TK_GT:
                bit = 1
            elif c == TK_EQ:
                bit = 2
            elif c == TK_LT:
                bit = 4
            else:
                break
            if bits & bit:
                self.fail(AS_ERR_SYNTAX)
            bits |= bit
            self.getc()
        if not bits:
            self.fail(AS_ERR_SYNTAX)
        return bits

    def apply_op(self, rel, op, lhs, rhs):
        if rel:
            if lhs.type != rhs.type:
                self.fail(AS_ERR_TYPE_MISMATCH)
            if lhs.type == AS_STR:
                cmp = _cmp_mem(lhs.str, rhs.str)
            else:
                cmp = -1 if lhs.num < rhs.num else (1 if lhs.num > rhs.num else 0)
            ok = 0
            if (op & 4) and cmp < 0:
                ok = 1
            if (op & 2) and cmp == 0:
                ok = 1
            if (op & 1) and cmp > 0:
                ok = 1
            return AsValue.of_num(ok)
        if op == TK_PLUS and (lhs.type == AS_STR or rhs.type == AS_STR):
            if lhs.type != AS_STR or rhs.type != AS_STR:
                self.fail(AS_ERR_TYPE_MISMATCH)
            if len(lhs.str) + len(rhs.str) > 255:
                self.fail(AS_ERR_STRING_TOO_LONG)
            return AsValue.of_str(lhs.str + rhs.str)
        if lhs.type != AS_NUM or rhs.type != AS_NUM:
            self.fail(AS_ERR_TYPE_MISMATCH)
        a, b = lhs.num, rhs.num
        if op == TK_PLUS:
            r = a + b
        elif op == TK_MINUS:
            r = a - b
        elif op == TK_STAR:
            r = a * b
        elif op == TK_SLASH:
            if b == 0:
                self.fail(AS_ERR_DIVISION_BY_ZERO)
            r = a / b
        elif op == TK_CARET:
            try:
                r = float(a) ** float(b)
            except (ValueError, OverflowError, ZeroDivisionError):
                r = math.inf
            if isinstance(r, complex):
                r = math.inf
        elif op == TK_AND:
            r = 1 if (a != 0.0 and b != 0.0) else 0
        elif op == TK_OR:
            r = 1 if (a != 0.0 or b != 0.0) else 0
        else:
            self.fail(AS_ERR_SYNTAX)
        if not math.isfinite(r):
            self.fail(AS_ERR_OVERFLOW)
        return AsValue.of_num(r)

    def parse_expr_body(self, min_prec):
        out = self.parse_primary()
        while True:
            c = self.peekc()
            rel = (c == TK_GT or c == TK_EQ or c == TK_LT)
            prec = 0x64 if rel else _bin_prec(c)
            op = c
            if prec < 0 or prec < min_prec:
                break
            if rel:
                mask = self.take_rel()
            else:
                self.getc()
                mask = 0
            rhs = self.parse_expr(prec + 1)
            out = self.apply_op(rel, mask if rel else op, out, rhs)
        return out

    def parse_expr(self, min_prec):
        self.depth += 1
        if self.depth > 64:
            self.depth -= 1
            self.fail(AS_ERR_FORMULA_TOO_COMPLEX)
        try:
            return self.parse_expr_body(min_prec)
        finally:
            self.depth -= 1

    def eval(self):
        return self.parse_expr(0)

    def eval_num(self):
        v = self.eval()
        if v.type != AS_NUM:
            self.fail(AS_ERR_TYPE_MISMATCH)
        return v.num

    # ================================================================
    # peek/poke/paddle (peekpoke.c)
    # ================================================================
    def do_peek(self, addr):
        if not self.screen:
            return 0
        return self.screen.peek(addr)

    def do_poke(self, addr, value):
        if not self.screen:
            return
        rc = self.screen.poke(addr, value)
        if rc != AS_OK:
            self.fail(rc)

    def do_pdl(self, n):
        if n < 0 or n > 255:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if self.screen and 0 <= n <= 1:
            return self.screen.pdl[n]
        return 0

    # ================================================================
    # Statement execution (exec.c)
    # ================================================================
    def _read_line_number(self):
        v = 0
        any_digit = False
        while ord('0') <= self.peekc() <= ord('9'):
            v = v * 10 + (self.getc() - ord('0'))
            if v > 63999:
                self.fail(AS_ERR_ILLEGAL_QUANTITY)
            any_digit = True
        if not any_digit:
            self.fail(AS_ERR_SYNTAX)
        return v

    def _eval_coord(self):
        v = self.eval_num()
        if not math.isfinite(v) or v < 0 or v > 32767:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        return int(math.trunc(v))

    def _store_ref(self, ref, val):
        if ref.type == AS_T_STR:
            if val.type != AS_STR:
                self.fail(AS_ERR_TYPE_MISMATCH)
        elif val.type != AS_NUM:
            self.fail(AS_ERR_TYPE_MISMATCH)
        if self.check:
            return
        self._vcall(self.vars.store, ref, val)

    def _print_value(self, v):
        if not self.screen or self.check:
            return
        if v.type == AS_STR:
            for b in v.str:
                self.screen.putc(b)
            return
        if not math.isfinite(v.num):
            self.fail(AS_ERR_OVERFLOW)
        self.screen.puts(_format_num(v.num))
        self.screen.putc(ord(' '))

    def _do_goto(self, n):
        if self.check:
            return AS_OK
        ln = self._jumps.get(n)
        if ln is None:
            self.fail(AS_ERR_UNDEF_STATEMENT)
        self.line = ln
        self.pc = 0
        self.at_line_start = 1
        return AS_OK

    def _do_gosub(self, n):
        if self.check:
            return AS_OK
        ln = self._jumps.get(n)
        if ln is None:
            self.fail(AS_ERR_UNDEF_STATEMENT)
        if len(self.stack) >= AS_STACK:
            self.fail(AS_ERR_OUT_OF_MEMORY)
        self.stack.append(AsFrame(kind=1, line=self.line, pc=self.pc))
        self.line = ln
        self.pc = 0
        self.at_line_start = 1
        return AS_OK

    # -- statements -------------------------------------------------
    def stmt_end(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        self.running = 0
        self.can_cont = 0
        return AS_END

    def stmt_stop(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        if self._in_direct():
            self.status = "BREAK"
            if self.screen:
                self.screen.puts(self.status)
                self.screen.putc(ord('\r'))
            self.running = 0
            return AS_END
        self.can_cont = 1
        self.cont_line = self.line
        self.cont_pc = self.pc
        self.status = ("BREAK IN %d" % self.line.number) if self.line else "BREAK"
        if self.screen:
            self.screen.puts(self.status)
            self.screen.putc(ord('\r'))
        self.running = 0
        self.paused = 1
        return AS_PAUSED

    def stmt_rem(self):
        if self.line:
            self.pc = len(self.line.tokens)
        return AS_OK

    def stmt_data(self):
        while self.peekc() and self.peekc() != ord(':'):
            self.getc()
        return AS_OK

    def stmt_let(self):
        ref = self.parse_ref()
        if self.peekc() != TK_EQ:
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        v = self.eval()
        self._store_ref(ref, v)
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        return AS_OK

    def stmt_for(self):
        ref = self.parse_ref()
        if ref.is_array or ref.type == AS_T_STR:
            self.fail(AS_ERR_TYPE_MISMATCH)
        if self.getc() != TK_EQ:
            self.fail(AS_ERR_SYNTAX)
        startv = self.eval_num()
        self._store_ref(ref, AsValue.of_num(startv))
        self._expect(TK_TO)
        limit = self.eval_num()
        step = 1.0
        if self.peekc() == TK_STEP:
            self.getc()
            step = self.eval_num()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        i = len(self.stack) - 1
        while i >= 0:
            if self.stack[i].kind != 0:
                break
            if self.stack[i].name == ref.name and self.stack[i].vtype == ref.type:
                del self.stack[i:]
                break
            i -= 1
        if len(self.stack) >= AS_STACK:
            self.fail(AS_ERR_OUT_OF_MEMORY)
        self.stack.append(AsFrame(kind=0, name=ref.name, vtype=ref.type,
                                   limit=limit, step=step, line=self.line, pc=self.pc))
        return AS_OK

    def stmt_next(self):
        while True:
            name = -1
            vtype = AS_T_FLOAT
            if ord('A') <= self.peekc() <= ord('Z'):
                ref = self.parse_ref()
                if ref.is_array or ref.type == AS_T_STR:
                    self.fail(AS_ERR_TYPE_MISMATCH)
                name = ref.name
                vtype = ref.type
            if name >= 0 and self.peekc() == ord(','):
                self.getc()
                if not (ord('A') <= self.peekc() <= ord('Z')):
                    self.fail(AS_ERR_SYNTAX)
            elif not self.at_end():
                self.fail(AS_ERR_SYNTAX)
            if self.check:
                if self.at_end():
                    return AS_OK
                continue
            while True:
                if not self.stack or self.stack[-1].kind != 0:
                    self.fail(AS_ERR_NEXT_WITHOUT_FOR)
                if name < 0 or (self.stack[-1].name == name and self.stack[-1].vtype == vtype):
                    break
                self.stack.pop()
            fr = self.stack[-1]
            cur = self._vcall(self.vars.get_scalar, fr.vtype, fr.name)
            cur += fr.step
            self._vcall(self.vars.set_scalar, fr.vtype, fr.name, cur)
            cur = self._vcall(self.vars.get_scalar, fr.vtype, fr.name)
            if (fr.step >= 0 and cur > fr.limit) or (fr.step < 0 and cur < fr.limit):
                self.stack.pop()
                if self.at_end():
                    return AS_OK
                continue
            self.line = fr.line
            self.pc = fr.pc
            self.at_line_start = 0
            return AS_OK

    def stmt_goto(self):
        n = self._read_line_number()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        return self._do_goto(n)

    def stmt_gosub(self):
        n = self._read_line_number()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        return self._do_gosub(n)

    def stmt_return(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        while self.stack and self.stack[-1].kind == 0:
            self.stack.pop()
        if not self.stack or self.stack[-1].kind != 1:
            self.fail(AS_ERR_RETURN_WITHOUT_GOSUB)
        fr = self.stack.pop()
        self.line = fr.line
        self.pc = fr.pc
        self.at_line_start = 0
        return AS_OK

    def stmt_pop(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        while self.stack and self.stack[-1].kind == 0:
            self.stack.pop()
        if not self.stack or self.stack[-1].kind != 1:
            self.fail(AS_ERR_RETURN_WITHOUT_GOSUB)
        self.stack.pop()
        return AS_OK

    def stmt_if(self):
        v = self.eval()
        if v.type != AS_NUM:
            self.fail(AS_ERR_TYPE_MISMATCH)
        cond = v.num != 0
        if self.peekc() == TK_GOTO:
            self.getc()
            n = self._read_line_number()
            if not self.at_end():
                self.fail(AS_ERR_SYNTAX)
            if self.check or not cond:
                return AS_OK
            return self._do_goto(n)
        if self.peekc() != TK_THEN:
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        if ord('0') <= self.peekc() <= ord('9'):
            n = self._read_line_number()
            if not self.at_end():
                self.fail(AS_ERR_SYNTAX)
            if self.check or not cond:
                return AS_OK
            return self._do_goto(n)
        if not cond and not self.check and self.line:
            self.pc = len(self.line.tokens)
        return AS_OK

    def stmt_on(self):
        v = self.eval_num()
        if not math.isfinite(v) or v < 0 or v > 255:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        n = int(math.trunc(v))
        if self.peekc() == TK_GOTO:
            gosub = False
        elif self.peekc() == TK_GOSUB:
            gosub = True
        else:
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        count = 0
        chosen = 0
        chosen_ok = False
        while True:
            ln = self._read_line_number()
            count += 1
            if count == n:
                chosen = ln
                chosen_ok = True
            if self.peekc() == ord(','):
                self.getc()
                continue
            break
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check or not chosen_ok:
            return AS_OK
        return self._do_gosub(chosen) if gosub else self._do_goto(chosen)

    def stmt_print(self):
        newline = True
        if self.at_end():
            if not self.check and self.screen:
                self.screen.putc(ord('\r'))
            return AS_OK
        while not self.at_end():
            c = self.peekc()
            if c == ord(';'):
                self.getc()
                newline = False
                continue
            if c == ord(','):
                self.getc()
                newline = False
                if not self.check and self.screen:
                    self.screen.comma_tab()
                continue
            if c == TK_TAB or c == TK_SPC:
                tab = (c == TK_TAB)
                self.getc()
                v = self.eval_num()
                if self.getc() != ord(')'):
                    self.fail(AS_ERR_SYNTAX)
                if not math.isfinite(v) or v < 0 or v >= 256:
                    self.fail(AS_ERR_ILLEGAL_QUANTITY)
                n = int(math.trunc(v))
                if not self.check and self.screen:
                    if tab:
                        dest = 0 if n == 0 else n - 1
                        guard = 0
                        while self.screen.cur_x != dest and guard < 255:
                            self.screen.putc(ord(' '))
                            guard += 1
                    else:
                        for _ in range(n):
                            self.screen.putc(ord(' '))
                newline = True
                continue
            v = self.eval()
            self._print_value(v)
            newline = True
        if newline and not self.check and self.screen:
            self.screen.putc(ord('\r'))
        return AS_OK

    def _parse_prompt(self):
        """Returns (question, prompt_str)."""
        question = True
        prompt = ""
        if self.peekc() == ord('"'):
            v = self.eval()
            if v.type != AS_STR:
                self.fail(AS_ERR_TYPE_MISMATCH)
            if self.peekc() == ord(';'):
                question = True
                self.getc()
            elif self.peekc() == ord(','):
                question = False
                self.getc()
            else:
                self.fail(AS_ERR_SYNTAX)
            prompt = v.str[:239].decode('latin-1')
        return question, prompt

    def stmt_input(self):
        if self.check:
            self._parse_prompt()
            while True:
                self.parse_ref()
                if self.peekc() == ord(','):
                    self.getc()
                    continue
                break
            if not self.at_end():
                self.fail(AS_ERR_SYNTAX)
            return AS_OK
        if self._in_direct():
            self.fail(AS_ERR_ILLEGAL_DIRECT)
        if not self.input_ready:
            if not self.input_shown:
                question, prompt = self._parse_prompt()
                if self.screen:
                    if prompt:
                        self.screen.puts(prompt)
                    if question:
                        self.screen.putc(ord('?'))
                    self.screen.cursor_on = 1
                self.input_line = ""
                self.input_shown = 1
            self.pc = self.stmt_pc
            self.wait = AS_INPUT
            return AS_INPUT
        self.input_ready = 0
        self.input_shown = 0
        self.wait = 0
        if self.screen:
            self.screen.cursor_on = 0
        self._parse_prompt()
        refs = []
        while True:
            if len(refs) >= 8:
                self.fail(AS_ERR_SYNTAX)
            refs.append(self.parse_ref())
            if self.peekc() == ord(','):
                self.getc()
                continue
            break
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        p = self.input_line
        pos = 0
        n = len(p)
        for i, ref in enumerate(refs):
            while pos < n and p[pos] == ' ':
                pos += 1
            if pos < n and p[pos] == '"':
                pos += 1
                start = pos
                while pos < n and p[pos] != '"':
                    pos += 1
                field = p[start:pos]
                if pos < n and p[pos] == '"':
                    pos += 1
            else:
                start = pos
                while pos < n and p[pos] != ',':
                    pos += 1
                field = p[start:pos].rstrip(' ')
            if ref.type == AS_T_STR:
                val = AsValue.of_str(field.encode('latin-1', 'replace')[:255])
            else:
                m = re.match(r'\s*[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?', field)
                text = m.group(0).strip() if m else ""
                if field and not text:
                    self.screen.puts("?REENTER")
                    self.screen.putc(ord('\r'))
                    self.input_line = ""
                    self.input_shown = 0
                    self.pc = self.stmt_pc
                    self.wait = AS_INPUT
                    return AS_INPUT
                try:
                    num = float(text) if text else 0.0
                except ValueError:
                    num = 0.0
                val = AsValue.of_num(num)
            self._store_ref(ref, val)
            while pos < n and p[pos] == ' ':
                pos += 1
            if i + 1 < len(refs):
                if pos >= n or p[pos] != ',':
                    if self.screen:
                        self.screen.puts("??")
                        self.screen.putc(ord('\r'))
                        self.screen.cursor_on = 1
                    self.input_line = ""
                    self.input_shown = 1
                    self.pc = self.stmt_pc
                    self.wait = AS_INPUT
                    return AS_INPUT
                pos += 1
        while pos < n and p[pos] == ' ':
            pos += 1
        if pos < n and self.screen:
            self.screen.puts("?EXTRA IGNORED")
            self.screen.putc(ord('\r'))
        return AS_OK

    def stmt_get(self):
        if self.check:
            self.parse_ref()
            if not self.at_end():
                self.fail(AS_ERR_SYNTAX)
            return AS_OK
        if self._in_direct():
            self.fail(AS_ERR_ILLEGAL_DIRECT)
        if not self.key_ready:
            self.pc = self.stmt_pc
            self.wait = AS_GET
            return AS_GET
        ch = self.got_key & 0xff
        self.key_ready = 0
        self.wait = 0
        ref = self.parse_ref()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if ref.type == AS_T_STR:
            val = AsValue.of_str(bytes([ch]))
        else:
            try:
                val = AsValue.of_num(float(chr(ch)))
            except ValueError:
                val = AsValue.of_num(0)
        self._store_ref(ref, val)
        return AS_OK

    def _pull_data(self):
        while True:
            if self.data_line is None:
                self.data_line = self.prog.head if self.prog else None
            if self.data_line is None:
                self.fail(AS_ERR_OUT_OF_DATA)
            t = self.data_line.tokens
            n = len(t)
            if not self.data_ready:
                if self.data_pc >= n:
                    self.data_line = self.data_line.next
                    self.data_pc = 0
                    continue
                if t[self.data_pc] == TK_DATA:
                    self.data_pc += 1
                    self.data_ready = 1
                elif t[self.data_pc] == TK_REM:
                    self.data_line = self.data_line.next
                    self.data_pc = 0
                    continue
                elif t[self.data_pc] == ord('"'):
                    self.data_pc += 1
                    while self.data_pc < n and t[self.data_pc] != ord('"'):
                        self.data_pc += 1
                    if self.data_pc < n:
                        self.data_pc += 1
                    continue
                else:
                    self.data_pc += 1
                    continue
            while self.data_pc < n and t[self.data_pc] == ord(' '):
                self.data_pc += 1
            if self.data_pc >= n or t[self.data_pc] == ord(':'):
                self.data_ready = 0
                if self.data_pc < n and t[self.data_pc] == ord(':'):
                    self.data_pc += 1
                continue
            if t[self.data_pc] == ord('"'):
                self.data_pc += 1
                s = self.data_pc
                while self.data_pc < n and t[self.data_pc] != ord('"'):
                    self.data_pc += 1
                field = bytes(t[s:self.data_pc])
                if self.data_pc < n and t[self.data_pc] == ord('"'):
                    self.data_pc += 1
            else:
                s = self.data_pc
                while self.data_pc < n and t[self.data_pc] not in (ord(','), ord(':')):
                    self.data_pc += 1
                e = self.data_pc
                while e > s and t[e - 1] == ord(' '):
                    e -= 1
                field = bytes(t[s:e])
            if self.data_pc < n and t[self.data_pc] == ord(','):
                self.data_pc += 1
            else:
                self.data_ready = 0
            return field

    def stmt_read(self):
        while True:
            ref = self.parse_ref()
            if self.check:
                if self.peekc() == ord(','):
                    self.getc()
                    continue
                break
            field = self._pull_data()
            if ref.type == AS_T_STR:
                val = AsValue.of_str(field[:255])
            else:
                try:
                    text = field.decode('latin-1')
                    m = _VAL_RE.match(text) or re.match(r'\s*[+-]?\d*\.?\d*([eE][+-]?\d+)?', text)
                    num = float(text.strip()) if text.strip() else 0.0
                except ValueError:
                    num = 0.0
                val = AsValue.of_num(num)
            self._store_ref(ref, val)
            if self.peekc() == ord(','):
                self.getc()
                continue
            break
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        return AS_OK

    def stmt_restore(self):
        if ord('0') <= self.peekc() <= ord('9'):
            n = self._read_line_number()
            if not self.at_end():
                self.fail(AS_ERR_SYNTAX)
            if self.check:
                return AS_OK
            ln = self._jumps.get(n)
            if ln is None:
                self.fail(AS_ERR_UNDEF_STATEMENT)
            self.data_line = ln
        else:
            if not self.at_end():
                self.fail(AS_ERR_SYNTAX)
            if self.check:
                return AS_OK
            self.data_line = self.prog.head if self.prog else None
        self.data_pc = 0
        self.data_ready = 0
        return AS_OK

    def stmt_dim(self):
        while True:
            ref = self.parse_ref()
            if not ref.is_array:
                self.fail(AS_ERR_SYNTAX)
            if not self.check:
                self._vcall(self.vars.dim, ref.name, ref.type, ref.subs)
            if self.peekc() == ord(','):
                self.getc()
                continue
            break
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        return AS_OK

    def stmt_def(self):
        self._expect(TK_FN)
        letter = self.peekc()
        if not (ord('A') <= letter <= ord('Z')):
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        if self.getc() != ord('('):
            self.fail(AS_ERR_SYNTAX)
        param = self.parse_ref()
        if param.is_array or param.type == AS_T_STR:
            self.fail(AS_ERR_TYPE_MISMATCH)
        if self.getc() != ord(')'):
            self.fail(AS_ERR_SYNTAX)
        if self.peekc() != TK_EQ:
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        start = self.pc
        while self.peekc() and self.peekc() != ord(':'):
            self.getc()
        n = self.pc - start
        if self.check:
            return AS_OK
        if self._in_direct():
            self.fail(AS_ERR_ILLEGAL_DIRECT)
        body = self.line.tokens[start:start + n] if self.line else b""
        self.fn[letter - ord('A')] = {
            'body': body, 'len': n, 'pname': param.name, 'ptype': param.type,
        }
        return AS_OK

    def stmt_run(self):
        has = False
        n = 0
        if ord('0') <= self.peekc() <= ord('9'):
            n = self._read_line_number()
            has = True
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        ln = self.prog.find(n) if has else (self.prog.head if self.prog else None)
        if has and ln is None:
            self.fail(AS_ERR_UNDEF_STATEMENT)
        self._reset_runtime()
        self.line = ln
        self.pc = 0
        self.at_line_start = 1
        self.running = 1 if ln else 0
        return AS_OK if ln else AS_END

    def stmt_del(self):
        a = self._read_line_number()
        self._expect(ord(','))
        b = self._read_line_number()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        lo, hi = (a, b) if a < b else (b, a)
        if self.line and lo <= self.line.number <= hi:
            nxt = self.line.next
            while nxt and nxt.number <= hi:
                nxt = nxt.next
            self.line = nxt
            self.pc = 0
            self.at_line_start = 1
        self.prog.delete_range(lo, hi)
        self._jumps = {ln.number: ln for ln in self.prog.lines} if self.prog else {}
        self.can_cont = 0
        return AS_OK

    def stmt_list(self):
        a, b = 0, 63999
        have = False
        if ord('0') <= self.peekc() <= ord('9'):
            a = self._read_line_number()
            have = True
            b = a
        if self.peekc() == ord(','):
            self.getc()
            b = 63999
            if ord('0') <= self.peekc() <= ord('9'):
                b = self._read_line_number()
            if not have:
                a = 0
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check or not self.screen or not self.prog:
            return AS_OK
        for ln in self.prog.lines:
            if ln.number < a or ln.number > b:
                continue
            self.screen.puts("%d " % ln.number)
            self.screen.puts(as_detokenize(ln.tokens))
            self.screen.putc(ord('\r'))
        return AS_OK

    def stmt_new(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        self.line = None
        if self.prog:
            self.prog.clear()
            self.prog.dirty = 1
        self._reset_runtime()
        self.running = 0
        return AS_END

    def stmt_clear(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        self.vars.clear()
        self.fn = [None] * 26
        self.stack = []
        self.data_line = None
        self.data_pc = 0
        self.data_ready = 0
        self.onerr = 0
        self.in_onerr = 0
        return AS_OK

    def stmt_cont(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        if not self.can_cont or not self.cont_line:
            self.fail(AS_ERR_CANT_CONTINUE)
        self.line = self.cont_line
        self.pc = self.cont_pc
        self.at_line_start = 0
        self.running = 1
        self.paused = 0
        self.can_cont = 0
        return AS_OK

    def stmt_poke(self):
        addr = self.eval_num()
        self._expect(ord(','))
        val = self.eval_num()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not math.isfinite(addr) or addr < 0 or addr > 65535:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if not math.isfinite(val) or val < 0 or val > 255:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if self.check:
            return AS_OK
        self.do_poke(int(math.trunc(addr)), int(math.trunc(val)))
        return AS_OK

    def stmt_home(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not self.check and self.screen:
            self.screen.home()
        return AS_OK

    def stmt_htab(self):
        n = self._eval_coord()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if n < 0 or n > 255:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if not self.check and self.screen:
            self.screen.cur_x = 0 if n == 0 else n - 1
        return AS_OK

    def stmt_vtab(self):
        n = self._eval_coord()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if n < 1 or n > 24:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if not self.check and self.screen:
            self.screen.cur_y = n - 1
        return AS_OK

    def stmt_text(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not self.check and self.screen:
            self.screen.text_mode()
        return AS_OK

    def stmt_gr(self):
        cols, rows, saw = 40, 40, False
        if self.peekc() == ord('('):
            self.getc()
            cols = self._eval_coord()
            self._expect(ord(','))
            rows = self._eval_coord()
            if self.getc() != ord(')'):
                self.fail(AS_ERR_SYNTAX)
            saw = True
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check or not self.screen:
            return AS_OK
        if not saw or (cols == 40 and rows == 40):
            self.screen.gr(40, 40)
        elif cols == 80 and rows == 50:
            self.screen.gr(80, 50)
        else:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        return AS_OK

    def stmt_hgr(self):
        w, h, saw = 0, 0, False
        if self.peekc() == ord('('):
            self.getc()
            w = self._eval_coord()
            self._expect(ord(','))
            h = self._eval_coord()
            if self.getc() != ord(')'):
                self.fail(AS_ERR_SYNTAX)
            saw = True
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check or not self.screen:
            return AS_OK
        if not saw:
            self.screen.hgr(0)
        elif w == 320 and h == 200:
            self.screen.hgr(3)
        elif w == 640 and h == 400:
            self.screen.hgr(2)
        else:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        return AS_OK

    def stmt_hgr2(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not self.check and self.screen:
            self.screen.hgr(1)
        return AS_OK

    def stmt_color(self):
        n = self._eval_coord()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if n < 0 or n > 15:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if not self.check and self.screen:
            self.screen.color = n
        return AS_OK

    def stmt_hcolor(self):
        n = self._eval_coord()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if n < 0 or n > 15:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if not self.check and self.screen:
            self.screen.hcolor = n
        return AS_OK

    def stmt_plot(self):
        x = self._eval_coord()
        self._expect(ord(','))
        y = self._eval_coord()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check or not self.screen:
            return AS_OK
        rc = self.screen.plot(x, y)
        if rc != AS_OK:
            self.fail(rc)
        return AS_OK

    def stmt_hlin(self):
        x1 = self._eval_coord()
        self._expect(ord(','))
        x2 = self._eval_coord()
        self._expect(TK_AT)
        y = self._eval_coord()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check or not self.screen:
            return AS_OK
        rc = self.screen.hlin(x1, x2, y)
        if rc != AS_OK:
            self.fail(rc)
        return AS_OK

    def stmt_vlin(self):
        y1 = self._eval_coord()
        self._expect(ord(','))
        y2 = self._eval_coord()
        self._expect(TK_AT)
        x = self._eval_coord()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check or not self.screen:
            return AS_OK
        rc = self.screen.vlin(y1, y2, x)
        if rc != AS_OK:
            self.fail(rc)
        return AS_OK

    def stmt_hplot(self):
        x = y = 0
        abs_first = False
        if self.peekc() != TK_TO:
            x = self._eval_coord()
            self._expect(ord(','))
            y = self._eval_coord()
            abs_first = True
        if abs_first and not self.check and self.screen:
            rc = self.screen.hplot(x, y)
            if rc != AS_OK:
                self.fail(rc)
        while self.peekc() == TK_TO:
            self.getc()
            x = self._eval_coord()
            self._expect(ord(','))
            y = self._eval_coord()
            if not self.check and self.screen:
                rc = self.screen.hplot_to(x, y)
                if rc != AS_OK:
                    self.fail(rc)
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        return AS_OK

    def stmt_style(self, style):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not self.check and self.screen:
            self.screen.style = style
        return AS_OK

    def stmt_onerr(self):
        self._expect(TK_GOTO)
        n = self._read_line_number()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        self.onerr = 1
        self.onerr_line = n
        return AS_OK

    def stmt_resume(self):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        if not self.in_onerr or not self.resume_line:
            self.fail(AS_ERR_CANT_CONTINUE)
        self.in_onerr = 0
        self.line = self.resume_line
        self.pc = self.resume_pc
        self.at_line_start = 0
        return AS_OK

    def stmt_trace(self, on):
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not self.check:
            self.trace = on
        return AS_OK

    def stmt_ignore_num(self):
        self.eval_num()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        return AS_OK

    def stmt_call(self):
        self.eval_num()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if self.check:
            return AS_OK
        self.fail(AS_ERR_CALL)

    def _begin_wait(self, seconds, hz):
        if not (seconds > 0):
            return AS_OK
        until = time.monotonic() + seconds
        if not math.isfinite(until):
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if self.check:
            return AS_OK
        self.tone_hz = hz
        self.wait_until = until
        self.wait_frozen = 0
        self.wait = AS_DELAY
        if self.screen:
            self.screen.tone_hz = hz
        return AS_DELAY

    def _skip_spaces(self):
        while self.peekc() == ord(' '):
            self.getc()

    def stmt_delay(self):
        self._skip_spaces()
        sec = self.eval_num()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not math.isfinite(sec) or sec < 0:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        return self._begin_wait(sec, 0)

    def stmt_tone(self):
        self._skip_spaces()
        hz = self.eval_num()
        if self.peekc() != ord(','):
            self.fail(AS_ERR_SYNTAX)
        self.getc()
        sec = self.eval_num()
        if not self.at_end():
            self.fail(AS_ERR_SYNTAX)
        if not math.isfinite(hz) or hz < 0 or hz > 8000:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        if not math.isfinite(sec) or sec < 0:
            self.fail(AS_ERR_ILLEGAL_QUANTITY)
        return self._begin_wait(sec, hz)

    _EXT_WORDS = ("DELAY", "TONE")

    def _take_ext(self):
        best = 0
        found = None
        for w in self._EXT_WORDS:
            k = 0
            while k < len(w):
                p = self.pc + k
                if not self.line or p >= len(self.line.tokens) or self.line.tokens[p] != ord(w[k]):
                    break
                k += 1
            if k == len(w) and k > best:
                best = k
                found = w
        if not found:
            return None
        self.pc += best
        return found

    def stmt_amp(self):
        start = self.pc
        name = self._take_ext()
        if name:
            return self.stmt_delay() if name == "DELAY" else self.stmt_tone()
        c = self.peekc()
        if not (ord('A') <= c <= ord('Z')):
            self.fail(AS_ERR_SYNTAX)
        while ord('A') <= c <= ord('Z'):
            self.getc()
            c = self.peekc()
        self.pc = start
        self.fail(AS_ERR_SYNTAX)

    def stmt_unsupported(self):
        while not self.at_end():
            if self.peekc() == ord('"'):
                self.getc()
                while self.peekc() and self.peekc() != ord('"'):
                    self.getc()
                if self.peekc() == ord('"'):
                    self.getc()
                continue
            self.getc()
        if self.check:
            return AS_OK
        self.fail(AS_ERR_NOT_SUPPORTED)

    def _dispatch(self, tok):
        if tok == TK_END:
            return self.stmt_end()
        if tok == TK_FOR:
            return self.stmt_for()
        if tok == TK_NEXT:
            return self.stmt_next()
        if tok == TK_DATA:
            return self.stmt_data()
        if tok == TK_INPUT:
            return self.stmt_input()
        if tok == TK_DEL:
            return self.stmt_del()
        if tok == TK_DIM:
            return self.stmt_dim()
        if tok == TK_READ:
            return self.stmt_read()
        if tok == TK_GR:
            return self.stmt_gr()
        if tok == TK_TEXT:
            return self.stmt_text()
        if tok in (TK_PR, TK_IN):
            return self.stmt_ignore_num()
        if tok == TK_CALL:
            return self.stmt_call()
        if tok == TK_PLOT:
            return self.stmt_plot()
        if tok == TK_HLIN:
            return self.stmt_hlin()
        if tok == TK_VLIN:
            return self.stmt_vlin()
        if tok == TK_HGR2:
            return self.stmt_hgr2()
        if tok == TK_HGR:
            return self.stmt_hgr()
        if tok == TK_HCOLOR:
            return self.stmt_hcolor()
        if tok == TK_HPLOT:
            return self.stmt_hplot()
        if tok in (TK_DRAW, TK_XDRAW, TK_ROT, TK_SCALE, TK_SHLOAD):
            return self.stmt_unsupported()
        if tok == TK_HTAB:
            return self.stmt_htab()
        if tok == TK_HOME:
            return self.stmt_home()
        if tok == TK_TRACE:
            return self.stmt_trace(1)
        if tok == TK_NOTRACE:
            return self.stmt_trace(0)
        if tok == TK_NORMAL:
            return self.stmt_style(0)
        if tok == TK_INVERSE:
            return self.stmt_style(1)
        if tok == TK_FLASH:
            return self.stmt_style(2)
        if tok == TK_COLOR:
            return self.stmt_color()
        if tok == TK_POP:
            return self.stmt_pop()
        if tok == TK_VTAB:
            return self.stmt_vtab()
        if tok in (TK_HIMEM, TK_LOMEM, TK_SPEED):
            return self.stmt_ignore_num()
        if tok == TK_ONERR:
            return self.stmt_onerr()
        if tok == TK_RESUME:
            return self.stmt_resume()
        if tok in (TK_RECALL, TK_STORE, TK_WAIT, TK_LOAD, TK_SAVE):
            return self.stmt_unsupported()
        if tok == TK_AMP:
            return self.stmt_amp()
        if tok == TK_LET:
            return self.stmt_let()
        if tok == TK_GOTO:
            return self.stmt_goto()
        if tok == TK_RUN:
            return self.stmt_run()
        if tok == TK_IF:
            return self.stmt_if()
        if tok == TK_RESTORE:
            return self.stmt_restore()
        if tok == TK_GOSUB:
            return self.stmt_gosub()
        if tok == TK_RETURN:
            return self.stmt_return()
        if tok == TK_REM:
            return self.stmt_rem()
        if tok == TK_STOP:
            return self.stmt_stop()
        if tok == TK_ON:
            return self.stmt_on()
        if tok == TK_DEF:
            return self.stmt_def()
        if tok == TK_POKE:
            return self.stmt_poke()
        if tok == TK_PRINT:
            return self.stmt_print()
        if tok == TK_CONT:
            return self.stmt_cont()
        if tok == TK_LIST:
            return self.stmt_list()
        if tok == TK_CLEAR:
            return self.stmt_clear()
        if tok == TK_GET:
            return self.stmt_get()
        if tok == TK_NEW:
            return self.stmt_new()
        self.fail(AS_ERR_SYNTAX)

    def _finish_stmt(self, rc):
        if self.redirect:
            self.redirect = 0
            return AS_OK
        return rc

    def exec_one(self):
        if not self.line:
            return AS_END
        if self.at_line_start:
            self.at_line_start = 0
            if not self.check and self.line.breakpoint and not self.break_skip:
                self.break_skip = 1
                self.at_line_start = 1
                self.running = 0
                self.paused = 1
                self.status = "BREAK IN %d" % self.line.number
                return AS_PAUSED
            self.break_skip = 0
            if not self.check and self.trace and self.screen and self.line:
                self.screen.puts("#%d " % self.line.number)
        self.stmt_line = self.line
        self.stmt_pc = self.pc
        c = self.peekc()
        if c == 0:
            self.line = self.line.next
            self.pc = 0
            self.at_line_start = 1
            if not self.line:
                self.running = 0
                return AS_END
            return AS_OK
        if c == ord(':'):
            self.getc()
            return AS_OK
        if TK_END <= c <= TK_NEW:
            self.getc()
            try:
                rc = self._dispatch(c)
            except AsError as e:
                rc = e.code
            return self._finish_stmt(rc)
        if ord('A') <= c <= ord('Z'):
            try:
                rc = self.stmt_let()
            except AsError as e:
                rc = e.code
            return self._finish_stmt(rc)
        try:
            self.fail(AS_ERR_SYNTAX)
        except AsError as e:
            rc = e.code
        return self._finish_stmt(rc)

    # ================================================================
    # Public API (as_machine_*)
    # ================================================================
    def _reset_runtime(self):
        self.vars.clear()
        self.fn = [None] * 26
        self.stack = []
        self.data_line = None
        self.data_pc = 0
        self.data_ready = 0
        self.onerr = 0
        self.in_onerr = 0
        self.can_cont = 0
        self.wait = 0
        self.input_ready = 0
        self.input_shown = 0
        self.key_ready = 0
        self._silence_tone()
        self._jumps = {ln.number: ln for ln in self.prog.lines} if self.prog else {}
        if self.screen:
            self.screen.cursor_on = 0

    def _silence_tone(self):
        self.tone_hz = 0.0
        self.wait_frozen = 0
        if self.screen:
            self.screen.tone_hz = 0.0

    def _thaw_wait(self):
        if self.wait != AS_DELAY or not self.wait_frozen:
            return
        self.wait_until = time.monotonic() + self.wait_until
        self.wait_frozen = 0
        if self.screen:
            self.screen.tone_hz = self.tone_hz

    def _start_immediate(self, tokens):
        self.direct_line = AsLine(0, tokens)
        self._jumps = {ln.number: ln for ln in self.prog.lines} if self.prog else {}
        self.line = self.direct_line
        self.pc = 0
        self.at_line_start = 1
        self.break_skip = 1
        self.running = 1
        self.paused = 0
        self.step = 0
        self.wait = 0
        self._silence_tone()
        self.error = 0
        self.redirect = 0
        self.input_shown = 0
        self.input_ready = 0
        self.status = ""

    def run(self):
        if self.paused and self.line:
            self.paused = 0
            self.running = 1
            self.break_skip = 1
            self._thaw_wait()
            return
        self._reset_runtime()
        self.line = self.prog.head if self.prog else None
        self.pc = 0
        self.at_line_start = 1
        self.running = 1 if self.line else 0
        self.paused = 0
        self.status = ""
        self.step = 0

    def stop(self):
        self.running = 0
        self.paused = 0
        self.step = 0
        self.wait = 0
        self.stack = []
        self.can_cont = 0
        self._silence_tone()
        if self.screen:
            self.screen.cursor_on = 0
        self.status = "STOPPED"

    def pause(self):
        if not self.running:
            return
        self.running = 0
        self.paused = 1
        if self.wait == AS_DELAY and not self.wait_frozen:
            left = self.wait_until - time.monotonic()
            self.wait_until = left if left > 0 else 0
            self.wait_frozen = 1
        if self.screen:
            self.screen.tone_hz = 0

    def cont(self):
        if not self.paused:
            return
        self.paused = 0
        self.running = 1
        self.break_skip = 1
        self._thaw_wait()

    def do_step(self):
        if not self.running and not self.paused:
            self.run()
        self.step = 1
        self.running = 1
        self.paused = 0
        self.break_skip = 1
        self._thaw_wait()

    def quantum(self, seconds):
        if self.wait == AS_DELAY:
            if not self.wait_frozen and time.monotonic() >= self.wait_until:
                self.wait = 0
                self._silence_tone()
            else:
                return AS_DELAY
        elif self.wait:
            return self.wait
        if not self.running:
            return AS_PAUSED if self.paused else (self.error if self.error else AS_OK)
        t0 = time.monotonic()
        steps = 0
        while True:
            rc = self.exec_one()
            if rc in (AS_INPUT, AS_GET, AS_DELAY):
                return rc
            if rc == AS_PAUSED:
                return AS_PAUSED
            if rc == AS_END:
                self.running = 0
                return AS_END
            if rc != AS_OK:
                self.running = 0
                return rc
            if self.step:
                self.step = 0
                self.running = 0
                self.paused = 1
                return AS_PAUSED
            if not self.running:
                return AS_END
            steps += 1
            if (steps & 31) == 0:
                if time.monotonic() - t0 >= seconds:
                    return AS_OK

    def is_running(self):
        return self.running

    def is_paused(self):
        return self.paused

    def is_waiting(self):
        return self.wait

    def current_line(self):
        if not self.line or self.line is self.direct_line:
            return 0
        return self.line.number

    def gosub_stack(self):
        out = []
        for fr in self.stack:
            if fr.kind != 1:
                continue
            ln = fr.line
            if not ln or ln is self.direct_line:
                continue
            out.append(ln.number)
        return out

    def on_line(self, number):
        return bool(self.line) and self.line is not self.direct_line and self.line.number == number

    def edited(self):
        drop = self.paused or self.can_cont
        self.can_cont = 0
        self.paused = 0
        self.running = 0
        self.wait = 0
        self.step = 0
        self.line = None
        self.stack = []
        self._silence_tone()
        if self.screen:
            self.screen.cursor_on = 0
        if drop:
            self.status = ""

    def keydown(self, ch):
        if self.wait == AS_INPUT:
            if ch in (ord('\r'), ord('\n')):
                if self.screen:
                    self.screen.putc(ord('\r'))
                self.input_ready = 1
                self.wait = 0
                if self.screen:
                    self.screen.cursor_on = 0
                return
            if ch in (8, 127):
                if self.input_line:
                    self.input_line = self.input_line[:-1]
                    if self.screen:
                        self.screen.backspace()
                        self.screen.putc(ord(' '))
                        self.screen.backspace()
                return
            if 32 <= ch < 127 and len(self.input_line) < 254:
                self.input_line += chr(ch)
                if self.screen:
                    self.screen.putc(ch)
            return
        if self.wait == AS_GET:
            self.got_key = 13 if ch == ord('\r') else (ch & 0x7f)
            self.key_ready = 1
            self.wait = 0
            return
        if self.screen:
            self.screen.key_strobe = (ch & 0x7f) | 0x80

    def prompt(self, text):
        """Apple II prompt. Returns (kind, err) -- kind: 0 empty, 1 stored, 2 executed.
        err is AS_ERR_SYNTAX or None."""
        if text is None:
            text = ""
        s = text.lstrip(' \t')
        has = False
        num = 0
        if s and ord('0') <= ord(s[0]) <= ord('9'):
            digits = 0
            i = 0
            while i < len(s) and ord('0') <= ord(s[i]) <= ord('9'):
                digits += 1
                if digits > 5:
                    return 0, AS_ERR_SYNTAX
                num = num * 10 + (ord(s[i]) - ord('0'))
                if num > 63999:
                    return 0, AS_ERR_SYNTAX
                i += 1
            s = s[i:].lstrip(' \t')
            has = True
        if has:
            if not self.prog:
                return 0, AS_ERR_SYNTAX
            t, length = as_tokenize(s)
            old = self.prog.find(num)
            br = old.breakpoint if old else 0
            self.edited()
            if length == 0:
                self.prog.upsert(num, b"", 0)
            else:
                self.prog.upsert(num, t.bytes[:length], br)
            return 1, None
        t, length = as_tokenize(s)
        if length == 0:
            return 0, None
        self._start_immediate(t.bytes[:length])
        return 2, None


def as_check_line(tokens):
    """Syntax-check one tokenized line (no line number). Returns (AS_OK, None)
    on success, or (err_code, err_pc) on failure."""
    from .as_program import AsProgram
    from .as_screen import AsScreen
    prog = AsProgram()
    screen = AsScreen()
    m = AsMachine(prog, screen)
    line = AsLine(0, tokens)
    m.check = 1
    m.line = line
    m.pc = 0
    m.at_line_start = 1
    m.break_skip = 1
    rc = AS_OK
    while m.line and m.pc <= len(m.line.tokens):
        if m.pc >= len(m.line.tokens):
            break
        before = m.pc
        try:
            rc = m.exec_one()
        except AsError as e:
            rc = e.code
            break
        if rc != AS_OK:
            break
        if m.pc == before:
            break
    if rc == AS_OK:
        return AS_OK, None
    return rc, m.err_pc
