"""AFTERLIGHT: three original cars with molten veins and twin boosters.
Actual 3D geometry, traveling surface light, blaze and a reflective studio.
"""
import os,sys,math,ctypes as C,subprocess,time,argparse,json,struct,wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import engine as e
from styles import STYLES,recolor
from engine import GL,Mesh,trans,rot,scale,normalize,lookat,perspective,ortho,smooth,ease,lerp,color,linear

ROOT=Path(__file__).resolve().parent
FONT=str(ROOT/'fonts/BarlowCondensed-Bold.ttf')
e.COLORS.update(cream='#c4ccff',teal='#356876',brass='#bb8051',glass='#080f32',rubber='#16242c',roof='#304853',stone='#394656')
def shader(name):return (ROOT/'shaders'/name).read_text().replace('#include "common.glsl"',(ROOT/'shaders/common.glsl').read_text())
def sm(a,b,t):return a+(b-a)*smooth(t)
def quint(t):
    q=min(1.,max(0.,t));return q*q*q*(q*(q*6.-15.)+10.)
def ellipsoid(m,c,r,col,mat=0,n=36,ny=20):
    start=len(m.data);m.sphere((0,0,0),1,col,n=n,m=ny)
    rr=np.array(r);cc=np.array(c)
    for row in m.data[start:]:
        p=np.array(row[:3]);row[:3]=(cc+p*rr).tolist();row[3:6]=normalize(p/rr).tolist();row[9]=mat

def transform_new(m,start,M):
    nn=np.linalg.inv(M[:3,:3]).T
    for row in m.data[start:]:
        row[:3]=(M@np.array([*row[:3],1]))[:3].tolist();row[3:6]=normalize(nn@row[3:6]).tolist()

def torus(m,c,r,t,col,axis='z',s=(1,1,1),mat=-1,n=40):
    start=len(m.data);m.torus((0,0,0),r,t,col,axis=axis,n=n,m=10)
    transform_new(m,start,trans(*c)@scale(*s))
    for row in m.data[start:]:row[9]=mat

def segment_matrix(a,b):
    a=np.array(a,dtype=float);b=np.array(b,dtype=float);y=normalize(b-a);x=normalize(np.cross(y,(0,0,1)))
    if np.linalg.norm(x)<.1:x=normalize(np.cross(y,(1,0,0)))
    z=normalize(np.cross(x,y));mm=np.eye(4,dtype=np.float32);mm[:3,:3]=np.column_stack((x,y*np.linalg.norm(b-a),z));mm[:3,3]=(a+b)/2;return mm

def wire(m,pts,r,col,mat=-1):
    for a,b in zip(pts[:-1],pts[1:]):
        st=len(m.data);m.cylinder((0,0,0),r,1,col,n=12);transform_new(m,st,segment_matrix(a,b))
        for row in m.data[st:]:row[9]=mat

def atlas():
    im=Image.new('RGB',(1024,512),'#111823');d=ImageDraw.Draw(im)
    rows=[('brand','blitzedo','#111823','#e1e8ef'),('number0','07','#111823','#ffb656'),('number1','08','#111823','#7df9ff'),('number2','09','#111823','#ff6bf2')]
    for i,(key,text,bg,fg) in enumerate(rows):
        y=i*128;d.rectangle((0,y,1024,y+128),fill=bg);f=ImageFont.truetype(FONT,116);bb=d.textbbox((0,0),text,font=f);tw=bb[2]-bb[0]
        d.text(((1024-tw)/2,y+(128-(bb[3]-bb[1]))/2-bb[1]),text,font=f,fill=fg)
        e.ATLAS_REGIONS[key]=((1024-tw-40)/2048,(512-y-128)/512,(1024+tw+40)/2048,(512-y)/512)
    im.save(ROOT/'atlas.png');return np.array(im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).convert('RGBA'),dtype=np.float32)/255


def boost_at(t):return .025+.975*smooth((t-4.4)/1.6)
def deploy_at(t):return .05+.95*smooth((t-4.0)/1.65)
def brake_at(t):return .35+.40*smooth((t-5.)/2.)
_TIMES=np.linspace(0,30,6001)
_DIST=np.cumsum([.13+boost_at(t)*3.5 for t in _TIMES])*.005

