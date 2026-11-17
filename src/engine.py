import json,os,sys,urllib.request as U
# Board: 10x12 mailbox, a8=21 .. h1=98, pieces +1..+6 white P N B R Q K, negative black, 9 off board.
V=(0,100,320,330,500,900,0)
KN=(-21,-19,-12,-8,8,12,19,21)
KG=(-11,-10,-9,-1,1,9,10,11)
RK=(-10,-1,1,10)
BS=(-11,-9,9,11)
CM={95:12,91:13,98:14,25:3,21:7,28:11}
MATE=90000
BUD=int(os.environ.get('NODES',60000))
class Stop(Exception):pass
def sq(n):return 21+(8-int(n[1]))*10+ord(n[0])-97
def nm(s):return chr(96+s%10)+str(10-s//10)
def parse(f):
 p,s,c,e=f.split()[:4]
 b=[9]*120
 for i in range(8):
  for j in range(8):b[21+i*10+j]=0
 i=0
 for ch in p:
  if ch=='/':pass
  elif ch.isdigit():i+=int(ch)
  else:
   b[21+i//8*10+i%8]=('PNBRQK'.find(ch.upper())+1)*(1 if ch.isupper() else -1)
   i+=1
 r=sum(m for ch,m in zip('KQkq',(1,2,4,8)) if ch in c)
 return(b,1 if s=='w' else -1,r,0 if e=='-' else sq(e))
def hit(b,t,s):
 # is square t attacked by side s
 d=-10*s
 if b[t-d-1]==s or b[t-d+1]==s:return 1
 for o in KN:
  if b[t+o]==2*s:return 1
 for o in KG:
  if b[t+o]==6*s:return 1
 for o in RK:
  u=t+o
  while b[u]==0:u+=o
  if b[u]==4*s or b[u]==5*s:return 1
 for o in BS:
  u=t+o
  while b[u]==0:u+=o
  if b[u]==3*s or b[u]==5*s:return 1
 return 0
def gen(st,caps=0):
 b,s,cr,ep=st
 out=[]
 for f in range(21,99):
  p=b[f]
  if p*s<=0 or p>6 or p<-6:continue
  a=abs(p)
  if a==1:
   d=-10*s
   t=f+d
   pr=1 if t//10 in(2,9) else 0
   if b[t]==0 and(not caps or pr):
    out.append((f,t,5 if pr else 0))
    if f//10==(8 if s>0 else 3)and b[t+d]==0 and not caps:out.append((f,t+d,0))
   for t in(f+d-1,f+d+1):
    if-7<b[t]*s<0:out.append((f,t,5 if pr else 0))
    elif t==ep and ep:out.append((f,t,0))
  else:
   for o in(KN if a==2 else KG if a==6 else RK if a==4 else BS if a==3 else KG):
    t=f+o
    while 1:
     x=b[t]
     if x==0:
      if not caps:out.append((f,t,0))
     elif-7<x*s<0:out.append((f,t,0))
     if x!=0 or a in(2,6):break
     t+=o
  if a==6 and not caps and cr and f==(95 if s>0 else 25):
   k=1 if s>0 else 4
   q=2 if s>0 else 8
   if cr&k and b[f+1]==0 and b[f+2]==0 and b[f+3]==4*s and not(hit(b,f,-s)or hit(b,f+1,-s)or hit(b,f+2,-s)):out.append((f,f+2,0))
   if cr&q and b[f-1]==0 and b[f-2]==0 and b[f-3]==0 and b[f-4]==4*s and not(hit(b,f,-s)or hit(b,f-1,-s)or hit(b,f-2,-s)):out.append((f,f-2,0))
 return out
def mk(st,m):
 b,s,cr,ep=st
 f,t,pr=m
 b=b[:]
 p=b[f]
 a=abs(p)
 n=0
 b[f]=0
 if a==1:
  if t==ep and(t-f)%10:b[t+10*s]=0
  if abs(t-f)==20:n=(f+t)//2
  if pr:p=s*pr
 elif a==6 and abs(t-f)==2:
  if t>f:b[t+1]=0;b[t-1]=4*s
  else:b[t-2]=0;b[t+1]=4*s
 b[t]=p
 return(b,-s,cr&CM.get(f,15)&CM.get(t,15),n)
# piece-square tables, white's view, indexed [piece][square]
P=[[0]*120 for _ in range(7)]
Q=[[0]*120 for _ in range(7)]
E=[0]*120
for r in range(8):
 for c in range(8):
  i=21+r*10+c
  k=7-r
  ce=(0,1,2,3,3,2,1,0)
  cc=ce[c]+ce[r]
  P[1][i]=max(0,k-1)*9+(ce[c]*4 if 2<k<6 else 0)
  P[2][i]=9*cc-(12 if c in(0,7)or k in(0,7)else 0)
  P[3][i]=5*cc-(8 if k==0 else 0)
  P[4][i]=(18 if k==6 else 0)+2*ce[c]
  P[5][i]=2*cc
  P[6][i]=-9*cc+(25 if k==0 and c in(1,2,6)else 0)
  E[i]=18*cc
for a in range(1,7):
 for r in range(8):
  for c in range(8):Q[a][21+r*10+c]=P[a][21+(7-r)*10+c]
def ev(b):
 x=0
 m=0
 for f in range(21,99):
  p=b[f]
  if p==0 or p>6 or p<-6:continue
  if p>0:
   x+=V[p]+P[p][f]
   if p>1:m+=V[p]
  else:
   x-=V[-p]+Q[-p][f]
   if p<-1:m+=V[-p]
 if m<2200:
  for f in range(21,99):
   if b[f]==6:x+=E[f]+9*9
   elif b[f]==-6:x-=E[f]+9*9
 return x
def order(b,ms,tm,H):
 def key(m):
  if m==tm:return-10**6
  v=b[m[1]]
  return-(abs(v)*10-abs(b[m[0]])+1000 if v else H.get((m[0],m[1]),0)-5000+(500 if m[2] else 0)) 
 ms.sort(key=key)
class Eng:
 def __init__(s,seen):
  s.n=0;s.T={};s.H={};s.seen=seen;s.lim=BUD*2
 def q(s,st,al,be):
  s.n+=1
  if s.n>s.lim:raise Stop
  b=st[0];c=st[1]
  x=c*ev(b)
  if x>=be:return x
  if x>al:al=x
  ms=gen(st,1)
  order(b,ms,None,s.H)
  for m in ms:
   if abs(b[m[1]])==6:return MATE
   y=-s.q(mk(st,m),-be,-al)
   if y>=be:return y
   if y>al:al=y
  return al
 def ab(s,st,d,al,be,ply,nu=1):
  s.n+=1
  if s.n>s.lim:raise Stop
  b,c,cr,ep=st
  k=(tuple(b),c,cr,ep)
  if ply and k in s.seen:return 0
  ck=hit(b,b.index(6*c),-c)
  if ck:d+=1
  if d<=0:return s.q(st,al,be)
  e=s.T.get(k)
  tm=None
  if e:
   tm=e[3]
   if e[0]>=d and ply:
    if e[1]==0 or(e[1]==1 and e[2]>=be)or(e[1]==2 and e[2]<=al):return e[2]
  if nu and d>2 and not ck and be<MATE-999 and sum(V[abs(p)]for p in b if 0<p*c<7)>1500:
   s.seen.add(k)
   y=-s.ab((b,-c,cr,0),d-3,-be,1-be,ply+1,0)
   s.seen.discard(k)
   if y>=be:return be
  ms=gen(st)
  order(b,ms,tm,s.H)
  best=-MATE-1
  a0=al
  bm=None
  for i,m in enumerate(ms):
   if abs(b[m[1]])==6:return MATE-ply
   s.seen.add(k)
   t=mk(st,m)
   if i>3 and d>2 and not b[m[1]]and not ck:
    y=-s.ab(t,d-2,-al-1,-al,ply+1)
    if y>al:y=-s.ab(t,d-1,-be,-al,ply+1)
   else:y=-s.ab(t,d-1,-be,-al,ply+1)
   s.seen.discard(k)
   if y>best:best=y;bm=m
   if y>al:al=y
   if al>=be:
    if not b[m[1]]:s.H[(m[0],m[1])]=s.H.get((m[0],m[1]),0)+d*d
    break
  if best<-MATE+999 and not ck:best=0
  s.T[k]=(d,0 if a0<best<be else 1 if best>=be else 2,best,bm)
  return best
 def go(s,st,legal):
  b=st[0]
  ms=[m for m in gen(st)if nm(m[0])+nm(m[1])+('' if not m[2]else'q')in legal]
  if not ms:return None
  bm=ms[0]
  for d in range(1,40):
   try:
    al=-MATE-1
    cur=None
    order(b,ms,bm,s.H)
    for m in ms:
     y=-s.ab(mk(st,m),d-1,-MATE-1,-al,1)
     if y>al:al=y;cur=m
    bm=cur
   except Stop:break
   if s.n>BUD or al>MATE-100:break
  return bm
def post(p,d):
 r=U.Request(os.environ['MAKEFUN_ENV_URL']+p,json.dumps(d).encode(),{'content-type':'application/json'})
 return json.load(U.urlopen(r))
g=post('/game',{})
seen=set()
gid=0
while g['status']!='done':
 if g['status']!='your_move':
  g=post('/game',{})
  continue
 st=parse(g['fen'])
 if g['game']!=gid:seen=set();gid=g['game']
 legal=set(g['legal_moves'])
 m=Eng(seen).go(st,legal)
 mv=nm(m[0])+nm(m[1])+('q'if m[2]else'')if m else g['legal_moves'][0]
 if mv not in legal:mv=g['legal_moves'][0]
 seen.add((tuple(st[0]),st[1],st[2],st[3]))
 g=post('/move',{'game':g['game'],'move':mv})
