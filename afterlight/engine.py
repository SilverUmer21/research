"""AFTERLIGHT rendering utilities: EGL/OpenGL, transforms and procedural geometry.
Requires Python, numpy, Pillow, Mesa EGL/OpenGL and ffmpeg. No web service.
"""
from __future__ import annotations
import os
os.environ.setdefault('EGL_PLATFORM', 'surfaceless')
os.environ.setdefault('LIBGL_ALWAYS_SOFTWARE', '1')
os.environ.setdefault('LP_NUM_THREADS', '8')
import argparse, ctypes as C, math, subprocess, time, wave, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent
FONT = str(ROOT / 'fonts/BarlowCondensed-Bold.ttf')
SANS = '/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf'
INK = '#37233d'; CREAM = '#f5dbbf'; ORANGE = '#ff963d'; TEAL = '#436e76'
COLORS = dict(cream=CREAM, orange=ORANGE, teal=TEAL, stone='#bc9aa6',
              road='#dea999', brass='#e9ab61', glass='#37233d', rubber='#30232b',
              shadow='#4e009c', white='#fff0ce', roof='#416f78', green='#9da345')

def color(c):
    c = COLORS.get(c, c)
    if isinstance(c, str): return tuple(int(c[i:i+2],16)/255 for i in (1,3,5))
    return tuple(c)
def clamp(v,a=0.,b=1.): return min(b,max(a,v))
def smooth(t): t=clamp(t); return t*t*(3-2*t)
def ease(t): t=clamp(t); return 1-(1-t)**3
def lerp(a,b,t): return np.array(a)*(1-t)+np.array(b)*t
def trans(x=0,y=0,z=0):
    m=np.eye(4,dtype=np.float32); m[:3,3]=(x,y,z); return m
def scale(x=1,y=None,z=None):
    return np.diag([x, x if y is None else y, x if z is None else z, 1]).astype(np.float32)
