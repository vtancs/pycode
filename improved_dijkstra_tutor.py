
# Improved Dijkstra Tutor (full app)
# Fixes:
# - Dynamic log area
# - Auto-follow log
# - Mouse-wheel scrolling
# - Reserved bottom control area
# - Scroll bar
# - Better node placement for large graphs

import pygame, heapq, random, math

pygame.init()

W,H = 1800,950
GRAPH_W = 1150
SIDE_X = GRAPH_W + 10
BOTTOM_BAR = 80

screen = pygame.display.set_mode((W,H))
pygame.display.set_caption("Improved Dijkstra Tutor")

FONT = pygame.font.SysFont("consolas",22)
SMALL = pygame.font.SysFont("consolas",18)
clock = pygame.time.Clock()

logs=[]
scroll=0
auto_follow=True

def add_log(msg):
    global scroll
    logs.append(msg)
    if auto_follow:
        scroll=max(0,len(logs)-1)

def generate_graph(n):
    labels=[chr(65+i) if i<26 else f"N{i}" for i in range(n)]
    g={k:[] for k in labels}

    cols=max(4,int(math.sqrt(n)))
    spacing_x=900/max(cols,1)
    rows=math.ceil(n/cols)
    spacing_y=700/max(rows,1)

    pos={}
    for i,node in enumerate(labels):
        c=i%cols
        r=i//cols
        x=100+c*spacing_x+random.randint(-20,20)
        y=80+r*spacing_y+random.randint(-20,20)
        pos[node]=(int(x),int(y))

    for i in range(n-1):
        g[labels[i]].append((labels[i+1],random.randint(1,9)))

    for node in labels:
        for _ in range(random.randint(2,4)):
            t=random.choice(labels)
            if t!=node:
                g[node].append((t,random.randint(1,15)))
    return g,pos

class Dijkstra:
    def __init__(self,g,s,t):
        self.g=g; self.s=s; self.t=t
        self.dist={n:float("inf") for n in g}
        self.dist[s]=0
        self.prev={}
        self.vis=set()
        self.pq=[(0,s)]
        self.current=None
        self.edge=None
        self.finished=False
        self.explain="Press SPACE to step."
        add_log(f"Start at {s}")

    def step(self):
        if self.finished:return
        while self.pq:
            d,n=heapq.heappop(self.pq)
            if n not in self.vis: break
        else:
            self.finished=True; return

        self.current=n
        self.vis.add(n)

        self.explain=f"Selected {n}\nReason: smallest tentative distance ({d})"
        add_log(f"Visit {n} ({d})")

        if n==self.t:
            self.finished=True
            add_log("Target reached")
            return

        for nb,w in self.g[n]:
            nd=d+w
            self.edge=(n,nb)
            if nd<self.dist[nb]:
                old=self.dist[nb]
                self.dist[nb]=nd
                self.prev[nb]=n
                heapq.heappush(self.pq,(nd,nb))
                add_log(f"{n}->{nb}: {old} -> {nd}")

    def path(self):
        if self.t not in self.prev and self.t!=self.s:
            return []
        cur=self.t
        p=[cur]
        while cur in self.prev:
            cur=self.prev[cur]
            p.append(cur)
        return p[::-1]

graph,pos=generate_graph(20)
algo=Dijkstra(graph,list(graph)[0],list(graph)[-1])

node_count="20"
inp=pygame.Rect(20,H-60,100,35)
btn=pygame.Rect(130,H-60,180,35)

