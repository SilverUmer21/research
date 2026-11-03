#version 330 core
#include "common.glsl"
// Embers leave the nozzles, fall under gravity and skip once on the wet floor.
layout(location=0)in vec3 rnd;layout(location=2)in vec3 side;layout(location=3)in float seed;layout(location=4)in vec2 uv;
uniform mat4 model,vp;uniform vec3 cameraRight,cameraUp;out vec2 U;out float A;out float T;
void main(){
 float life=.55+rnd.z*.9;
 float age=fract(rnd.x+time/life*(.8+rnd.y*.6));
 float tt=age*life;
 float len=.2+boost*3.4;
 float vx=(2.5+rnd.y*4.+speed*.35)*(.6+boost*.4);
 float theta=seed*2.*PI;float spread=.04+tt*(.5+rnd.y*.6);
 float y=.48+cos(theta)*spread*.4+tt*(.9*rnd.z)-4.9*tt*tt;
 if(y<.01){y=abs(y)*.35+.01;}
 vec3 p=vec3(-2.75-tt*vx-speed*tt*.9,y,side.x*.53+sin(theta)*spread);
 vec4 w=model*vec4(p,1.);vec3 tangent=normalize(mat3(model)*vec3(-1.,-0.15,0.));
 float sz=.006+rnd.z*.010;
 w.xyz+=tangent*uv.x*sz*(3.+speed*.5)+cameraUp*uv.y*sz;
 gl_Position=vp*w;U=uv;T=1.-age;A=pow(1.-age,1.3)*boost;
}
