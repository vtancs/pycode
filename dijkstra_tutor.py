
import pygame, heapq, random, math

pygame.init()

WIDTH, HEIGHT = 1600, 900
GRAPH_WIDTH = 1000
LOG_X = GRAPH_WIDTH + 10

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dijkstra Tutor")

FONT = pygame.font.SysFont("consolas", 22)
SMALL = pygame.font.SysFont("consolas", 18)
clock = pygame.time.Clock()

event_log = []
log_scroll = 0
LINES_VISIBLE = 32
follow_log = True

def log(msg):
    global log_scroll
    event_log.append(msg)
    if follow_log:
        log_scroll = max(0, len(event_log) - LINES_VISIBLE)

def generate_graph(n):
    labels = [chr(65+i) if i < 26 else f"N{i}" for i in range(n)]
    graph = {k: [] for k in labels}
    pos = {}
    cx, cy = GRAPH_WIDTH//2, HEIGHT//2 - 50
    radius = min(GRAPH_WIDTH, HEIGHT)//3

    for i, node in enumerate(labels):
        ang = 2*math.pi*i/max(1,n)
        pos[node] = (
            int(cx + radius*math.cos(ang)),
            int(cy + radius*math.sin(ang))
        )

    for i in range(n-1):
        graph[labels[i]].append((labels[i+1], random.randint(1, 9)))

    for node in labels:
        for _ in range(random.randint(2,4)):
            t = random.choice(labels)
            if t != node:
                graph[node].append((t, random.randint(1,15)))
    return graph, pos

class TutorDijkstra:
    def __init__(self, graph, start, target):
        self.graph = graph
        self.start = start
        self.target = target
        self.dist = {n: float("inf") for n in graph}
        self.dist[start] = 0
        self.prev = {}
        self.visited = set()
        self.pq = [(0,start)]
        self.current = None
        self.current_edge = None
        self.finished = False
        self.explanation = "Press SPACE for next step."
        log(f"Start node = {start}")

    def step(self):
        if self.finished:
            return

        while self.pq:
            d,node = heapq.heappop(self.pq)
            if node not in self.visited:
                break
        else:
            self.finished = True
            return

        self.current = node
        self.visited.add(node)

        self.explanation = (
            f"Visit {node}\n"
            f"Reason: smallest tentative distance = {d}."
        )
        log(f"Visit {node} distance={d}")

        if node == self.target:
            self.finished = True
            log("Target reached.")
            return

        for neigh,w in self.graph[node]:
            nd = d+w
            old = self.dist[neigh]
            self.current_edge = (node, neigh)

            log(f"Check {node}->{neigh} weight={w}")
            log(f"Candidate distance = {d}+{w}={nd}")

            if nd < old:
                self.dist[neigh] = nd
                self.prev[neigh] = node
                heapq.heappush(self.pq,(nd,neigh))

                self.explanation = (
                    f"Relax {node}->{neigh}\n"
                    f"{nd} < {old if old != float('inf') else '∞'}\n"
                    f"Update distance of {neigh}."
                )
                log(f"Update {neigh}: {old} -> {nd}")

    def path(self):
        if self.target not in self.prev and self.target != self.start:
            return []
        cur = self.target
        p = [cur]
        while cur in self.prev:
            cur = self.prev[cur]
            p.append(cur)
        return p[::-1]

graph, positions = generate_graph(8)
anim = TutorDijkstra(graph, list(graph)[0], list(graph)[-1])

node_text = "8"
input_active = False

box = pygame.Rect(20, HEIGHT-55, 100, 35)
btn = pygame.Rect(130, HEIGHT-55, 170, 35)

auto = False
STEP = pygame.USEREVENT+1
pygame.time.set_timer(STEP, 700)

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            elif e.key == pygame.K_SPACE:
                anim.step()
            elif e.key == pygame.K_RETURN:
                auto = not auto
            elif e.key == pygame.K_PAGEUP:
                globals()['log_scroll'] = max(0, log_scroll-10)
            elif e.key == pygame.K_PAGEDOWN:
                globals()['log_scroll'] = min(max(0,len(event_log)-LINES_VISIBLE), log_scroll+10)
            elif input_active:
                if e.key == pygame.K_BACKSPACE:
                    node_text = node_text[:-1]
                elif e.unicode.isdigit():
                    node_text += e.unicode

        elif e.type == pygame.MOUSEBUTTONDOWN:
            if box.collidepoint(e.pos):
                input_active = True
            else:
                input_active = False

            if btn.collidepoint(e.pos):
                count = max(2, int(node_text or "2"))
                event_log.clear()
                graph, positions = generate_graph(count)
                anim = TutorDijkstra(graph, list(graph)[0], list(graph)[-1])

        elif e.type == pygame.MOUSEWHEEL:
            follow_log = False
            log_scroll = max(0, min(max(0,len(event_log)-LINES_VISIBLE), log_scroll - e.y))

        elif e.type == STEP and auto and not anim.finished:
            anim.step()

    screen.fill((18,18,24))

    if anim.finished:
        p = anim.path()
        for i in range(len(p)-1):
            pygame.draw.line(screen,(255,215,0),positions[p[i]],positions[p[i+1]],8)

    for n, edges in graph.items():
        for t,w in edges:
            col = (90,90,90)
            if anim.current_edge == (n,t):
                col = (0,255,255)
            pygame.draw.line(screen,col,positions[n],positions[t],2)

    for n,p in positions.items():
        col=(80,80,80)
        if n in anim.visited: col=(0,180,0)
        if n==anim.current: col=(0,120,255)
        pygame.draw.circle(screen,col,p,26)
        pygame.draw.circle(screen,(255,255,255),p,26,2)
        screen.blit(FONT.render(n,True,(255,255,255)),(p[0]-8,p[1]-10))

    pygame.draw.rect(screen,(30,30,40),(GRAPH_WIDTH,0,WIDTH-GRAPH_WIDTH,HEIGHT))

    y=15
    screen.blit(FONT.render("Explanation",True,(255,255,255)),(LOG_X,y))
    y += 35
    for line in anim.explanation.split("\n"):
        screen.blit(SMALL.render(line,True,(220,220,220)),(LOG_X,y))
        y += 24

    y += 20
    screen.blit(FONT.render("Navigation Log",True,(255,255,0)),(LOG_X,y))
    y += 30

    start = max(0, log_scroll)
    end = min(len(event_log), start+LINES_VISIBLE)
    for line in event_log[start:end]:
        screen.blit(SMALL.render(line,True,(220,220,220)),(LOG_X,y))
        y += 20

    pygame.draw.rect(screen,(60,60,60),box)
    pygame.draw.rect(screen,(90,90,120),btn)
    screen.blit(FONT.render(node_text,True,(255,255,255)),(box.x+5,box.y+5))
    screen.blit(SMALL.render("Generate Graph",True,(255,255,255)),(btn.x+20,btn.y+8))

    screen.blit(
        SMALL.render("SPACE=Step  ENTER=Auto  MouseWheel=Scroll Log  ESC=Exit",True,(255,255,255)),
        (320, HEIGHT-48)
    )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
