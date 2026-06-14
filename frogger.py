# ASCII Frogger Deluxe Arcade Edition
# Fixed: Safe zone movement and River/Log collision logic

import pygame, random
pygame.init()

W,H=1100,760
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("ASCII Frogger Deluxe Arcade")
clock=pygame.time.Clock()

FONT=pygame.font.SysFont("consolas",22,True)
BIG=pygame.font.SysFont("consolas",36,True)

BLACK=(0,0,0); GREEN=(0,255,0); RED=(255,80,80)
BLUE=(100,160,255); YELLOW=(255,220,0); WHITE=(220,220,220)

PW=42
GOAL=0
RIVER=[1,2,3,4]
SAFE=[5]        
ROAD=[6,7,8,9]  
START=10        

class Frog:
    def __init__(self): self.reset(); self.b=0; self.v=True
    def reset(self): self.x=PW//2; self.y=START
    def update(self,dt):
        self.b+=dt
        if self.b>250: self.v=not self.v; self.b=0

class Obj:
    def __init__(self,r,x,d): self.r=r; self.x=x; self.d=d
    def move(self):
        self.x+=self.d
        if self.d>0 and self.x>PW: self.x=-3
        if self.d<0 and self.x<-3: self.x=PW

class Game:
    def __init__(self):
        self.level=1; self.score=0; self.lives=3
        self.timer=60; self.paused=False
        self.win=False; self.over=False
        self.title=True

        self.frog=Frog()
        self.cross=False

        self.goals=[False]*5
        self.goal_pos=[2,10,18,26,34]
        self.fly=random.randint(0,4)

        self.tick=0
        self.slow_rate=8

        self.cars=[]
        for r in ROAD:
            for x in (4, 22):
                self.cars.append(Obj(r,x,random.choice([-1,1])))

        self.logs=[]
        for r in RIVER:
            # Stagger logs across lanes cleanly
            for x in (2, 16, 30):
                self.logs.append(Obj(r,x,random.choice([-1,1])))

    def reset_frog(self):
        self.cross=False
        self.frog.reset()

    def lose(self):
        self.lives-=1
        self.reset_frog()
        if self.lives<=0: self.over=True

    def move(self,dx,dy):
        self.frog.x=max(0,min(PW-3,self.frog.x+dx))
        self.frog.y=max(0,min(START,self.frog.y+dy))

    def put(self,a,t,p):
        for i,c in enumerate(t):
            if 0<=p+i<len(a): a[p+i]=c

    def update(self,dt):
        self.frog.update(dt)
        if self.paused or self.over or self.win or self.title: return

        self.timer-=dt/1000
        if self.timer<=0:
            self.lose()
            self.timer=60

        # Move logs and cars
        move_tick = False
        self.tick+=1
        if self.tick>=self.slow_rate:
            self.tick=0
            move_tick = True
            for c in self.cars: c.move()
            for l in self.logs: l.move()

        if self.frog.y in SAFE and not self.cross:
            self.cross=True
            self.score+=50

        # Check car collisions
        for c in self.cars:
            if self.frog.y==c.r and c.x-1<=self.frog.x<=c.x+1:
                self.lose(); return

        # Check river/log collisions
        if self.frog.y in RIVER:
            on=False
            for l in self.logs:
                # Fixed: Expanded hitbox match slightly to allow safe landing adjustments
                if l.r==self.frog.y and l.x-2 <= self.frog.x <= l.x+2:
                    on=True
                    # Carry the frog along with the log's movement step
                    if move_tick:
                        self.frog.x=max(0,min(PW-3,self.frog.x+l.d))
                    break
            if not on:
                self.lose(); return

        # Check goal reaches
        if self.frog.y==GOAL:
            idx=min(range(5), key=lambda i:abs(self.frog.x-(self.goal_pos[i]+1)))
            if not self.goals[idx]:
                self.score+=100
                if idx==self.fly:
                    self.score+=250
                self.goals[idx]=True

            self.timer=60
            self.reset_frog()

            if all(self.goals):
                self.level+=1
                self.score+=1000
                self.goals=[False]*5
                self.fly=random.randint(0,4)
                self.slow_rate=max(3,self.slow_rate-1)

    def draw(self):
        screen.fill(BLACK)

        if self.title:
            screen.blit(BIG.render("ASCII FROGGER DELUXE",True,GREEN),(250,180))
            screen.blit(FONT.render("Press SPACE to Start",True,YELLOW),(380,300))
            screen.blit(FONT.render("P Pause   ESC Exit",True,WHITE),(400,350))
            pygame.display.flip()
            return

        rows=[]
        rows.append(f"SCORE {self.score:05d}  LIVES {self.lives}  LEVEL {self.level}  TIME {int(self.timer):02d}")
        rows.append("="*PW)

        # 0: GOAL Row
        g=[" "]*PW
        for i,p in enumerate(self.goal_pos):
            self.put(g,"[*]" if i==self.fly and not self.goals[i] else ("[F]" if self.goals[i] else "[ ]"),p)
        rows.append("".join(g))

        # 1, 2, 3, 4: RIVER Rows
        for r in RIVER:
            line=["~"]*PW
            for l in self.logs:
                if l.r==r:self.put(line,"OOO",l.x)
            if self.frog.y==r and self.frog.v:self.put(line,"<@>",self.frog.x)
            rows.append("".join(line))

        # 5: SAFE Row
        for safe_row in SAFE:
            line = ["="] * PW
            if self.frog.y == safe_row and self.frog.v:
                self.put(line, "<@>", self.frog.x)
            rows.append("".join(line))
        
        # 6, 7, 8, 9: ROAD Rows
        for r in ROAD:
            line=["."]*PW
            for c in self.cars:
                if c.r==r:self.put(line,"CAR",c.x)
            if self.frog.y==r and self.frog.v:self.put(line,"<@>",self.frog.x)
            rows.append("".join(line))

        # 10: START Row
        s=["."]*PW
        if self.frog.y==START and self.frog.v:self.put(s,"<@>",self.frog.x)
        rows.append("".join(s))
        
        rows.append("="*PW)
        rows.append("ARROWS/WASD MOVE  P PAUSE  ESC EXIT")

        y=15
        for row in rows:
            x=10
            for ch in row:
                col=WHITE
                if ch in "<@>=": col=GREEN
                elif ch=="~": col=BLUE
                elif ch in "O[]#*": col=YELLOW
                elif ch in "CAR": col=RED
                screen.blit(FONT.render(ch,True,col),(x,y))
                x+=14
            y+=28

        if self.paused:
            screen.blit(BIG.render("PAUSED",True,YELLOW),(430,690))
        if self.over:
            screen.blit(BIG.render("GAME OVER - R",True,RED),(320,690))

        pygame.display.flip()

g=Game()
run=True

while run:
    dt=clock.tick(60)

    for e in pygame.event.get():
        if e.type==pygame.QUIT: run=False
        if e.type==pygame.KEYDOWN:
            if e.key==pygame.K_ESCAPE: run=False
            elif g.title and e.key==pygame.K_SPACE: g.title=False
            elif e.key==pygame.K_p: g.paused=not g.paused
            elif e.key==pygame.K_r and g.over: g=Game()
            elif not(g.paused or g.title or g.over):
                if e.key in (pygame.K_LEFT,pygame.K_a): g.move(-1,0)
                if e.key in (pygame.K_RIGHT,pygame.K_d): g.move(1,0)
                if e.key in (pygame.K_UP,pygame.K_w): g.move(0,-1)
                if e.key in (pygame.K_DOWN,pygame.K_s): g.move(0,1)

    g.update(dt)
    g.draw()

pygame.quit()