#version 330 core
#include "common.glsl"
// Capture embers: the dissolving car's body flies apart upward in its own colour.
layout(location=0)in vec3 rnd;layout(location=3)in float seed;layout(location=4)in vec2 uv;
uniform mat4 model,vp;uniform vec3 cameraRight,cameraUp;uniform float burstT;out vec2 U;out float A;out float T;
void main(){
 vec3 start=vec3(-2.3+rnd.x*4.6,.3+rnd.y*1.3,(rnd.z-.5)*2.);
 float delay=rnd.x*.55+seed*.25;float tt=max(0.,burstT-delay);
 vec3 vel=vec3((rnd.z-.5)*1.5,1.2+seed*3.2,(rnd.y-.5)*1.6);
 vec3 p=start+vel*tt+vec3(sin(tt*3.+seed*9.)*.3,-.9*tt*tt,cos(tt*2.7+seed*7.)*.3);
 vec4 w=model*vec4(p,1.);float sz=.012+seed*.03;
 w.xyz+=cameraRight*uv.x*sz+cameraUp*uv.y*sz;
 gl_Position=vp*w;U=uv;T=clamp(1.-tt/2.2,0.,1.);A=step(.001,tt)*T;
}
