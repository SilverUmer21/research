"""Organic branching channels conforming to the actual car triangles.
Each molten ribbon carries distance-along-path coordinates for travelling pulses.
"""
import math
import numpy as np
from engine import normalize

class Projector:
    def __init__(self,body,axis=1,sign=1):
        tri=np.asarray(getattr(body,"surface_data",body.data),dtype=float).reshape(-1,3,12)
        normals=tri[:,0,3:6]
        keep=(normals[:,axis]*sign)>.10
        if axis==1:keep&=np.max(tri[:,:,1],axis=1)<1.12
        self.tri=tri[keep,:,:3]
        self.axis=axis;self.sign=sign;self.free=[i for i in range(3) if i!=axis]
        t=self.tri[:,:,self.free];self.a=t[:,0];self.b=t[:,1]-t[:,0];self.c=t[:,2]-t[:,0]
        self.den=self.b[:,0]*self.c[:,1]-self.b[:,1]*self.c[:,0]
        good=np.abs(self.den)>1.e-8
        self.tri=self.tri[good];self.a=self.a[good];self.b=self.b[good];self.c=self.c[good];self.den=self.den[good]
    def __call__(self,q,offset=0.):
        q=np.asarray(q);d=q-self.a
        u=(d[:,0]*self.c[:,1]-d[:,1]*self.c[:,0])/self.den
        v=(self.b[:,0]*d[:,1]-self.b[:,1]*d[:,0])/self.den
        mask=(u>=-.002)&(v>=-.002)&(u+v<=1.002)
        p=self.tri[:,0]+u[:,None]*(self.tri[:,1]-self.tri[:,0])+v[:,None]*(self.tri[:,2]-self.tri[:,0])
        idx=np.where(mask)[0]
        if not len(idx):return None
        i=idx[np.argmax(p[idx,self.axis]*self.sign)];point=p[i].copy();point[self.axis]+=offset*self.sign
        return point

def curve(points,n=48):
    p=np.asarray(points,dtype=float);t=np.linspace(0,1,n)
    if len(p)==4:return np.array([(1-q)**3*p[0]+3*(1-q)**2*q*p[1]+3*(1-q)*q*q*p[2]+q**3*p[3] for q in t])
    return np.array([p[0]*(1-q)+p[-1]*q for q in t])

def build_veins(mesh,body,style=0):
    bed=mesh('veinBeds',True);molten=mesh('veins',True)
    top=Projector(body,1,1);sides={s:Projector(body,2,s) for s in (-1,1)}
    roots=[]
    def ribbon(controls,proj,width,phase=0.,start=0.):
        pts2=curve(controls,48);centers=[proj(p,.006) for p in pts2]
        dist=start
        for j in range(len(pts2)-1):
            a,b=centers[j],centers[j+1]
            if a is None or b is None:continue
            d=np.linalg.norm(b-a);tangent=normalize(pts2[j+1]-pts2[j]);cross=np.array([-tangent[1],tangent[0]])
            taper=.65+.35*math.sin(math.pi*(j+.5)/(len(pts2)-1))
            for target,w,offset,emit in [(bed,width*1.75,.005,0),(molten,width,.010,2.6)]:
                q=[pts2[j]-cross*w*taper,pts2[j]+cross*w*taper,pts2[j+1]+cross*w*taper,pts2[j+1]-cross*w*taper]
                p=[proj(x,offset) for x in q]
                if any(x is None for x in p):continue
                uv=[(dist,-1),(dist,1),(dist+d,1),(dist+d,-1)] if target is molten else None
                if np.cross(p[1]-p[0],p[2]-p[0])[proj.axis]*proj.sign<0:
                    p=p[::-1]
                    if uv is not None:uv=uv[::-1]
                st=len(target.data);target.face(p,'#080b13' if target is bed else '#ff952f',em=emit,uvs=uv)
                if target is molten:
                    for row in target.data[st:]:row[9]=phase
            dist+=d
        good=[p for p in centers if p is not None]
        if good:roots.append(good[len(good)//3])
    # Paired main arteries, each with distinct organic branch curvature.
    for side in (-1,1):
        z=lambda v:side*v
        ribbon([(.73,z(.20)),(1.11,z(.27)),(1.54,z(.45)),(2.17,z(.64))],top,.019,0.)
        branches=[
            ([(1.00,z(.29)),(1.13,z(.49)),(1.28,z(.79)),(1.49,z(.98))],.013,.30),
            ([(1.32,z(.41)),(1.43,z(.28)),(1.71,z(.20)),(1.95,z(.20))],.010,.66),
            ([(1.63,z(.52)),(1.70,z(.68)),(1.86,z(.77)),(2.05,z(.78))],.011,.99),
            ([(.86,z(.68)),(1.12,z(.79)),(1.32,z(.99)),(1.46,z(1.01))],.014,.28)
        ]
        for points,w,offset in branches:ribbon(points,top,w,0.,offset)
        # Door roots split toward the sill and the forward intake.
        proj=sides[side]
        ribbon([(-.95,.785),(-.60,.805),(.10,.80),(.78,.73)],proj,.013,.07,0.)
        ribbon([(-.78,.79),(-.92,.71),(-1.02,.55),(-.87,.45)],proj,.009,.07,.22)
        ribbon([(.40,.78),(.70,.82),(.90,.67),(.94,.48)],proj,.010,.07,1.10)
        # The rear artery feeds the turbine housing underneath the wing.
        ribbon([(-1.25,z(.43)),(-1.44,z(.59)),(-1.86,z(.55)),(-2.22,z(.57))],top,.016,.12,0.)
    # Small three-dimensional flame licks grow from hot branch junctions.
    flames=mesh('blaze')
    anchors=[]
    for x,z in [(1.05,.34),(1.42,-.46),(1.27,.94),(-1.68,-.54)]:
        p=top((x,z),.018)
        if p is not None:anchors.append(p)
    for k,p in enumerate(anchors):
        for layer in (0.,1.):
            for j in range(18):
                a=j/18.;b=(j+1)/18.
                for i in range(10):
                    q=i*math.pi*2/10;qq=(i+1)*math.pi*2/10
                    for u,t in [(a,q),(b,q),(b,qq),(a,q),(b,qq),(a,qq)]:
                        flames.data.append([*p,u,t,layer,1,1,1,float(k),u,t/(2*math.pi)])
    print('Vein ribbons:',len(molten.data)//3,'triangles; flame anchors:',len(anchors),flush=True)
