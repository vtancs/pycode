import sys
sys.path.insert(0, '..')
from applesoft.as_program import AsProgram
from applesoft.as_screen import AsScreen
from applesoft.as_exec import AsMachine, as_check_line
from applesoft.as_tokenize import as_tokenize
from applesoft.as_common import AS_END, AS_OK, AS_ERR_SYNTAX, as_error_text


def run_prog(lines, max_steps=100000):
    prog = AsProgram()
    screen = AsScreen()
    m = AsMachine(prog, screen)
    for ln in lines:
        num, _, rest = ln.partition(' ')
        t, length = as_tokenize(rest)
        prog.upsert(int(num), t.bytes[:length], 0)
    m.run()
    steps = 0
    while m.running and steps < max_steps:
        m.quantum(0.05)
        steps += 1
    return m, screen


def text_of(screen):
    out = []
    for y in range(24):
        row = ''.join(chr(screen.cell[y][x].ch) for x in range(40)).rstrip()
        if row:
            out.append(row)
    return out


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        raise SystemExit(1)


# 1. Arrays, strings, LEFT$/MID$/RIGHT$, string concat
m, s = run_prog([
    "10 DIM A(5)",
    "20 FOR I = 0 TO 5 : A(I) = I*I : NEXT I",
    "30 S$ = \"HELLO WORLD\"",
    "40 PRINT LEFT$(S$,5); \"/\"; MID$(S$,7,5); \"/\"; RIGHT$(S$,5)",
    "50 PRINT A(4) + A(2)",
])
check("arrays+strings", text_of(s) == ['HELLO/WORLD/WORLD', ' 20'])

# 2. GOSUB/RETURN + IF/THEN + ON GOTO
m, s = run_prog([
    "10 GOSUB 100",
    "20 PRINT \"BACK\"",
    "30 ON X GOTO 200,210,220",
    "40 END",
    "100 PRINT \"SUB\"",
    "110 RETURN",
    "200 PRINT \"ONE\" : END",
    "210 PRINT \"TWO\" : END",
    "220 PRINT \"THREE\" : END",
])
# X undefined (0) -> ON GOTO falls through
check("gosub+if", text_of(s) == ['SUB', 'BACK'])

# 3. error handling via division by zero + status
m, s = run_prog(["10 PRINT 1/0"])
check("div-by-zero error text", "DIVISION BY ZERO" in m.status)

# 4. ONERR GOTO
m, s = run_prog([
    "10 ONERR GOTO 100",
    "20 PRINT 1/0",
    "30 END",
    "100 PRINT \"CAUGHT\" : END",
])
check("onerr", 'CAUGHT' in text_of(s))

# 5. PEEK/POKE roundtrip via text window vars (32/33/34/35/36/37)
m, s = run_prog([
    "10 POKE 36, 5",
    "20 PRINT PEEK(36)",
])
check("peek/poke", text_of(s)[-1].strip() == '5')

# 6. GR/PLOT/SCRN
m, s = run_prog([
    "10 GR",
    "20 COLOR= 7",
    "30 PLOT 2,3",
    "40 PRINT SCRN(2,3)",
])
check("gr+plot+scrn", text_of(s)[-1].strip() == '7')

# 7. RND determinism (seeded negative)
m, s = run_prog([
    "10 X = RND(-5)",
    "20 PRINT RND(1) = RND(1)",
])
check("rnd", text_of(s) == [' 0'])

# 8. syntax check (editor support)
t, length = as_tokenize("PRINT 1 +")
rc, err_at = as_check_line(t.bytes[:length])
check("check_line detects syntax error", rc == AS_ERR_SYNTAX)
t, length = as_tokenize("PRINT 1 + 2")
rc, err_at = as_check_line(t.bytes[:length])
check("check_line accepts good line", rc == AS_OK)

# 9. DATA/READ/RESTORE
m, s = run_prog([
    "10 DATA 1,2,3",
    "20 READ A,B,C",
    "30 PRINT A+B+C",
    "40 RESTORE",
    "50 READ D",
    "60 PRINT D",
])
check("data/read/restore", text_of(s) == [' 6', ' 1'])

print("ALL PASS")
