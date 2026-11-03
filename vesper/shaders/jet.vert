#version 330 core
#include "common.glsl"
// Three nested plume shells: 0 white-hot core, 1 magenta sheath, 2 violet haze.
layout(location=0)in vec3 param;layout(location=2)in vec3 sides;
uniform mat4 model,vp;
out vec3 P;out vec2 U;out float layer;out float diamond;
void main(){
 float u=param.x,a=param.y;layer=param.z;
 float len=(.18+boost*3.4)*(1.+speed*.010)*(1.+.03*sin(time*47.+sides.x));
 // Stationary shock diamonds: the core pinches at fixed stations along the plume.
 float st=u*len/.42;
 diamond=pow(.5+.5*cos(st*2.*PI),6.)*smoothstep(.0,.08,u)*exp(-u*2.6);
 float base=layer<.5?.42:(layer<1.5?1.:1.5);
 float r=.135*pow(max(0.,1.-u),layer>1.5?.8:.55)*(1.+u*(layer<1.5?.30:.7))*base;
 if(layer<.5)r*=.75+.35*diamond;
 if(layer>1.5)r*=1.+.25*noise3(vec3(u*6.-time*3.,a,sides.x));
 r*=1.+.10*sin(a*3.+u*33.-time*27.);
 float sway=.012*sin(u*15.-time*12.)*u+u*u*.05*speed*.02;
 vec3 p=vec3(-2.73-u*len,.48+cos(a)*r+sway,sides.x*.53+sin(a)*r);
 vec4 w=model*vec4(p,1.);P=w.xyz;if(reflectionPass>.5)P.y=-P.y;
 gl_Position=vp*w;U=vec2(u,a/(2.*PI));
}
