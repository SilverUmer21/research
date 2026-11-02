#version 330 core
#include "common.glsl"
layout(location=0)in vec3 anchor;layout(location=1)in vec3 param;layout(location=3)in float seed;
uniform mat4 model,vp;out vec2 U;out float layer;out float heat;
void main(){
 float u=param.x,a=param.y;layer=param.z;
 float distance=seed<.5?.35:(seed<1.5?.74:(seed<2.5?1.05:.50));
 float flow=fract(distance*.48-time*(.74+boost*.55)+(seed>2.5?.12:0.));
 heat=exp(-pow((flow-.5)/.15,2.));
 float flicker=.80+.20*sin(time*12.+seed*2.+u*8.);
 float h=.035+boost*.13+charge*.04+heat*.10;
 float radius=(.020+boost*.014)*pow(max(0.,1.-u),.7)*(layer<.5?.50:1.);
 vec3 p=anchor+vec3(cos(a)*radius,u*h*flicker,sin(a)*radius);
 p.x+=u*u*.024*sin(time*10.+seed*2.);p.z+=u*u*.018*cos(time*11.+seed);
 gl_Position=vp*model*vec4(p,1.);U=vec2(u,a/(2.*PI));
}
