#version 330 core
// Letters erupt from the floor left to right with a small overshoot.
layout(location=0)in vec3 pos;layout(location=1)in vec3 normal;layout(location=2)in vec3 color;layout(location=3)in float material;layout(location=4)in vec2 uv;
uniform mat4 model,vp,lightvp;uniform float reflectionPass,logoTime,logoH;
out vec3 W,N,C;out vec2 U;out float M;out vec4 L;
void main(){
 float q=clamp((logoTime-uv.x*.9)/.75,0.,1.);
 float r=q<=0.?0.:1.+2.2*(q-1.)*(q-1.)*(q-1.)+1.2*(q-1.)*(q-1.);
 vec3 p=pos;p.y-=(1.-r)*logoH*1.08;
 vec4 w=model*vec4(p,1.);N=normal;W=w.xyz;if(reflectionPass>.5){W.y=-W.y;N.y=-N.y;}
 C=color;M=material;U=uv;L=lightvp*vec4(W,1.);gl_Position=vp*w;
}
