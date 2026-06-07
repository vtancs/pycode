
"""
Advanced Dijkstra Tutor
Features:
- Animated Dijkstra
- Explanation panel
- Priority Queue panel
- Distance table
- Scrollable log
- Quiz prompt (predict next node)
- Mouse wheel log scroll
- Auto run / step mode
- Node count generation
"""
import pygame, heapq, random, math

pygame.init()

W,H=1800,950
GRAPH_W=1050
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("Advanced Dijkstra Tutor")

FONT=pygame.font.SysFont("consolas",22)
SMALL=pygame.font.SysFont("consolas",18)
clock=pygame.time.Clock()

logs=[]
scroll=0
VISIBLE=24

def add_log(msg):
    global scroll
    logs.append(msg)
    scroll=max(0,len(logs)-VISIBLE)

def make_graph(n):
    labels=[chr(65+i) if i<26 else f"N{i}" for i in range(n)]
    g={x:[] for x in labels}
    pos={}
    cx,cy=GRAPH_W//2,H//2
    r=min(GRAPH_W,H)//3
    for i,node in enumerate(labels):
        a=2*math.pi*i/n
        pos[node]=(int(cx+r*math.cos(a)),int(cy+r*math.sin(a)))
    for i in range(n-1):
        g[labels[i]].append((labels[i+1],random.randint(1,9)))
    for node in labels:
        for _ in range(random.randint(2,5)):
            t=random.choice(labels)
            if t!=node:
                g[node].append((t,random.randint(1,15)))
    return g,pos

class DijkstraTutor:
    def __init__(self,g,s,t):
        self.g=g; self.s=s; self.t=t
        self.dist={k:float("inf") for k in g}
        self.dist[s]=0
        self.prev={}
        self.vis=set()
        self.pq=[(0,s)]
        self.current=None
        self.edge=None
        self.finished=False
        self.explain="Press SPACE."
        add_log(f"Start at {s}")

    def next_prediction(self):
        items=[(d,n) for d,n in self.pq if n not in self.vis]
        if not items: return None
        return min(items)[1]

    def step(self):
        if self.finished: return
        while self.pq:
            d,node=heapq.heappop(self.pq)
            if node not in self.vis: break
        else:
            self.finished=True; return

        self.current=node
        self.vis.add(node)

        self.explain=f"Selected {node}\nReason: smallest tentative distance ({d})"
        add_log(f"Visit {node} ({d})")

        if node==self.t:
            self.finished=True
            add_log("Target reached")
            return

        for nb,w in self.g[node]:
            self.edge=(node,nb)
            nd=d+w
            if nd<self.dist[nb]:
                old=self.dist[nb]
                self.dist[nb]=nd
                self.prev[nb]=node
                heapq.heappush(self.pq,(nd,nb))
                add_log(f"{node}->{nb}: {old} -> {nd}")
                self.explain=(
                    f"Relax edge {node}->{nb}\n"
                    f"New distance={nd}\n"
                    f"Update because shorter."
                )

    def path(self):
        if self.t not in self.prev and self.t!=self.s: return []
        cur=self.t; p=[cur]
        while cur in self.prev:
            cur=self.prev[cur]; p.append(cur)
        return p[::-1]

graph,pos=make_graph(10)
algo=DijkstraTutor(graph,list(graph)[0],list(graph)[-1])

auto=False
node_count="10"

inp=pygame.Rect(20,H-55,100,35)
btn=pygame.Rect(130,H-55,180,35)

STEP=pygame.USEREVENT+1
pygame.time.set_timer(STEP,500)

running=True
while running:
    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False
        elif e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE: running=False
            elif e.key==pygame.K_SPACE: algo.step()
            elif e.key==pygame.K_RETURN: auto=not auto
            elif e.key==pygame.K_BACKSPACE: node_count=node_count[:-1]
            elif e.unicode.isdigit(): node_count+=e.unicode
        elif e.type==pygame.MOUSEBUTTONDOWN:
            if btn.collidepoint(e.pos):
                n=max(2,int(node_count or "2"))
                logs.clear()
                graph,pos=make_graph(n)
                algo=DijkstraTutor(graph,list(graph)[0],list(graph)[-1])
        elif e.type==pygame.MOUSEWHEEL:
            scroll=max(0,min(max(0,len(logs)-VISIBLE),scroll-e.y))
        elif e.type==STEP and auto and not algo.finished:
            algo.step()

    screen.fill((18,18,24))

    p=algo.path() if algo.finished else []
    for i in range(len(p)-1):
        pygame.draw.line(screen,(255,215,0),pos[p[i]],pos[p[i+1]],8)

    for n,edges in graph.items():
        for t,w in edges:
            col=(90,90,90)
            if algo.edge==(n,t): col=(0,255,255)
            pygame.draw.line(screen,col,pos[n],pos[t],2)

    for n,xy in pos.items():
        col=(80,80,80)
        if n in algo.vis: col=(0,180,0)
        if n==algo.current: col=(0,120,255)
        pygame.draw.circle(screen,col,xy,24)
        pygame.draw.circle(screen,(255,255,255),xy,24,2)
        screen.blit(SMALL.render(n,True,(255,255,255)),(xy[0]-8,xy[1]-8))

    pygame.draw.rect(screen,(30,30,40),(GRAPH_W,0,W-GRAPH_W,H))

    x=GRAPH_W+15
    y=15

    screen.blit(FONT.render("Explanation",True,(255,255,255)),(x,y)); y+=35
    for line in algo.explain.splitlines():
        screen.blit(SMALL.render(line,True,(220,220,220)),(x,y)); y+=22

    y+=10
    pred=algo.next_prediction()
    screen.blit(FONT.render("Quiz",True,(255,255,0)),(x,y)); y+=28
    q=f"Which node is next? Suggested answer: {pred}"
    screen.blit(SMALL.render(q,True,(255,255,255)),(x,y)); y+=35

    screen.blit(FONT.render("Priority Queue",True,(255,255,255)),(x,y)); y+=25
    for item in sorted(algo.pq)[:8]:
        screen.blit(SMALL.render(str(item),True,(200,255,200)),(x,y)); y+=20

    y+=10
    screen.blit(FONT.render("Distance Table",True,(255,255,255)),(x,y)); y+=25
    for n in list(graph.keys())[:12]:
        d=algo.dist[n]
        d="∞" if d==float("inf") else str(d)
        prev=algo.prev.get(n,"-")
        screen.blit(SMALL.render(f"{n:>2}  {d:<4} prev:{prev}",True,(220,220,220)),(x,y)); y+=18

    y+=10
    screen.blit(FONT.render("Navigation Log",True,(255,255,0)),(x,y)); y+=25
    for line in logs[scroll:scroll+VISIBLE]:
        screen.blit(SMALL.render(line,True,(220,220,220)),(x,y)); y+=18

    pygame.draw.rect(screen,(60,60,60),inp)
    pygame.draw.rect(screen,(100,100,130),btn)
    screen.blit(FONT.render(node_count,True,(255,255,255)),(inp.x+5,inp.y+4))
    screen.blit(SMALL.render("Generate Graph",True,(255,255,255)),(btn.x+20,btn.y+8))

    screen.blit(SMALL.render("SPACE Step | ENTER Auto | MouseWheel Scroll | ESC Exit",True,(255,255,255)),(340,H-45))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
