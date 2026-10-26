"""Program listing storage, renumbering, and the DOS 3.3 .abas file format.

Port of as_program.h / program.c. A Python list (kept sorted by line number)
replaces the C linked list; behavior is otherwise 1:1.
"""

from .as_common import AsError, AS_OK, AS_ERR_ILLEGAL_QUANTITY, AS_ERR_OUT_OF_MEMORY, AS_ERR_SYNTAX
from .as_token import TK_REM, TK_DATA, TK_ON, TK_GOTO, TK_GOSUB, TK_THEN, TK_RUN, TK_RESTORE


class AsLine:
    __slots__ = ("number", "breakpoint", "tokens", "next")

    def __init__(self, number, tokens=b"", breakpoint=0):
        self.number = number
        self.tokens = bytes(tokens)
        self.breakpoint = breakpoint
        self.next = None  # relinked by AsProgram whenever lines[] changes

    @property
    def len(self):
        return len(self.tokens)


def _copy_string_span(t, pc):
    n = len(t)
    if pc < n and t[pc] == ord('"'):
        pc += 1
    while pc < n and t[pc] != ord('"'):
        pc += 1
    if pc < n and t[pc] == ord('"'):
        pc += 1
    return pc


def _read_num(t, pc):
    """Returns (status, num, next_pc). status 1 ok, 0 not a number, -1 overflow."""
    n = len(t)
    v = 0
    any_digit = False
    i = pc
    if i >= n or not (ord('0') <= t[i] <= ord('9')):
        return 0, 0, pc
    while i < n and ord('0') <= t[i] <= ord('9'):
        v = v * 10 + (t[i] - ord('0'))
        if v > 63999:
            return -1, 0, i
        i += 1
        any_digit = True
    if not any_digit:
        return 0, 0, pc
    return 1, v, i


def _collect_targets(tokens, targets):
    t = tokens
    n = len(t)
    pc = 0
    while pc < n:
        c = t[pc]
        if c == TK_REM:
            return
        if c == ord('"'):
            pc = _copy_string_span(t, pc)
            continue
        if c == TK_DATA:
            pc += 1
            while pc < n and t[pc] != ord(':'):
                pc += 1
            continue
        if c == TK_ON:
            depth = 0
            pc += 1
            while pc < n and t[pc] != ord(':'):
                if t[pc] == ord('"'):
                    pc = _copy_string_span(t, pc)
                    continue
                if t[pc] == ord('('):
                    depth += 1
                elif t[pc] == ord(')') and depth:
                    depth -= 1
                if depth == 0 and t[pc] in (TK_GOTO, TK_GOSUB):
                    break
                pc += 1
            if pc < n and t[pc] in (TK_GOTO, TK_GOSUB):
                pc += 1
                while True:
                    status, num, nxt = _read_num(t, pc)
                    if status <= 0:
                        break
                    targets.add(num)
                    pc = nxt
                    if pc < n and t[pc] == ord(','):
                        pc += 1
                        continue
                    break
            continue
        if c in (TK_GOTO, TK_GOSUB, TK_THEN, TK_RUN, TK_RESTORE):
            pc += 1
            status, num, nxt = _read_num(t, pc)
            if status > 0:
                targets.add(num)
                pc = nxt
            continue
        pc += 1


def _rewrite_tokens(tokens, line_map):
    """line_map: dict old_number -> new_number. Rewrites GOTO/GOSUB/THEN/RUN/RESTORE/ON targets."""
    t = tokens
    n = len(t)
    out = bytearray()
    pc = 0

    def mapped(num):
        return line_map.get(num, num)

    while pc < n:
        c = t[pc]
        if c == TK_REM:
            out.extend(t[pc:])
            break
        if c == ord('"'):
            start = pc
            pc = _copy_string_span(t, pc)
            out.extend(t[start:pc])
            continue
        if c == TK_DATA:
            out.append(c)
            pc += 1
            while pc < n and t[pc] != ord(':'):
                out.append(t[pc])
                pc += 1
            continue
        if c == TK_ON:
            depth = 0
            out.append(c)
            pc += 1
            while pc < n and t[pc] != ord(':'):
                if t[pc] == ord('"'):
                    start = pc
                    pc = _copy_string_span(t, pc)
                    out.extend(t[start:pc])
                    continue
                if t[pc] == ord('('):
                    depth += 1
                elif t[pc] == ord(')') and depth:
                    depth -= 1
                if depth == 0 and t[pc] in (TK_GOTO, TK_GOSUB):
                    break
                out.append(t[pc])
                pc += 1
            if pc < n and t[pc] in (TK_GOTO, TK_GOSUB):
                out.append(t[pc])
                pc += 1
                while True:
                    status, num, nxt = _read_num(t, pc)
                    if status <= 0:
                        break
                    out.extend(str(mapped(num)).encode('ascii'))
                    pc = nxt
                    if pc < n and t[pc] == ord(','):
                        out.append(ord(','))
                        pc += 1
                        continue
                    break
            continue
        if c in (TK_GOTO, TK_GOSUB, TK_THEN, TK_RUN, TK_RESTORE):
            out.append(c)
            pc += 1
            status, num, nxt = _read_num(t, pc)
            if status > 0:
                out.extend(str(mapped(num)).encode('ascii'))
                pc = nxt
            continue
        out.append(c)
        pc += 1
    return bytes(out)


