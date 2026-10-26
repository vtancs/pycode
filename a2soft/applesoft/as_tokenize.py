"""Source <-> token-byte conversion. Direct port of as_tokenize.h / tokenize.c."""

from .as_common import AS_CLS_PLAIN, AS_CLS_KEYWORD, AS_CLS_VARIABLE, AS_CLS_REMARK
from .as_token import TK_FIRST, TK_COUNT, TK_AMP, TK_DATA, TK_REM, TK_PRINT, TK_GOTO, TK_GOSUB, TK_THEN, TK_ON, as_keyword

_EXT_WORDS = ["DELAY", "TONE"]


def _ext_command(s, n, i):
    best = 0
    for w in _EXT_WORDS:
        k = 0
        while k < len(w) and i + k < n:
            c = s[i + k].upper()
            if c != w[k]:
                break
            k += 1
        if k == len(w) and k > best:
            best = k
    return best


def _kw_match(s, n, i):
    """Returns (token, end) or (None, None)."""
    for t in range(TK_COUNT):
        tok = TK_FIRST + t
        w = as_keyword(tok)
        j = i
        k = 0
        ok = True
        while k < len(w):
            while j < n and s[j] == ' ':
                j += 1
            if j >= n or s[j].upper() != w[k]:
                ok = False
                break
            j += 1
            k += 1
        if not ok:
            continue
        if tok == 0xC5:  # TK_AT
            if j - i != 2:
                continue
            k2 = j
            while k2 < n and s[k2] == ' ':
                k2 += 1
            if k2 < n:
                c = s[k2].upper()
                if c in ('N', 'O'):
                    continue
        return tok, j
    return None, None


class AsTokenized:
    __slots__ = ("bytes", "src", "src_n", "klass", "source_len")

    def __init__(self, bytes_, src, src_n, klass, source_len):
        self.bytes = bytes_   # bytes
        self.src = src        # list[int] source offset per token byte
        self.src_n = src_n    # list[int] source length per token byte
        self.klass = klass    # bytearray parallel to source text
        self.source_len = source_len


def as_tokenize(src):
    """Tokenize one program line (no line number). Never fails on text."""
    if src is None:
        src = ""
    n = len(src)
    klass = bytearray(n if n else 1)
    out_bytes = []
    out_src = []
    out_src_n = []

    def add(c, s, sn):
        out_bytes.append(c)
        out_src.append(s)
        out_src_n.append(sn)

    def mark_kw(begin, end):
        for i in range(begin, end):
            if src[i] != ' ':
                klass[i] = AS_CLS_KEYWORD

    data = False
    amp_name = False
    i = 0
    while i < n:
        c = src[i]
        if not data and c == ' ':
            i += 1
            continue
        if not data and c == '"':
            start = i
            i += 1
            while i < n and src[i] != '"':
                i += 1
            if i < n and src[i] == '"':
                i += 1
            while start < i:
                add(ord(src[start]), start, 1)
                start += 1
            continue
        if data:
            if c == ':':
                data = False
                add(ord(':'), i, 1)
                i += 1
                continue
            if c == '"':
                start = i
                i += 1
                while i < n and src[i] != '"':
                    i += 1
                if i < n and src[i] == '"':
                    i += 1
                while start < i:
                    add(ord(src[start]), start, 1)
                    start += 1
                continue
            add(ord(c), i, 1)
            i += 1
            continue
        if c == '?':
            add(TK_PRINT, i, 1)
            klass[i] = AS_CLS_KEYWORD
            i += 1
            continue
        if amp_name:
            if ('A' <= c <= 'Z') or ('a' <= c <= 'z'):
                cmd = _ext_command(src, n, i)
                end = i + cmd if cmd else i
                if not cmd:
                    while end < n:
                        ch = src[end].upper()
                        if not ('A' <= ch <= 'Z'):
                            break
                        end += 1
                while i < end:
                    ch = src[i].upper()
                    add(ord(ch), i, 1)
                    klass[i] = AS_CLS_KEYWORD
                    i += 1
                amp_name = False
                if i < n and src[i] == ' ':
                    add(ord(' '), i, 1)
                    while i < n and src[i] == ' ':
                        i += 1
                continue
            amp_name = False
        if '0' <= c <= ';':
            varish = i > 0 and klass[i - 1] == AS_CLS_VARIABLE and '0' <= c <= '9'
            add(ord(c), i, 1)
            if varish:
                klass[i] = AS_CLS_VARIABLE
            i += 1
            continue
        token, end = _kw_match(src, n, i)
        if token is not None:
            span = end - i
            if span == 0:
                span = 1
            add(token, i, span)
            mark_kw(i, end)
            i = end
            amp_name = (token == TK_AMP)
            if token == TK_DATA:
                data = True
            if token == TK_REM:
                while i < n:
                    add(ord(src[i]), i, 1)
                    klass[i] = AS_CLS_REMARK
                    i += 1
                break
            continue
        outc = c
        cls = AS_CLS_PLAIN
        if 'a' <= c <= 'z':
            outc = c.upper()
        if 'A' <= outc <= 'Z':
            cls = AS_CLS_VARIABLE
        elif c in ('$', '%') and i > 0 and klass[i - 1] == AS_CLS_VARIABLE:
            cls = AS_CLS_VARIABLE
        add(ord(outc), i, 1)
        klass[i] = cls
        i += 1

    add(0, n, 0)
    length = len(out_bytes) - 1
    return AsTokenized(bytes(out_bytes), out_src, out_src_n, klass, n), length


