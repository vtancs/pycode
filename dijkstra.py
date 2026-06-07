import pygame
import heapq
import random
import math

pygame.init()

# =====================================================
# CONFIG
# =====================================================

WIDTH = 1600
HEIGHT = 900

GRAPH_WIDTH = 1100
LOG_WIDTH = WIDTH - GRAPH_WIDTH

BG = (15, 15, 20)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dijkstra Route Visualizer")

clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 24)
SMALL_FONT = pygame.font.SysFont("consolas", 18)

# =====================================================
# LOGGING
# =====================================================

event_log = []


def log(msg):
    event_log.append(msg)

    if len(event_log) > 1000:
        event_log.pop(0)


# =====================================================
# GRAPH GENERATION
# =====================================================

def generate_graph(num_nodes):

    labels = []

    for i in range(num_nodes):

        if i < 26:
            labels.append(chr(65 + i))
        else:
            labels.append(f"N{i}")

    positions = {}

    center_x = GRAPH_WIDTH // 2
    center_y = HEIGHT // 2 - 40

    radius = min(GRAPH_WIDTH, HEIGHT) // 3

    for i, node in enumerate(labels):

        angle = (2 * math.pi * i) / len(labels)

        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)

        positions[node] = (int(x), int(y))

    graph = {n: [] for n in labels}

    # ensure connectivity chain
    for i in range(len(labels) - 1):

        weight = random.randint(1, 15)

        graph[labels[i]].append(
            (labels[i + 1], weight)
        )

    # extra random edges
    for node in labels:

        edge_count = random.randint(2, 4)

        for _ in range(edge_count):

            target = random.choice(labels)

            if target == node:
                continue

            weight = random.randint(1, 15)

            graph[node].append(
                (target, weight)
            )

    return graph, positions


# =====================================================
# DIJKSTRA
# =====================================================

class DijkstraAnimator:

    def __init__(self, graph, start, target):

        self.graph = graph
        self.start = start
        self.target = target

        self.dist = {
            n: float('inf')
            for n in graph
        }

        self.dist[start] = 0

        self.prev = {}

        self.pq = [(0, start)]

        self.current = None
        self.current_edge = None

        self.visited = set()

        self.finished = False

        log(f"Starting at node {start}")

    def step(self):

        if self.finished:
            return

        while self.pq:

            d, node = heapq.heappop(self.pq)

            if node not in self.visited:
                break
        else:
            self.finished = True
            return

        self.current = node

        self.visited.add(node)

        log(
            f"Visit {node} "
            f"(distance={d})"
        )

        if node == self.target:

            self.finished = True

            log("Target reached!")

            path = self.shortest_path()

            log("Path: " + " -> ".join(path))

            return

        for neighbor, weight in self.graph[node]:

            self.current_edge = (node, neighbor)

            nd = d + weight

            log(
                f"Check {node}->{neighbor} "
                f"cost {weight}"
            )

            if nd < self.dist[neighbor]:

                old = self.dist[neighbor]

                self.dist[neighbor] = nd

                self.prev[neighbor] = node

                heapq.heappush(
                    self.pq,
                    (nd, neighbor)
                )

                if old == float("inf"):
                    old_text = "∞"
                else:
                    old_text = str(old)

                log(
                    f"Update {neighbor}: "
                    f"{old_text} -> {nd}"
                )

    def shortest_path(self):

        path = []

        cur = self.target

        if cur not in self.prev and cur != self.start:
            return []

        while cur in self.prev:

            path.append(cur)

            cur = self.prev[cur]

        path.append(self.start)

        path.reverse()

        return path


# =====================================================
# UI
# =====================================================

textbox_rect = pygame.Rect(
    20,
    HEIGHT - 60,
    100,
    40
)

button_rect = pygame.Rect(
    140,
    HEIGHT - 60,
    200,
    40
)

node_input = "8"
input_active = False