def rot(a,axis='z'):
    c,s=math.cos(a),math.sin(a)
    if axis=='x': m=[[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]
    elif axis=='y': m=[[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
    else: m=[[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]]
    return np.array(m,dtype=np.float32)
def normalize(a): a=np.array(a,dtype=np.float32); return a/max(np.linalg.norm(a),1e-9)
def linear(c):
    a=np.array(color(c),dtype=float)
    return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def lookat(eye,target,roll=0):
    eye=np.array(eye); f=normalize(np.array(target)-eye); s=normalize(np.cross(f,(0,1,0))); u=np.cross(s,f)
    m=np.eye(4,dtype=np.float32); m[0,:3]=s; m[1,:3]=u; m[2,:3]=-f; m[:3,3]=-m[:3,:3]@eye
    return rot(roll)@m
def perspective(fov,aspect,near=.15,far=180):
    f=1/math.tan(math.radians(fov)/2)
    return np.array([[f/aspect,0,0,0],[0,f,0,0],[0,0,(far+near)/(near-far),2*far*near/(near-far)],[0,0,-1,0]],np.float32)
def ortho(l,r,b,t,n,f):
    return np.array([[2/(r-l),0,0,-(r+l)/(r-l)],[0,2/(t-b),0,-(t+b)/(t-b)],[0,0,-2/(f-n),-(f+n)/(f-n)],[0,0,0,1]],np.float32)

class GL:
    def __init__(self,w,h):
        self.e=C.CDLL('libEGL.so.1'); self.g=C.CDLL('libGL.so.1'); self.w=w; self.h=h
        P=C.c_void_p; I=C.c_int; U=C.c_uint; F=C.c_float
        def bind(lib,name,ret,args):
            fn=getattr(lib,name); fn.restype=ret; fn.argtypes=args; return fn
        E=lambda n,r,a:bind(self.e,n,r,a)
        d=E('eglGetDisplay',P,[P])(None); ma,mi=I(),I()
        assert E('eglInitialize',I,[P,C.POINTER(I),C.POINTER(I)])(d,C.byref(ma),C.byref(mi))
        E('eglBindAPI',I,[U])(0x30A2)
        att=(I*13)(0x3033,1,0x3040,8,0x3024,8,0x3023,8,0x3022,8,0x3025,24,0x3038)
        cfg=P(); num=I(); E('eglChooseConfig',I,[P,C.POINTER(I),C.POINTER(P),I,C.POINTER(I)])(d,att,C.byref(cfg),1,C.byref(num))
        att2=(I*7)(0x3098,3,0x30FB,3,0x30FD,1,0x3038)
        ctx=E('eglCreateContext',P,[P,P,P,C.POINTER(I)])(d,cfg,None,att2)
        pa=(I*5)(0x3057,w,0x3056,h,0x3038)
        sf=E('eglCreatePbufferSurface',P,[P,P,C.POINTER(I)])(d,cfg,pa)
        assert E('eglMakeCurrent',I,[P,P,P,P])(d,sf,sf,ctx)
        self.keep=(d,ctx,sf)
        defs={
            'glGetString':(C.c_char_p,[U]), 'glGenVertexArrays':(None,[I,C.POINTER(U)]),
            'glBindVertexArray':(None,[U]), 'glGenBuffers':(None,[I,C.POINTER(U)]),
            'glBindBuffer':(None,[U,U]),'glBufferData':(None,[U,C.c_size_t,P,U]),
            'glVertexAttribPointer':(None,[U,I,U,C.c_ubyte,I,P]), 'glEnableVertexAttribArray':(None,[U]),
            'glCreateShader':(U,[U]), 'glShaderSource':(None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)]),
            'glCompileShader':(None,[U]),'glGetShaderiv':(None,[U,U,C.POINTER(I)]),
            'glGetShaderInfoLog':(None,[U,I,C.POINTER(I),C.c_char_p]),
            'glCreateProgram':(U,[]),'glAttachShader':(None,[U,U]),'glLinkProgram':(None,[U]),
            'glGetProgramiv':(None,[U,U,C.POINTER(I)]),'glGetProgramInfoLog':(None,[U,I,C.POINTER(I),C.c_char_p]),
            'glUseProgram':(None,[U]),'glGetUniformLocation':(I,[U,C.c_char_p]),
            'glUniformMatrix4fv':(None,[I,I,C.c_ubyte,C.POINTER(F)]),'glUniform1f':(None,[I,F]),
            'glUniform1i':(None,[I,I]),'glUniform2f':(None,[I,F,F]),'glUniform3f':(None,[I,F,F,F]),
            'glViewport':(None,[I,I,I,I]),'glEnable':(None,[U]),'glDisable':(None,[U]),
            'glClearColor':(None,[F,F,F,F]),'glClear':(None,[U]),'glDepthMask':(None,[C.c_ubyte]),
            'glDrawArrays':(None,[U,I,I]),'glReadPixels':(None,[I,I,I,I,U,U,P]),
            'glGenTextures':(None,[I,C.POINTER(U)]),'glBindTexture':(None,[U,U]),
            'glTexImage2D':(None,[U,I,I,I,I,I,U,U,P]),'glTexParameteri':(None,[U,U,I]),
            'glActiveTexture':(None,[U]),'glGenFramebuffers':(None,[I,C.POINTER(U)]),
            'glBindFramebuffer':(None,[U,U]),'glFramebufferTexture2D':(None,[U,U,U,U,I]),
            'glCheckFramebufferStatus':(U,[U]),'glDrawBuffer':(None,[U]),'glReadBuffer':(None,[U]),
            'glPixelStorei':(None,[U,I]),'glFinish':(None,[]),
        }
        for n,(ret,args) in defs.items(): setattr(self,n,bind(self.g,n,ret,args))
        print('Renderer:',self.glGetString(0x1F01).decode(),flush=True)
        vao=U(); self.glGenVertexArrays(1,C.byref(vao)); self.glBindVertexArray(vao)
        self.emptyvao=vao.value
        self.glPixelStorei(0x0D05,1); self.glPixelStorei(0x0CF5,1)
        self.glEnable(0x0B71)
    def program(self,vs,fs):
        pid=self.glCreateProgram()
        for src,typ in [(vs,0x8B31),(fs,0x8B30)]:
            s=self.glCreateShader(typ); txt=C.c_char_p(src.encode()); self.glShaderSource(s,1,C.byref(txt),None); self.glCompileShader(s)
            ok=C.c_int(); self.glGetShaderiv(s,0x8B81,C.byref(ok))
            if not ok.value:
                buf=C.create_string_buffer(8192); self.glGetShaderInfoLog(s,8192,None,buf); raise RuntimeError(buf.value.decode())
            self.glAttachShader(pid,s)
        self.glLinkProgram(pid); ok=C.c_int(); self.glGetProgramiv(pid,0x8B82,C.byref(ok))
        if not ok.value:
            buf=C.create_string_buffer(8192); self.glGetProgramInfoLog(pid,8192,None,buf); raise RuntimeError(buf.value.decode())
        return pid
    def u(self,p,n,val):
        loc=self.glGetUniformLocation(p,n.encode())
        if isinstance(val,np.ndarray) and val.shape==(4,4): self.glUniformMatrix4fv(loc,1,1,val.astype(np.float32).ctypes.data_as(C.POINTER(C.c_float)))
        elif isinstance(val,(tuple,list,np.ndarray)):
            if len(val)==3:self.glUniform3f(loc,*val)
            else:self.glUniform2f(loc,*val)
        else:self.glUniform1f(loc,float(val))
    def tex(self,w,h,data=None,depth=False):
        tid=C.c_uint(); self.glGenTextures(1,C.byref(tid)); self.glBindTexture(0x0DE1,tid)
        self.glTexImage2D(0x0DE1,0,0x81A6 if depth else 0x881A,w,h,0,0x1902 if depth else 0x1908,0x1406,None if data is None else data.ctypes.data_as(C.c_void_p))
        for key,v in [(0x2801,0x2601),(0x2800,0x2601),(0x2802,0x812F),(0x2803,0x812F)]: self.glTexParameteri(0x0DE1,key,v)
        return tid.value
    def framebuffer(self,w,h,withdepth=False):
        tid=self.tex(w,h); fb=C.c_uint();self.glGenFramebuffers(1,C.byref(fb)); self.glBindFramebuffer(0x8D40,fb)
        self.glFramebufferTexture2D(0x8D40,0x8CE0,0x0DE1,tid,0)
        if withdepth:
            d=self.tex(w,h,depth=True);self.glFramebufferTexture2D(0x8D40,0x8D00,0x0DE1,d,0)
        assert self.glCheckFramebufferStatus(0x8D40)==0x8CD5
        return fb.value,tid


ATLAS_REGIONS={}
class Mesh:
    def __init__(self): self.data=[]; self.gl=None
    def face(self,pts,c,em=0,uvs=None):
        pts=np.array(pts,dtype=float); n=normalize(np.cross(pts[1]-pts[0],pts[2]-pts[0])); col=color(c)
        if uvs is None: uvs=[(-1.,-1.)]*len(pts)
        for i in range(1,len(pts)-1):
            for j in (0,i,i+1): self.data.append([*pts[j],*n,*col,em,*uvs[j]])
    def box(self,pos,size,c,bevel=0,M=None,em=0):
        h=np.array(size,dtype=float)/2; b=min(bevel,float(min(h))*.92)
        faces=[]
        for a in range(3):
            axes=[x for x in range(3) if x!=a]
            for s in (-1,1):
                ps=[]
                for p,q in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    v=np.zeros(3);v[a]=s*h[a];v[axes[0]]=p*(h[axes[0]]-b);v[axes[1]]=q*(h[axes[1]]-b);ps.append(v)
                if np.dot(np.cross(ps[1]-ps[0],ps[2]-ps[0]),np.eye(3)[a]*s)<0:ps.reverse()
                faces.append(ps)
        if b>0:
            for a in range(3):
                for bb in range(a+1,3):
                    k=3-a-bb
                    for sa in (-1,1):
                        for sb in (-1,1):
                            ps=[]
                            for end,which in [(-1,0),(-1,1),(1,1),(1,0)]:
                                v=np.zeros(3);v[k]=end*(h[k]-b);v[a]=sa*(h[a]-(b if which else 0));v[bb]=sb*(h[bb]-(0 if which else b));ps.append(v)
                            normal=np.zeros(3);normal[a]=sa;normal[bb]=sb
                            if np.dot(np.cross(ps[1]-ps[0],ps[2]-ps[0]),normal)<0:ps.reverse()
                            faces.append(ps)
            for sx in (-1,1):
                for sy in (-1,1):
                    for sz in (-1,1):
                        signs=np.array([sx,sy,sz]); ps=[]
                        for a in range(3):
                            v=(h-b)*signs;v[a]=h[a]*signs[a];ps.append(v)
                        if np.dot(np.cross(ps[1]-ps[0],ps[2]-ps[0]),signs)<0:ps.reverse()
                        faces.append(ps)
        for ps in faces:
            ps=np.array(ps)+np.array(pos)
            if M is not None: ps=(M@np.column_stack((ps,np.ones(len(ps)))).T).T[:,:3]
            self.face(ps,c,em)
    def cylinder(self,pos,r,length,c,axis='y',n=20,r2=None,em=0):
        r2=r if r2 is None else r2
        rings=[]
        for k,rr in [(-1,r),(1,r2)]:
            ring=[]
            for i in range(n):
                a=2*math.pi*i/n
                v=np.array([rr*math.cos(a),k*length/2,rr*math.sin(a)])
                if axis=='z':v=v[[0,2,1]]
                elif axis=='x':v=v[[1,0,2]]
                ring.append(v+pos)
            rings.append(ring)
        # The XZ circle runs clockwise when viewed from above.
        def face(p):self.face(p[::-1] if axis!='y' else p,c,em)
        face(rings[0]);face(rings[1][::-1])
        for i in range(n):j=(i+1)%n;face([rings[0][i],rings[1][i],rings[1][j],rings[0][j]])
    def torus(self,pos,r,minor,c,axis='z',n=32,m=8,start=0,end=2*math.pi):
        points=[]
        for i in range(n+1):
            a=start+(end-start)*i/n;row=[]
            for j in range(m):
                b=2*math.pi*j/m; v=np.array([(r+minor*math.cos(b))*math.cos(a),(r+minor*math.cos(b))*math.sin(a),minor*math.sin(b)])
                if axis=='y':v=v[[0,2,1]]
                elif axis=='x':v=v[[2,0,1]]
                row.append(v+pos)
            points.append(row)
        for i in range(n):
            for j in range(m):
                k=(j+1)%m;pts=[points[i][j],points[i+1][j],points[i+1][k],points[i][k]]
                self.face(pts[::-1] if axis=='y' else pts,c)
    def sphere(self,pos,r,c,em=0,n=24,m=12):
        for j in range(m):
            a=-math.pi/2+math.pi*j/m;b=-math.pi/2+math.pi*(j+1)/m
            for i in range(n):
                p=2*math.pi*i/n;q=2*math.pi*(i+1)/n
                vs=[(math.cos(aa)*math.cos(pp),math.sin(aa),math.cos(aa)*math.sin(pp)) for aa,pp in [(a,p),(a,q),(b,q),(b,p)]]
                if j==0:vs=vs[1:]
                if j==m-1:vs=vs[:3]
                self.face((np.array(vs)*r+pos)[::-1],c,em)
    def label(self,center,w,h,key,M=None):
        x,y,z=center; ps=np.array([(x-w/2,y-h/2,z),(x+w/2,y-h/2,z),(x+w/2,y+h/2,z),(x-w/2,y+h/2,z)])
        if M is not None:ps=(M@np.column_stack([ps,np.ones(4)]).T).T[:,:3]
        u0,v0,u1,v1=ATLAS_REGIONS[key];self.face(ps,'white',uvs=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])
    def upload(self,gl):
        self.gl=gl; self.count=len(self.data); arr=np.array(self.data,dtype=np.float32)
        self.vao=C.c_uint();self.vbo=C.c_uint(); gl.glGenVertexArrays(1,C.byref(self.vao)); gl.glBindVertexArray(self.vao)
        gl.glGenBuffers(1,C.byref(self.vbo));gl.glBindBuffer(0x8892,self.vbo)
        gl.glBufferData(0x8892,arr.nbytes,arr.ctypes.data_as(C.c_void_p),0x88E4)
        for i,(sz,off) in enumerate([(3,0),(3,3),(3,6),(1,9),(2,10)]):
            gl.glEnableVertexAttribArray(i);gl.glVertexAttribPointer(i,sz,0x1406,0,48,C.c_void_p(off*4))
        self.data=[]
    def draw(self,prog,M):
        self.gl.u(prog,'model',M)
        self.gl.u(prog,'vehicle',1. if getattr(self,'name','') in ('van','lid') else 0.)
        self.gl.glBindVertexArray(self.vao);self.gl.glDrawArrays(4,0,self.count)