def as_tokenize_simple(src):
    """Convenience: returns just the token bytes (trailing 0 included), matching
    the C AsTokenized.bytes / len split used by callers that don't need klass."""
    t, length = as_tokenize(src)
    return t.bytes[:length]


def _skip_string_tokens(t, pc):
    if pc < len(t.bytes) and t.bytes[pc] == ord('"'):
        pc += 1
    while pc < len(t.bytes) and t.bytes[pc] != ord('"'):
        pc += 1
    if pc < len(t.bytes) and t.bytes[pc] == ord('"'):
        pc += 1
    return pc


def _take_num(t, pc):
    """Returns (status, num, begin, end, new_pc). status: 1 number, 0 not a
    number, -1 digits that overflow a legal line number."""
    i = pc
    tb = t.bytes
    if i >= len(tb) or not (ord('0') <= tb[i] <= ord('9')):
        return 0, 0, 0, 0, pc
    begin = t.src[i]
    v = 0
    overflow = False
    while i < len(tb) and ord('0') <= tb[i] <= ord('9'):
        if v > 6399:
            overflow = True
        else:
            v = v * 10 + (tb[i] - ord('0'))
        if v > 63999:
            overflow = True
        i += 1
    end = t.src[i - 1] + t.src_n[i - 1]
    if overflow:
        return -1, 0, begin, end, i
    return 1, v, begin, end, i


def _each_jump(t, fn):
    """fn(num, begin, end) -> True to stop early."""
    tb = t.bytes
    pc = 0
    length = len(tb)
    while pc < length:
        c = tb[pc]
        if c == TK_REM:
            return
        if c == ord('"'):
            pc = _skip_string_tokens(t, pc)
            continue
        if c == TK_DATA:
            pc += 1
            while pc < length and tb[pc] != ord(':'):
                pc += 1
            continue
        if c == TK_ON:
            depth = 0
            pc += 1
            while pc < length and tb[pc] != ord(':'):
                if tb[pc] == ord('"'):
                    pc = _skip_string_tokens(t, pc)
                    continue
                if tb[pc] == ord('('):
                    depth += 1
                elif tb[pc] == ord(')') and depth:
                    depth -= 1
                if depth == 0 and tb[pc] in (TK_GOTO, TK_GOSUB):
                    break
                pc += 1
            if pc < length and tb[pc] in (TK_GOTO, TK_GOSUB):
                pc += 1
                while True:
                    status, num, b, e, pc = _take_num(t, pc)
                    if status <= 0:
                        break
                    if fn(num, b, e):
                        return
                    if pc < length and tb[pc] == ord(','):
                        pc += 1
                        continue
                    break
            continue
        if c in (TK_GOTO, TK_GOSUB, TK_THEN):
            pc += 1
            status, num, b, e, pc = _take_num(t, pc)
            if status > 0 and fn(num, b, e):
                return
            continue
        pc += 1


def as_jump_numbers(src, cap=4096):
    """GOTO/GOSUB/THEN line numbers including each ON ... list entry.
    Returns a list of (number, begin, end) tuples, source-offset spans."""
    if not src:
        return []
    t, length = as_tokenize(src)
    t.bytes = t.bytes  # already includes trailing 0; _each_jump uses len(bytes)
    out = []

    def collect(num, b, e):
        if len(out) < cap:
            out.append((num, b, e))
        return False

    _each_jump(t, collect)
    return out


def as_jump_number_at(src, index):
    """If `index` falls in one of those numbers, return (number, begin, end); else None."""
    if not src:
        return None
    t, length = as_tokenize(src)
    result = [None]

    def at(num, b, e):
        if index < b or index >= e:
            return False
        result[0] = (num, b, e)
        return True

    _each_jump(t, at)
    return result[0]


def as_detokenize(token_bytes):
    """LIST-style text: a space before and after each keyword."""
    out = []
    amp_name = False
    for c in token_bytes:
        kw = as_keyword(c) if c >= TK_FIRST else None
        if kw is not None:
            out.append(' ')
            out.append(kw)
            out.append(' ')
            amp_name = (c == TK_AMP)
        else:
            ch = chr(c)
            gap = amp_name and not ('A' <= ch <= 'Z')
            if gap:
                amp_name = False
            if gap and ch != ' ' and out and out[-1] and out[-1][-1] != ' ':
                out.append(' ')
            out.append(ch)
    text = ''.join(out)
    text = text.rstrip(' ')
    text = text.lstrip(' ')
    return text
