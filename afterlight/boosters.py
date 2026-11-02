"""Twin mechanical boosters, deployable nozzle petals, 3D plumes and sparks."""
import math
import numpy as np

def build_boosters(mesh,torus):
    housing=mesh('boosterHousing',True);core=mesh('boostercore',True)
    for side in (-1,1):
        cy=.48;cz=side*.53
        for j in range(40):
            a=j*2*math.pi/40;b=(j+1)*2*math.pi/40
            def p(x,r,t):return (x,cy+math.cos(t)*r,cz+math.sin(t)*r)
            for xa,xb,ra,rb in [(-2.22,-2.43,.245,.265),(-2.43,-2.72,.265,.205)]:
                housing.face([p(xa,ra,a),p(xb,rb,a),p(xb,rb,b),p(xa,ra,b)],'#293c67')
            housing.face([p(-2.72,.205,a),p(-2.72,.160,a),p(-2.72,.160,b),p(-2.72,.205,b)],'#7b8ba9')
            housing.face([p(-2.72,.16,a),p(-2.72,.16,b),p(-2.43,.17,b),p(-2.43,.17,a)],'#172740')
        torus(housing,(-2.70,cy,cz),.213,.025,'#4e5e8c',axis='x',mat=-1,n=48)
        torus(core,(-2.713,cy,cz),.172,.012,'#2aa8ff',axis='x',mat=2.6,n=48)
        core.cylinder((-2.49,cy,cz),.156,.025,'#32c6ff',axis='x',n=40,em=2.6)
        for j in range(6):
            a=j*math.pi/3
            housing.box((-2.40,cy+math.cos(a)*.277,cz+math.sin(a)*.277),(.13,.035,.035),'#4c5d83',.010)
    petals=mesh('petal',True);petals.box((0,0,0),(.27,.042,.105),'#526487',.012)
    # U/angle/layer are expanded into animated tube positions by the vertex shader.
    jet=mesh('jets')
    for side in (-1,1):
        for layer in (0.,1.):
            for i in range(72):
                a=i/72;b=(i+1)/72
                for j in range(24):
                    t=j*2*math.pi/24;tt=(j+1)*2*math.pi/24
                    for u,q in [(a,t),(b,t),(b,tt),(a,t),(b,tt),(a,tt)]:
                        jet.data.append([u,q,layer,0,1,0,float(side),0,0,layer,u,q/(2*math.pi)])
    sparks=mesh('boostSparks');rng=np.random.default_rng(85)
    for side in (-1,1):
        for i in range(140):
            r=rng.random(3)
            for uv in [(-1,-1),(1,-1),(1,1),(-1,-1),(1,1),(-1,1)]:
                sparks.data.append([*r,0,1,0,float(side),0,0,rng.random(),*uv])
