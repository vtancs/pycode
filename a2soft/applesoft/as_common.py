"""Error codes, token value types, and classification constants.

Direct port of as_common.h / common.c.
"""

(AS_OK, AS_ERR_NEXT_WITHOUT_FOR, AS_ERR_SYNTAX, AS_ERR_RETURN_WITHOUT_GOSUB,
 AS_ERR_OUT_OF_DATA, AS_ERR_ILLEGAL_QUANTITY, AS_ERR_OVERFLOW, AS_ERR_OUT_OF_MEMORY,
 AS_ERR_UNDEF_STATEMENT, AS_ERR_BAD_SUBSCRIPT, AS_ERR_REDIMD_ARRAY, AS_ERR_DIVISION_BY_ZERO,
 AS_ERR_ILLEGAL_DIRECT, AS_ERR_TYPE_MISMATCH, AS_ERR_STRING_TOO_LONG, AS_ERR_FORMULA_TOO_COMPLEX,
 AS_ERR_CANT_CONTINUE, AS_ERR_UNDEF_FUNCTION, AS_ERR_CALL, AS_ERR_NOT_SUPPORTED,
 AS_STOPPED, AS_PAUSED, AS_END, AS_INPUT, AS_GET, AS_DELAY) = range(26)

AS_NUM = 0
AS_STR = 1

AS_T_FLOAT = 0
AS_T_INT = 1
AS_T_STR = 2

AS_CLS_PLAIN = 0
AS_CLS_KEYWORD = 1
AS_CLS_VARIABLE = 2
AS_CLS_REMARK = 3

_ERR_TEXT = {
    AS_ERR_NEXT_WITHOUT_FOR: "NEXT WITHOUT FOR",
    AS_ERR_SYNTAX: "SYNTAX ERROR",
    AS_ERR_RETURN_WITHOUT_GOSUB: "RETURN WITHOUT GOSUB",
    AS_ERR_OUT_OF_DATA: "OUT OF DATA",
    AS_ERR_ILLEGAL_QUANTITY: "ILLEGAL QUANTITY",
    AS_ERR_OVERFLOW: "OVERFLOW",
    AS_ERR_OUT_OF_MEMORY: "OUT OF MEMORY",
    AS_ERR_UNDEF_STATEMENT: "UNDEF'D STATEMENT",
    AS_ERR_BAD_SUBSCRIPT: "BAD SUBSCRIPT",
    AS_ERR_REDIMD_ARRAY: "REDIM'D ARRAY",
    AS_ERR_DIVISION_BY_ZERO: "DIVISION BY ZERO",
    AS_ERR_ILLEGAL_DIRECT: "ILLEGAL DIRECT",
    AS_ERR_TYPE_MISMATCH: "TYPE MISMATCH",
    AS_ERR_STRING_TOO_LONG: "STRING TOO LONG",
    AS_ERR_FORMULA_TOO_COMPLEX: "FORMULA TOO COMPLEX",
    AS_ERR_CANT_CONTINUE: "CAN'T CONTINUE",
    AS_ERR_UNDEF_FUNCTION: "UNDEF'D FUNCTION",
    AS_ERR_CALL: "CALL NOT SUPPORTED",
    AS_ERR_NOT_SUPPORTED: "NOT SUPPORTED",
}


def as_error_text(err):
    return _ERR_TEXT.get(err, "ERROR")


class AsError(Exception):
    """Raised internally to unwind to the statement dispatcher with an error code."""

    def __init__(self, code):
        super().__init__(as_error_text(code))
        self.code = code


class AsValue:
    __slots__ = ("type", "num", "str")

    def __init__(self, type=AS_NUM, num=0.0, str=b""):
        self.type = type
        self.num = num
        self.str = str

    @staticmethod
    def of_num(n):
        return AsValue(AS_NUM, float(n), b"")

    @staticmethod
    def of_str(s):
        if len(s) > 255:
            raise AsError(AS_ERR_STRING_TOO_LONG)
        return AsValue(AS_STR, 0.0, bytes(s))