def draw_graph(graph, positions, anim):

    for node in graph:

        for neighbor, weight in graph[node]:

            start = positions[node]
            end = positions[neighbor]

            color = (90, 90, 90)

            if anim.current_edge == (node, neighbor):
                color = (0, 255, 255)

            pygame.draw.line(
                screen,
                color,
                start,
                end,
                3
            )

            mx = (start[0] + end[0]) // 2
            my = (start[1] + end[1]) // 2

            txt = SMALL_FONT.render(
                str(weight),
                True,
                (255, 255, 255)
            )

            screen.blit(txt, (mx, my))

    for node, pos in positions.items():

        color = (70, 70, 70)

        if node in anim.visited:
            color = (0, 180, 0)

        if node == anim.current:
            color = (0, 120, 255)

        pygame.draw.circle(
            screen,
            color,
            pos,
            30
        )

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            pos,
            30,
            2
        )

        txt = FONT.render(
            node,
            True,
            (255, 255, 255)
        )

        screen.blit(
            txt,
            (
                pos[0] - 8,
                pos[1] - 12
            )
        )

        d = anim.dist[node]

        label = "∞"

        if d != float("inf"):
            label = str(d)

        dtxt = SMALL_FONT.render(
            label,
            True,
            (255, 255, 0)
        )

        screen.blit(
            dtxt,
            (
                pos[0] - 10,
                pos[1] - 55
            )
        )


def draw_final_path(anim, positions):

    path = anim.shortest_path()

    if len(path) < 2:
        return

    for i in range(len(path) - 1):

        a = positions[path[i]]
        b = positions[path[i + 1]]

        pygame.draw.line(
            screen,
            (255, 215, 0),
            a,
            b,
            10
        )


def draw_log_panel():

    pygame.draw.rect(
        screen,
        (25, 25, 35),
        (GRAPH_WIDTH, 0, LOG_WIDTH, HEIGHT)
    )

    title = FONT.render(
        "Navigation Log",
        True,
        (255, 255, 255)
    )

    screen.blit(
        title,
        (GRAPH_WIDTH + 20, 20)
    )

    y = 70

    visible = event_log[-35:]

    for line in visible:

        txt = SMALL_FONT.render(
            line,
            True,
            (220, 220, 220)
        )

        screen.blit(
            txt,
            (GRAPH_WIDTH + 10, y)
        )

        y += 22


def draw_controls():

    pygame.draw.rect(
        screen,
        (60, 60, 60),
        textbox_rect
    )

    pygame.draw.rect(
        screen,
        (120, 120, 120),
        button_rect
    )

    txt = FONT.render(
        node_input,
        True,
        (255, 255, 255)
    )

    screen.blit(
        txt,
        (
            textbox_rect.x + 10,
            textbox_rect.y + 8
        )
    )

    btn = SMALL_FONT.render(
        "Generate Graph",
        True,
        (255, 255, 255)
    )

    screen.blit(
        btn,
        (
            button_rect.x + 25,
            button_rect.y + 10
        )
    )

    info = SMALL_FONT.render(
        "SPACE=Step  ENTER=Auto  R=Restart  ESC=Exit",
        True,
        (255, 255, 255)
    )

    screen.blit(
        info,
        (380, HEIGHT - 48)
    )


# =====================================================
# INITIAL GRAPH
# =====================================================

graph, positions = generate_graph(8)

start_node = list(graph.keys())[0]
target_node = list(graph.keys())[-1]

anim = DijkstraAnimator(
    graph,
    start_node,
    target_node
)

auto_run = False

STEP_EVENT = pygame.USEREVENT + 1

pygame.time.set_timer(
    STEP_EVENT,
    600
)

# =====================================================
# MAIN LOOP
# =====================================================

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                anim.step()

            elif event.key == pygame.K_RETURN:
                auto_run = not auto_run

            elif event.key == pygame.K_r:

                event_log.clear()

                anim = DijkstraAnimator(
                    graph,
                    start_node,
                    target_node
                )

            elif input_active:

                if event.key == pygame.K_BACKSPACE:
                    node_input = node_input[:-1]

                elif event.unicode.isdigit():

                    if len(node_input) < 3:
                        node_input += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN:

            if textbox_rect.collidepoint(event.pos):
                input_active = True

            else:
                input_active = False

            if button_rect.collidepoint(event.pos):

                count = max(
                    2,
                    int(node_input or "2")
                )

                graph, positions = generate_graph(count)

                start_node = list(graph.keys())[0]
                target_node = list(graph.keys())[-1]

                event_log.clear()

                anim = DijkstraAnimator(
                    graph,
                    start_node,
                    target_node
                )

        elif event.type == STEP_EVENT:

            if auto_run and not anim.finished:
                anim.step()

    screen.fill(BG)

    if anim.finished:
        draw_final_path(
            anim,
            positions
        )

    draw_graph(
        graph,
        positions,
        anim
    )

    draw_log_panel()

    draw_controls()

    pygame.display.flip()

    clock.tick(60)

pygame.quit()