auto=False
STEP=pygame.USEREVENT+1
pygame.time.set_timer(STEP,500)

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False
        elif e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE:
                running=False
            elif e.key==pygame.K_SPACE:
                algo.step()
            elif e.key==pygame.K_RETURN:
                auto=not auto
            elif e.key==pygame.K_HOME:
                auto_follow=False
                scroll=0
            elif e.key==pygame.K_END:
                auto_follow=True
                scroll=max(0,len(logs)-1)
            elif e.key==pygame.K_BACKSPACE:
                node_count=node_count[:-1]
            elif e.unicode.isdigit():
                node_count+=e.unicode
        elif e.type==pygame.MOUSEBUTTONDOWN:
            if btn.collidepoint(e.pos):
                logs.clear()
                n=max(2,int(node_count or "2"))
                graph,pos=generate_graph(n)
                algo=Dijkstra(graph,list(graph)[0],list(graph)[-1])
        elif e.type==pygame.MOUSEWHEEL:
            auto_follow=False
            scroll=max(0,scroll-e.y)
        elif e.type==STEP and auto and not algo.finished:
            algo.step()

    screen.fill((18,18,24))

    path=algo.path() if algo.finished else []
    for i in range(len(path)-1):
        pygame.draw.line(screen,(255,215,0),pos[path[i]],pos[path[i+1]],6)

    for a,edges in graph.items():
        for b,w in edges:
            color=(90,90,90)
            if algo.edge==(a,b):
                color=(0,255,255)
            pygame.draw.line(screen,color,pos[a],pos[b],1)

    for n,p in pos.items():
        col=(80,80,80)
        if n in algo.vis: col=(0,180,0)
        if n==algo.current: col=(0,120,255)
        pygame.draw.circle(screen,col,p,18)
        pygame.draw.circle(screen,(255,255,255),p,18,1)
        screen.blit(SMALL.render(n,True,(255,255,255)),(p[0]-10,p[1]-8))

    pygame.draw.rect(screen,(30,30,40),(GRAPH_W,0,W-GRAPH_W,H))

    x=SIDE_X
    y=15

    screen.blit(FONT.render("Explanation",True,(255,255,255)),(x,y))
    y+=35

    for line in algo.explain.splitlines():
        screen.blit(SMALL.render(line,True,(220,220,220)),(x,y))
        y+=22

    y+=10
    screen.blit(FONT.render("Priority Queue",True,(255,255,0)),(x,y))
    y+=25

    for item in sorted(algo.pq)[:8]:
        screen.blit(SMALL.render(str(item),True,(220,255,220)),(x,y))
        y+=18

    y+=10
    screen.blit(FONT.render("Navigation Log",True,(255,255,0)),(x,y))
    y+=25

    log_top=y
    log_bottom=H-BOTTOM_BAR-10
    line_h=18
    visible=max(1,(log_bottom-log_top)//line_h)

    max_scroll=max(0,len(logs)-visible)
    if auto_follow:
        scroll=max_scroll
    scroll=min(scroll,max_scroll)

    for line in logs[scroll:scroll+visible]:
        if y>log_bottom:
            break
        screen.blit(SMALL.render(line,True,(220,220,220)),(x,y))
        y+=line_h

    track_x=W-18
    track_y=log_top
    track_h=log_bottom-log_top

    pygame.draw.rect(screen,(70,70,70),(track_x,track_y,8,track_h))

    if len(logs)>0:
        thumb_h=max(30,int(track_h*(visible/max(len(logs),visible))))
        thumb_y=track_y
        if max_scroll>0:
            thumb_y=track_y+int((track_h-thumb_h)*(scroll/max_scroll))
        pygame.draw.rect(screen,(180,180,180),(track_x,thumb_y,8,thumb_h))

    pygame.draw.rect(screen,(60,60,60),inp)
    pygame.draw.rect(screen,(100,100,140),btn)

    screen.blit(FONT.render(node_count,True,(255,255,255)),(inp.x+5,inp.y+5))
    screen.blit(SMALL.render("Generate Graph",True,(255,255,255)),(btn.x+20,btn.y+8))

    screen.blit(
        SMALL.render("SPACE Step | ENTER Auto | MouseWheel Scroll | HOME Top | END Follow | ESC Exit",True,(255,255,255)),
        (340,H-48)
    )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
