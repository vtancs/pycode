"""Token byte values and keyword text. Direct port of as_token.h / token.c."""

TK_FIRST = 0x80

(TK_END, TK_FOR, TK_NEXT, TK_DATA, TK_INPUT, TK_DEL, TK_DIM, TK_READ,
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
 TK_LEFT, TK_RIGHT, TK_MID) = range(TK_FIRST, TK_FIRST + 107)

TK_LAST = TK_MID
TK_COUNT = TK_LAST - TK_FIRST + 1

assert TK_PRINT == 0xBA
assert TK_FOR == 0x81
assert TK_GOTO == 0xAB
assert TK_GOSUB == 0xB0
assert TK_AT == 0xC5
assert TK_SGN == 0xD2
assert TK_MID == 0xEA
assert TK_COUNT == 107

_KW = [
    "END", "FOR", "NEXT", "DATA", "INPUT", "DEL", "DIM", "READ",
    "GR", "TEXT", "PR#", "IN#", "CALL", "PLOT", "HLIN", "VLIN",
    "HGR2", "HGR", "HCOLOR=", "HPLOT", "DRAW", "XDRAW", "HTAB", "HOME",
    "ROT=", "SCALE=", "SHLOAD", "TRACE", "NOTRACE", "NORMAL", "INVERSE", "FLASH",
    "COLOR=", "POP", "VTAB", "HIMEM:", "LOMEM:", "ONERR", "RESUME", "RECALL",
    "STORE", "SPEED=", "LET", "GOTO", "RUN", "IF", "RESTORE", "&",
    "GOSUB", "RETURN", "REM", "STOP", "ON", "WAIT", "LOAD", "SAVE",
    "DEF", "POKE", "PRINT", "CONT", "LIST", "CLEAR", "GET", "NEW",
    "TAB(", "TO", "FN", "SPC(", "THEN", "AT", "NOT", "STEP",
    "+", "-", "*", "/", "^", "AND", "OR", ">",
    "=", "<", "SGN", "INT", "ABS", "USR", "FRE", "SCRN(",
    "PDL", "POS", "SQR", "RND", "LOG", "EXP", "COS", "SIN",
    "TAN", "ATN", "PEEK", "LEN", "STR$", "VAL", "ASC", "CHR$",
    "LEFT$", "RIGHT$", "MID$",
]


def as_keyword(token):
    if token < TK_FIRST or token > TK_LAST:
        return None
    return _KW[token - TK_FIRST]


# Reverse lookup used by the tokenizer: longest-keyword-first match.
_KW_BY_TEXT = [(kw, TK_FIRST + i) for i, kw in enumerate(_KW)]
_KW_BY_TEXT.sort(key=lambda p: -len(p[0]))
