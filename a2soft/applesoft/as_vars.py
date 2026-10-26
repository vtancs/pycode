"""Variable and array storage. Port of as_vars.h / vars.c.

Deviation from the C original: errors are raised as AsError(code) instead of
returned as int codes (idiomatic for Python; callers in as_exec.py catch AsError).
"""

from .as_common import (
    AsError, AsValue, AS_NUM, AS_STR, AS_T_FLOAT, AS_T_INT, AS_T_STR,
    AS_ERR_SYNTAX, AS_ERR_TYPE_MISMATCH, AS_ERR_ILLEGAL_QUANTITY,
    AS_ERR_BAD_SUBSCRIPT, AS_ERR_REDIMD_ARRAY, AS_ERR_OUT_OF_MEMORY,
)

AS_NVARS = 962


def as_name_index(c1, c2):
    """Map a variable's first two significant letters/digits to a 0..961 slot."""
    if c1 < ord('A') or c1 > ord('Z'):
        return -1
    if c2 == 0:
        second = 0
    elif ord('A') <= c2 <= ord('Z'):
        second = 1 + (c2 - ord('A'))
    elif ord('0') <= c2 <= ord('9'):
        second = 27 + (c2 - ord('0'))
    else:
        return -1
    return (c1 - ord('A')) * 37 + second


class AsRef:
    """Mirrors AsRef in as_vars.h: a resolved scalar or array variable reference."""

    __slots__ = ("is_array", "type", "name", "ndims", "subs")

    def __init__(self, is_array=False, type=AS_T_FLOAT, name=-1, ndims=0, subs=None):
        self.is_array = is_array
        self.type = type
        self.name = name
        self.ndims = ndims
        self.subs = subs if subs is not None else []


class _Array:
    __slots__ = ("name", "type", "dim", "count", "num", "intg", "s")

    def __init__(self, name, type, dim):
        self.name = name
        self.type = type
        self.dim = list(dim)
        count = 1
        for d in dim:
            if d < 1:
                raise AsError(AS_ERR_BAD_SUBSCRIPT)
            if count > 100000 // d:
                raise AsError(AS_ERR_OUT_OF_MEMORY)
            count *= d
        self.count = count
        if type == AS_T_FLOAT:
            self.num = [0.0] * count
            self.intg = None
            self.s = None
        elif type == AS_T_INT:
            self.num = None
            self.intg = [0] * count
            self.s = None
        else:
            self.num = None
            self.intg = None
            self.s = [b""] * count

    def offset(self, subs):
        if len(subs) != self.ndims():
            raise AsError(AS_ERR_BAD_SUBSCRIPT)
        off = 0
        stride = 1
        for i in range(len(subs) - 1, -1, -1):
            if subs[i] < 0 or subs[i] >= self.dim[i]:
                raise AsError(AS_ERR_BAD_SUBSCRIPT)
            off += subs[i] * stride
            stride *= self.dim[i]
        return off

    def ndims(self):
        return len(self.dim)


class AsVars:
    def __init__(self):
        self.flt = [0.0] * AS_NVARS
        self.intg = [0] * AS_NVARS
        self.s = [b""] * AS_NVARS
        self.arrays = {}  # (name, type) -> _Array

    def clear(self):
        self.flt = [0.0] * AS_NVARS
        self.intg = [0] * AS_NVARS
        self.s = [b""] * AS_NVARS
        self.arrays = {}

    def get_scalar(self, type, name):
        if name < 0 or name >= AS_NVARS:
            raise AsError(AS_ERR_SYNTAX)
        if type == AS_T_INT:
            return self.intg[name]
        if type == AS_T_FLOAT:
            return self.flt[name]
        raise AsError(AS_ERR_TYPE_MISMATCH)

    def set_scalar(self, type, name, value):
        if name < 0 or name >= AS_NVARS:
            raise AsError(AS_ERR_SYNTAX)
        if type == AS_T_INT:
            if value < -32767 or value > 32767:
                raise AsError(AS_ERR_ILLEGAL_QUANTITY)
            self.intg[name] = int(value)
            return
        if type == AS_T_FLOAT:
            self.flt[name] = value
            return
        raise AsError(AS_ERR_TYPE_MISMATCH)

    def _find_array(self, name, type):
        return self.arrays.get((name, type))

    def _alloc_array(self, name, type, dim):
        a = _Array(name, type, dim)
        self.arrays[(name, type)] = a
        return a

    def dim(self, name, type, max_index):
        ndims = len(max_index)
        if ndims < 1 or ndims > 8:
            raise AsError(AS_ERR_BAD_SUBSCRIPT)
        if self._find_array(name, type) is not None:
            raise AsError(AS_ERR_REDIMD_ARRAY)
        for m in max_index:
            if m < 0:
                raise AsError(AS_ERR_BAD_SUBSCRIPT)
        dims = [m + 1 for m in max_index]
        self._alloc_array(name, type, dims)

    def _ensure_auto(self, ref):
        a = self._find_array(ref.name, ref.type)
        if a is not None:
            if a.ndims() != ref.ndims:
                raise AsError(AS_ERR_BAD_SUBSCRIPT)
            return a
        return self._alloc_array(ref.name, ref.type, [11] * ref.ndims)

    def load(self, ref):
        if ref.name < 0 or ref.name >= AS_NVARS:
            raise AsError(AS_ERR_SYNTAX)
        if not ref.is_array:
            if ref.type == AS_T_STR:
                return AsValue.of_str(self.s[ref.name])
            return AsValue.of_num(self.get_scalar(ref.type, ref.name))
        a = self._ensure_auto(ref)
        off = a.offset(ref.subs)
        if ref.type == AS_T_STR:
            return AsValue.of_str(a.s[off])
        if ref.type == AS_T_INT:
            return AsValue.of_num(a.intg[off])
        return AsValue.of_num(a.num[off])

    def store(self, ref, val):
        if ref.name < 0 or ref.name >= AS_NVARS:
            raise AsError(AS_ERR_SYNTAX)
        if ref.type == AS_T_STR:
            if val.type != AS_STR:
                raise AsError(AS_ERR_TYPE_MISMATCH)
        else:
            if val.type != AS_NUM:
                raise AsError(AS_ERR_TYPE_MISMATCH)
            num = val.num
            if ref.type == AS_T_INT and (num < -32767 or num > 32767):
                raise AsError(AS_ERR_ILLEGAL_QUANTITY)
        if not ref.is_array:
            if ref.type == AS_T_STR:
                if len(val.str) > 255:
                    from .as_common import AS_ERR_STRING_TOO_LONG
                    raise AsError(AS_ERR_STRING_TOO_LONG)
                self.s[ref.name] = bytes(val.str)
            elif ref.type == AS_T_INT:
                self.intg[ref.name] = int(num)
            else:
                self.flt[ref.name] = num
            return
        a = self._ensure_auto(ref)
        off = a.offset(ref.subs)
        if ref.type == AS_T_STR:
            if len(val.str) > 255:
                from .as_common import AS_ERR_STRING_TOO_LONG
                raise AsError(AS_ERR_STRING_TOO_LONG)
            a.s[off] = bytes(val.str)
        elif ref.type == AS_T_INT:
            a.intg[off] = int(num)
        else:
            a.num[off] = num
