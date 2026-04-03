import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import math
import ctypes

# --- Window ---
WIDTH, HEIGHT = 800, 600
pygame.init()
pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)

# --- Enable blending ---
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# --- Simple shader ---
VERTEX_SHADER = """
#version 330
layout(location = 0) in vec3 position;
layout(location = 1) in vec3 color;
out vec3 vColor;
void main() {
    gl_Position = vec4(position, 1.0);
    gl_PointSize = 1.0;
    vColor = color;
}
"""

FRAGMENT_SHADER = """
#version 330
in vec3 vColor;
out vec4 fragColor;
void main() {
    fragColor = vec4(vColor, 1.0);
}
"""

shader = compileProgram(
    compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
    compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
)

glUseProgram(shader)

# --- Parameters ---
N = 25000
HALFPI = math.pi / 2

A_START = 3.54
A_END = 4.0
A_SUM = A_START + A_END

DSCR = 2
DXYZ = 3
SCALE = 1.6
DSCRSCALE = DSCR * SCALE

YZANGLE = math.radians(30)
COS_YZ = math.cos(YZANGLE)
SIN_YZ = math.sin(YZANGLE)

def logistic(x, a):
    return a * x * (1 - x)

def hsb_to_rgb(h):
    import colorsys
    return colorsys.hsv_to_rgb(h / 360.0, 1, 1)

vbo = glGenBuffers(1)

frame = 0
rotation = 0

clock = pygame.time.Clock()
running = True

# --- Fade strength (KEY PARAMETER) ---
FADE_ALPHA = 0.08   # lower = longer trails

while running:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Fade previous frame (THIS is the trail effect) ---
    glUseProgram(0)
    glColor4f(0, 0, 0, FADE_ALPHA)

    glBegin(GL_QUADS)
    glVertex2f(-1, -1)
    glVertex2f(1, -1)
    glVertex2f(1, 1)
    glVertex2f(-1, 1)
    glEnd()

    glUseProgram(shader)

    # --- Animate parameters ---
    t = (math.sin(frame * 0.02) + 1) / 2
    ar = A_START + (A_END - A_START) * t
    ad1 = A_SUM - ar
    ad2 = ar * 0.4 + ad1 * 0.6

    r = d1 = d2 = 0.5
    vertices = []

    for i in range(N):
        r  = logistic(r, ar)
        d1 = logistic(d1, ad1)
        d2 = logistic(d2, ad2)

        angle1 = HALFPI * (d1 + rotation / 90)
        angle2 = HALFPI * d2

        rsin = r * math.sin(angle2)

        x = rsin * math.cos(angle1)
        y = rsin * math.sin(angle1)
        z = r * math.cos(angle2)

        hue = r * 360
        cr, cg, cb = hsb_to_rgb(hue)

        points = [
            (x, y, z),
            (-y, x, z),
            (-x, -y, z),
            (y, -x, z),
        ]

        for px, py, pz in points:
            yr = py * COS_YZ - pz * SIN_YZ
            zr = py * SIN_YZ + pz * COS_YZ

            denom = DXYZ + yr
            if denom <= 0:
                continue

            f = DSCRSCALE / denom

            vx = px * f
            vy = zr * f

            vertices.extend([vx, vy, 0, cr, cg, cb])

    vertices = np.array(vertices, dtype=np.float32)

    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)

    stride = 6 * 4

    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 3, GL_FLOAT, False, stride, None)

    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 3, GL_FLOAT, False, stride, ctypes.c_void_p(12))

    glDrawArrays(GL_POINTS, 0, len(vertices) // 6)

    pygame.display.flip()

    rotation += 1
    frame += 1

pygame.quit()