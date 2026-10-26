import sys
sys.path.insert(0, '..')
from applesoft.as_program import AsProgram
from applesoft.as_screen import AsScreen
from applesoft.as_exec import AsMachine
from applesoft.as_tokenize import as_tokenize
from applesoft.as_common import AS_END, AS_OK


def load_program(m, lines):
    for ln in lines:
        num, _, rest = ln.partition(' ')
        t, length = as_tokenize(rest)
        m.prog.upsert(int(num), t.bytes[:length], 0)


def dump_screen(screen):
    for y in range(24):
        row = ''.join(chr(screen.cell[y][x].ch) for x in range(40))
        if row.strip():
            print(repr(row.rstrip()))


prog = AsProgram()
screen = AsScreen()
m = AsMachine(prog, screen)

load_program(m, [
    "10 FOR I = 1 TO 5",
    "20 PRINT I; \" SQUARED IS \"; I*I",
    "30 NEXT I",
    "40 PRINT \"DONE\"",
    "50 END",
])

m.run()
guard = 0
while m.running and guard < 100000:
    rc = m.quantum(0.01)
    guard += 1
    if rc == AS_END:
        break

print("status:", m.status)
dump_screen(screen)