def car_pose(t):
    b=boost_at(t);squat=-.035*b
    recoil=-.045*math.exp(-((t-6.0)/.18)**2)
    return trans(recoil,squat+.006*math.sin(t*15)*b,0)@rot(.018*b,'z')@rot(.008*math.sin(t*.6)*b,'y')

class World:
    def __init__(self,g,variants=(0,1,2)):
        self.meshes={};self.cars={}
        from car_geometry import build_car
        from boosters import build_boosters
        from veins import build_veins
        for v in variants:
            parts={};self.cars[v]=parts
            def mesh(name,hero=False):
                m=Mesh();m.name=name;m.hero=hero;m.variant=v;parts[name]=m
                self.meshes[(str(v)+':'+name) if len(variants)>1 else name]=m;return m
            body,inside,wheel=build_car(mesh,ellipsoid,torus,wire,transform_new,style=v)
            build_veins(mesh,body,v);build_boosters(mesh,torus)
            for m in parts.values():recolor(m,v)
        floor=Mesh();floor.name='floor';floor.hero=False
        floor.face([(-80,-.018,80),(80,-.018,80),(80,-.018,-80),(-80,-.018,-80)],'#080d18');self.floor=floor;self.meshes['floor']=floor
        for m in self.meshes.values():m.upload(g)
        print('Three-car geometry:',sum(m.count//3 for m in self.meshes.values()),'triangles',flush=True)
    def objects(self,t,variant=0,group=None):
        group=np.eye(4,dtype=np.float32) if group is None else group
        m=self.cars[variant];pose=group@car_pose(t);d=deploy_at(t)
        names=['shell','interior','filament','frontlava','taillava','lavachannels','plasma','glass','veinBeds','veins','boosterHousing','boostercore']
        out=[(m[k],pose) for k in names]
        spin=-float(np.interp(t,_TIMES,_DIST))/.435
        for xx in (-1.38,1.38):
            for side in (-1,1):
                steer=.025*math.sin(t*.7) if xx>0 else 0.
                out.append((m['wheel'],group@trans(xx,.44,side*.98*STYLES[variant]['width'])@rot(steer,'y')@rot(spin,'z')))
        for side in (-1,1):
            for j in range(6):
                a=j*math.pi/3;r=.213+d*.041
                q=(-2.62-d*.12,.48+math.cos(a)*r,side*.53+math.sin(a)*r)
                out.append((m['petal'],pose@trans(*q)@rot(a,'x')@rot(d*.14,'z')))
        return out,np.zeros(3),0.,.40+boost_at(t)*.60,0.

def scene(t):
    if t<27:
        v=min(2,int(t//9));return [(v,t-v*9,np.eye(4,dtype=np.float32))]
    return [(v,1.8+(t-27)*.12,trans((v-1)*.10,0,(v-1)*3.4)) for v in range(3)]

class Renderer:
    def __init__(self,w,h):
        self.w=w;self.h=h;self.g=g=GL(w,h);self.atlas=g.tex(1024,512,atlas());self.world=World(g)
        def program(v,f):return g.program(shader(v),shader(f))
        self.main=program('object.vert','object.frag');self.shadow=program('object.vert','shadow.frag')
        self.lava=program('object.vert','plasma.frag');self.glass=program('object.vert','glass.frag')
        self.jet=program('jet.vert','jet.frag');self.spark=program('spark.vert','spark.frag')
        self.vein=program('object.vert','vein.frag');self.blaze=program('blaze.vert','blaze.frag')
        self.sky=program('full.vert','sky.frag');self.floor=program('object.vert','floor.frag')
        self.bloom=program('full.vert','bloom.frag');self.comp=program('full.vert','composite.frag')
        self.fb,self.tex=g.framebuffer(w,h,True);self.bw=w//4;self.bh=h//4
        self.bf1,self.bt1=g.framebuffer(self.bw,self.bh);self.bf2,self.bt2=g.framebuffer(self.bw,self.bh)
        self.rf,self.rt=g.framebuffer(w//3,h//3,True)
        self.sd=g.tex(3072,3072,depth=True);f=C.c_uint();g.glGenFramebuffers(1,C.byref(f));self.sf=f.value
        g.glBindFramebuffer(0x8D40,self.sf);g.glFramebufferTexture2D(0x8D40,0x8D00,0x0DE1,self.sd,0);g.glDrawBuffer(0);g.glReadBuffer(0)
        self.pixels=np.empty((h,w,3),np.uint8)
        g.glBlendFunc=g.g.glBlendFunc;g.glBlendFunc.argtypes=[C.c_uint,C.c_uint];g.glBlendFunc.restype=None
        self.lightdir=normalize((.3,.83,.50));self.active_theme=0;self.active_frame=np.eye(4,dtype=np.float32);self.lineup=0
    def camera(self,t):
        if t<27:
            v=min(2,int(t//9));u=t-v*9
            if u<3.:
                q=smooth(u/3);a=math.radians(28+v*5+14*q);elev=math.radians(7+v*1.5+4*q);dist=9.3-.55*q;target=np.array([.05,.72,0]);fov=29.
            elif u<5.4:
                q=smooth((u-3)/2.4);a=math.radians(38+22*q);elev=math.radians(32+8*q);dist=4.65;target=np.array([1.05,.90,.16]);fov=32.
            else:
                q=smooth((u-5.4)/3.6);a=math.radians(136+17*q);elev=math.radians(11+3*q);dist=11.1;target=np.array([-1.25,.69,0]);fov=32.
        else:
            q=smooth((t-27)/3);a=math.radians(16-7*q);elev=math.radians(12);dist=14.8;target=np.array([0,.76,0]);fov=30.
        eye=target+dist*np.array([math.cos(a)*math.cos(elev),math.sin(elev),math.sin(a)*math.cos(elev)])
        return eye,target,fov
    def bindtex(self,u,t):self.g.glActiveTexture(0x84C0+u);self.g.glBindTexture(0x0DE1,t)
    def fs(self,p,fb,w,h):
        g=self.g;g.glBindFramebuffer(0x8D40,fb);g.glViewport(0,0,w,h);g.glDisable(0x0B71);g.glUseProgram(p);g.glBindVertexArray(g.emptyvao);g.glDrawArrays(4,0,3)
    def uniforms(self,p,t,eye,reflection=0):
        g=self.g;g.glUseProgram(p)
        for k,v in [('time',t),('eye',eye),('origin',self.active_frame[:3,3]),('phase',0),('charge',.40+.60*smooth((t-2.5)/2.0)),('warm',0),('lightDir',self.lightdir),('resolution',(self.w,self.h)),('boost',boost_at(t)),('brake',brake_at(t)),('reflectionPass',reflection),('hero',1),('gate',0),('theme',self.active_theme),('sceneMode',self.lineup),('carFrame',self.active_frame),('carInverse',np.linalg.inv(self.active_frame))]:g.u(p,k,v)
    def car(self,t,objects,vp,eye,view,reflection=False,variant=0,group=None):
        g=self.g;group=np.eye(4,dtype=np.float32) if group is None else group
        self.active_theme=variant;self.active_frame=group@car_pose(t);parts=self.world.cars[variant]
        mirror=scale(1,-1,1) if reflection else np.eye(4,dtype=np.float32)
        ref=float(reflection)
        self.uniforms(self.main,t,eye,ref);g.u(self.main,'vp',vp);g.u(self.main,'lightvp',self.lv)
        self.bindtex(0,self.sd);self.bindtex(1,self.atlas);g.glUniform1i(g.glGetUniformLocation(self.main,b'shadowmap'),0);g.glUniform1i(g.glGetUniformLocation(self.main,b'atlas'),1)
        special=['plasma','glass','frontlava','taillava','lavachannels','boostercore','veins']
        for m,M in objects:
            if m.name not in special:m.draw(self.main,mirror@M)
        self.uniforms(self.lava,t,eye,ref);g.u(self.lava,'vp',vp)
        kinds={'plasma':0,'frontlava':1,'taillava':2,'lavachannels':3,'boostercore':4}
        for m,M in objects:
            if m.name in kinds:g.u(self.lava,'lavaKind',kinds[m.name]);m.draw(self.lava,mirror@M)
        self.uniforms(self.vein,t,eye,ref);g.u(self.vein,'vp',vp)
        for m,M in objects:
            if m.name=='veins':m.draw(self.vein,mirror@M)
        self.uniforms(self.glass,t,eye,ref);g.u(self.glass,'vp',vp)
        g.glEnable(0x0BE2);g.glBlendFunc(0x0302,0x0303);g.glDepthMask(0)
        for m,M in objects:
            if m.name=='glass':m.draw(self.glass,mirror@M)
        self.uniforms(self.jet,t,eye,ref);g.u(self.jet,'vp',vp);g.glBlendFunc(0x0302,1)
        parts['jets'].draw(self.jet,mirror@self.active_frame)
        self.uniforms(self.blaze,t,eye,ref);g.u(self.blaze,'vp',vp);parts['blaze'].draw(self.blaze,mirror@self.active_frame)
        if not reflection:
            self.uniforms(self.spark,t,eye,0);g.u(self.spark,'vp',vp);g.u(self.spark,'cameraRight',view[0,:3]);g.u(self.spark,'cameraUp',view[1,:3])
            parts['boostSparks'].draw(self.spark,self.active_frame)
        g.glDepthMask(1);g.glDisable(0x0BE2)
    def render(self,t,text=True):
        g=self.g;cars=scene(t);self.lineup=float(t>=27);eye,target,fov=self.camera(t)
        view=lookat(eye,target);vp=perspective(fov,self.w/self.h,.12,180)@view
        self.lightdir=normalize((.24+.06*math.sin(t*.16),.85,.48+.07*math.cos(t*.2)))
        self.lv=ortho(-12,12,-10,10,.1,60)@lookat(self.lightdir*26,(0,.4,0))
        batches=[(v,u,G,self.world.objects(u,v,G)[0]) for v,u,G in cars]
        g.glEnable(0x0B71);g.glBindFramebuffer(0x8D40,self.sf);g.glViewport(0,0,3072,3072);g.glClear(0x100)
        for v,u,G,objects in batches:
            self.active_theme=v;self.active_frame=G@car_pose(u);self.uniforms(self.shadow,u,eye);g.u(self.shadow,'vp',self.lv);g.u(self.shadow,'lightvp',self.lv)
            for m,M in objects:
                if m.name not in ('glass','veins'):m.draw(self.shadow,M)
        g.glBindFramebuffer(0x8D40,self.rf);g.glViewport(0,0,self.w//3,self.h//3);g.glClearColor(0,0,0,0);g.glClear(0x4000|0x100)
        for v,u,G,objects in batches:self.car(u,objects,vp,eye,view,True,v,G)
        g.glBindFramebuffer(0x8D40,self.fb);g.glViewport(0,0,self.w,self.h);g.glClear(0x4000|0x100)
        self.uniforms(self.sky,t,eye);self.fs(self.sky,self.fb,self.w,self.h);g.glEnable(0x0B71)
        self.uniforms(self.floor,cars[0][1],eye);g.u(self.floor,'vp',vp);g.u(self.floor,'lightvp',self.lv)
        self.bindtex(0,self.sd);self.bindtex(2,self.rt)
        g.glUniform1i(g.glGetUniformLocation(self.floor,b'shadowmap'),0);g.glUniform1i(g.glGetUniformLocation(self.floor,b'reflectionMap'),2)
        self.world.floor.draw(self.floor,np.eye(4,dtype=np.float32))
        for v,u,G,objects in batches:self.car(u,objects,vp,eye,view,False,v,G)
        g.glUseProgram(self.bloom);self.bindtex(0,self.tex);g.glUniform1i(g.glGetUniformLocation(self.bloom,b'src'),0);g.u(self.bloom,'extract',1);g.u(self.bloom,'stepv',(1/self.bw,0));self.fs(self.bloom,self.bf1,self.bw,self.bh)
        self.bindtex(0,self.bt1);g.u(self.bloom,'extract',0);g.u(self.bloom,'stepv',(0,1/self.bh));self.fs(self.bloom,self.bf2,self.bw,self.bh)
        self.bindtex(0,self.bt2);g.u(self.bloom,'stepv',(3/self.bw,0));self.fs(self.bloom,self.bf1,self.bw,self.bh)
        self.bindtex(0,self.bt1);g.u(self.bloom,'stepv',(0,3/self.bh));self.fs(self.bloom,self.bf2,self.bw,self.bh)
        v,u,G=cars[0];self.active_theme=v;self.active_frame=G@car_pose(u)
        self.uniforms(self.comp,u,eye);self.bindtex(0,self.tex);self.bindtex(1,self.bt2)
        g.glUniform1i(g.glGetUniformLocation(self.comp,b'src'),0);g.glUniform1i(g.glGetUniformLocation(self.comp,b'glow'),1);g.u(self.comp,'pixel',(1/self.w,1/self.h))
        for i,side in enumerate((-1,1)):
            for key,x in [('heatA',-2.73),('heatB',-2.73-(.20+boost_at(u)*3.5))]:
                p=vp@self.active_frame@np.array([x,.48,side*.53,1]);uv=p[:2]/p[3]*.5+.5;g.u(self.comp,key+str(i),uv)
        self.fs(self.comp,0,self.w,self.h)
        g.glReadPixels(0,0,self.w,self.h,0x1907,0x1401,self.pixels.ctypes.data_as(C.c_void_p));im=Image.fromarray(self.pixels[::-1].copy())
        return self.overlay(im,t)
    def overlay(self,im,t):
        w,h=im.size;lay=Image.new('RGBA',im.size);d=ImageDraw.Draw(lay)
        bar=round(h*.035);d.rectangle((0,0,w,bar),fill='#030611');d.rectangle((0,h-bar,w,h),fill='#030611')
        if t<.4:d.rectangle((0,0,w,h),fill=(3,6,17,int(255*(1-smooth(t/.4)))))
        if t>29.55:d.rectangle((0,0,w,h),fill=(3,6,17,int(255*smooth((t-29.55)/.45))))
        return Image.alpha_composite(im.convert('RGBA'),lay).convert('RGB')

def main():
    p=argparse.ArgumentParser();p.add_argument('--stills',action='store_true');p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080);p.add_argument('--frames',type=int,default=900);p.add_argument('--start',type=int,default=0);p.add_argument('--output',default=str(ROOT/'AFTERLIGHT_picture.mp4'));a=p.parse_args()
    (ROOT/'renders').mkdir(exist_ok=True)
    r=Renderer(a.width,a.height)
    if a.stills:
        for t,name in [(1.5,'cinder_front'),(4.2,'cinder_veins'),(7.2,'cinder_boost'),(10.5,'glacier_front'),(13.2,'glacier_veins'),(16.2,'glacier_boost'),(19.5,'vesper_front'),(22.2,'vesper_veins'),(25.2,'vesper_boost'),(28.5,'lineup')]:
            temp=ROOT/'renders'/f'{name}.tmp.png';r.render(t).save(temp);temp.replace(ROOT/'renders'/f'{name}.png');print('RENDERED',name,flush=True)
        return
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{a.width}x{a.height}','-r','30','-i','-','-an','-vf','scale=1920:1080:flags=lanczos:out_color_matrix=bt709','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-movflags','+faststart',a.output]
    out=subprocess.Popen(cmd,stdin=subprocess.PIPE);begin=time.time()
    for i in range(a.start,a.start+a.frames):
        out.stdin.write(r.render(i/30).tobytes())
        if i%30==0:print('FRAME',i,'elapsed',round(time.time()-begin,1),flush=True)
    out.stdin.close();assert out.wait()==0;print('PICTURE COMPLETE',flush=True)
if __name__=='__main__':main()