class AsProgram:
    def __init__(self):
        self.lines = []  # sorted by number
        self.dirty = 0
        self._targets = set()

    def clear(self):
        self.lines = []
        self._targets = set()

    def count(self):
        return len(self.lines)

    def at(self, index):
        if 0 <= index < len(self.lines):
            return self.lines[index]
        return None

    def _bisect(self, number):
        lo, hi = 0, len(self.lines)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.lines[mid].number < number:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def find(self, number):
        i = self._bisect(number)
        if i < len(self.lines) and self.lines[i].number == number:
            return self.lines[i]
        return None

    @property
    def head(self):
        return self.lines[0] if self.lines else None

    def _relink(self):
        n = len(self.lines)
        for i, ln in enumerate(self.lines):
            ln.next = self.lines[i + 1] if i + 1 < n else None

    def rebuild_targets(self):
        self._relink()
        targets = set()
        for ln in self.lines:
            _collect_targets(ln.tokens, targets)
        self._targets = targets

    def is_target(self, number):
        return number in self._targets

    def upsert(self, number, tokens, breakpoint=0):
        if number > 63999:
            raise AsError(AS_ERR_ILLEGAL_QUANTITY)
        i = self._bisect(number)
        existing = self.lines[i] if i < len(self.lines) and self.lines[i].number == number else None
        if len(tokens) == 0:
            if existing is not None:
                del self.lines[i]
                self.dirty = 1
                self.rebuild_targets()
            return
        if existing is not None:
            existing.tokens = bytes(tokens)
            existing.breakpoint = breakpoint
        else:
            self.lines.insert(i, AsLine(number, tokens, breakpoint))
        self.dirty = 1
        self.rebuild_targets()

    def set_break(self, index, on):
        ln = self.at(index)
        if ln:
            ln.breakpoint = 1 if on else 0

    def delete_range(self, first, last):
        if first > last:
            first, last = last, first
        self.lines = [ln for ln in self.lines if not (first <= ln.number <= last)]
        self.dirty = 1
        self.rebuild_targets()

    def renumber(self, start, step):
        if step == 0:
            raise AsError(AS_ERR_ILLEGAL_QUANTITY)
        line_map = {}
        new_numbers = []
        num = start
        for ln in self.lines:
            if num > 63999:
                raise AsError(AS_ERR_ILLEGAL_QUANTITY)
            line_map[ln.number] = num
            new_numbers.append(num)
            num += step
        for ln, new_num in zip(self.lines, new_numbers):
            ln.tokens = _rewrite_tokens(ln.tokens, line_map)
            ln.number = new_num
        self.dirty = 1
        self.rebuild_targets()

    def mark_clean(self):
        self.dirty = 0

    # -- DOS 3.3 AppleSoft image, based at $0801 ---------------------------
    def save(self):
        """Returns bytes. Raises AsError(AS_ERR_OUT_OF_MEMORY) if too big."""
        total = 2
        for ln in self.lines:
            total += 4 + len(ln.tokens) + 1
        if total > 0x8DFF:
            raise AsError(AS_ERR_OUT_OF_MEMORY)
        buf = bytearray()
        addr = 0x0801
        for ln in self.lines:
            nxt = addr + 4 + len(ln.tokens) + 1
            buf.append(nxt & 0xff)
            buf.append((nxt >> 8) & 0xff)
            buf.append(ln.number & 0xff)
            buf.append((ln.number >> 8) & 0xff)
            buf.extend(ln.tokens)
            buf.append(0)
            addr = nxt
        buf.append(0)
        buf.append(0)
        return bytes(buf)

    def load(self, data):
        """Replaces this program's contents in place from a DOS 3.3 image.
        Raises AsError(AS_ERR_SYNTAX) / AsError(AS_ERR_OUT_OF_MEMORY) on bad data."""
        if not data or len(data) < 2:
            raise AsError(AS_ERR_SYNTAX)
        tmp = AsProgram()
        off = 0
        prev = 0
        have_prev = False
        n = len(data)
        while off + 1 < n:
            nxt = data[off] | (data[off + 1] << 8)
            if nxt == 0:
                if off + 2 != n:
                    raise AsError(AS_ERR_SYNTAX)
                break
            if nxt < 0x0801:
                raise AsError(AS_ERR_SYNTAX)
            next_off = nxt - 0x0801
            if next_off > n or next_off <= off + 4:
                raise AsError(AS_ERR_SYNTAX)
            lno = data[off + 2] | (data[off + 3] << 8)
            if lno > 63999 or (have_prev and lno <= prev):
                raise AsError(AS_ERR_SYNTAX)
            tok_end = next_off
            if data[tok_end - 1] != 0:
                raise AsError(AS_ERR_SYNTAX)
            for i in range(off + 4, tok_end - 1):
                if data[i] == 0:
                    raise AsError(AS_ERR_SYNTAX)
            tok_len = tok_end - (off + 4) - 1
            tmp.upsert(lno, data[off + 4:off + 4 + tok_len], 0)
            prev = lno
            have_prev = True
            off = next_off
        if off + 2 != n:
            raise AsError(AS_ERR_SYNTAX)
        self.lines = tmp.lines
        self.rebuild_targets()
        self.dirty = 0
