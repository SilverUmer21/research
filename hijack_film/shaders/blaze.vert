#version 330 core
#include "common.glsl"
layout(location=0)in vec3 anchor;layout(location=1)in vec3 param;layout(location=3)in float seed;
uniform mat4 model,vp;out vec2 U;out float layer;out float heatv;out float S;
void main(){
 float u=param.x,a=param.y;layer=param.z;S=seed;
 float flow=fract((seed<.5?.35:(seed<1.5?.74:(seed<2.5?1.05:.50)))*.48-flowPhase);
 heatv=exp(-sq((flow-.5)/.15))*alive;
 float h=(.03+boost*.14+charge*.04+heatv*.12)*alive;
 float radius=(.020+boost*.014)*pow(max(0.,1.-u),.7)*(layer<.5?.50:1.);
 vec3 p=anchor+vec3(cos(a)*radius,u*h*(.8+.2*sin(time*12.+seed*2.+u*8.)),sin(a)*radius);
 p.x-=u*u*.024*sin(time*10.+seed*2.);p.z+=u*u*.018*cos(time*11.+seed);
 gl_Position=vp*model*vec4(p,1.);U=vec2(u,a/(2.*PI));
}
