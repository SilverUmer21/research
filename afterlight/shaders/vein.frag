#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
void main(){
 float crossSection=pow(max(0.,1.-U.y*U.y),.5);
 float flow=fract(U.x*.48-time*(.74+boost*.55)+M);
 float pulse=exp(-pow((flow-.5)/.11,2.));
 float turbulence=noise3(localPoint(W)*29.+vec3(-time*3.,time,0.));
 float eddy=pow(.5+.5*sin(U.x*20.+turbulence*7.-time*6.),5.);
 vec3 fire=energyColor();vec3 hot=mix(fire,vec3(1.),.62);
 vec3 col=fire*(.42+.40*eddy+boost*.30)+hot*(pulse*(1.2+boost*1.4)+eddy*.25)*pow(crossSection,2.);
 col*=.55+.45*crossSection;frag=vec4(col,1.);
}
