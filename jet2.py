import pywavefront
import pygame
import numpy as np
import math

# --- Load OBJ ---
scene = pywavefront.Wavefront('f16.obj', create_materials=True, collect_faces=True)
raw_vertices = np.array(scene.vertices)

# --- Build edge list from faces ---
edge_set = set()
for mesh in scene.mesh_list:
    for face in mesh.faces:
        for i in range(len(face)):
            v1, v2 = face[i], face[(i+1) % len(face)]
            edge_set.add(tuple(sorted((v1, v2))))
edges = list(edge_set)

# --- Normalize model ---
def normalize(vertices):
    center = vertices.mean(axis=0)
    vertices = vertices - center
    scale = np.abs(vertices).max()
    return vertices / scale

vertices = normalize(raw_vertices)

# --- Rotation & projection ---
def rotate(points, ax, ay):
    Rx = np.array([[1,0,0],[0,math.cos(ax),-math.sin(ax)],[0,math.sin(ax),math.cos(ax)]])
    Ry = np.array([[math.cos(ay),0,math.sin(ay)],[0,1,0],[-math.sin(ay),0,math.cos(ay)]])
    return points @ Rx.T @ Ry.T

WIDTH, HEIGHT = 900, 700
def project(pts, scale=300, dist=3):
    proj = []
    for x, y, z in pts:
        f = scale / (z + dist)
        proj.append((WIDTH//2 + int(x * f), HEIGHT//2 - int(y * f)))
    return proj

# --- Pygame setup ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("F‑16 Wireframe Animation")
clock = pygame.time.Clock()
angle_x = angle_y = 0
frame = 0

running = True
while running:
    screen.fill((0, 0, 0))
    for evt in pygame.event.get():
        if evt.type == pygame.QUIT:
            running = False

    rotated = rotate(vertices, math.radians(angle_x), math.radians(angle_y))
    proj = project(rotated)
    edges_to_show = min(len(edges), frame // 2 + 1)

    for i, (a, b) in enumerate(edges):
        if i < edges_to_show:
            pygame.draw.aaline(screen, (0, 255, 255), proj[a], proj[b])

    angle_x += 0.8
    angle_y += 1.0
    frame += 1
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
