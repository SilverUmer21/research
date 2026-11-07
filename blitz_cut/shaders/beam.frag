#version 330 core
#include "common.glsl"
in vec2 U;in float layer;out vec4 frag;
uniform vec3 beamColor;uniform float head,tail,inten,prismMode;
void main(){
 float u=U.x;if(u>head||u<tail)discard;
 float dash=pow(.5+.5*sin(u*40.-time*22.),3.);
 float tip=exp(-sq((head-u)/.05));
 vec3 h=prismMode>.5?ring(u*1.5-time):beamColor;
 vec3 c=heat(h,.5+.25*dash+.5*tip);
 float a=(layer<.5?.85:.18)*(.55+.45*dash)*inten;
 frag=vec4(c*(1.+2.*tip),a);
}
