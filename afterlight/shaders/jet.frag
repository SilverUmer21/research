#version 330 core
#include "common.glsl"
in vec3 P;in vec2 U;in float layer;out vec4 frag;
void main(){
 float u=U.x;float flow=noise3(vec3(u*25.-time*10.,sin(U.y*2.*PI)*2.,cos(U.y*2.*PI)*2.));
 float cells=pow(.5+.5*cos(u*10.*PI-time*.9),4.);
 vec3 c=mix(lin(vec3(.16,.88,1.)),lin(vec3(.41,.10,1.)),smoothstep(.08,.85,u));
 if(theme<.5)c=mix(lin(vec3(1.,.70,.12)),lin(vec3(1.,.04,.16)),smoothstep(.08,.9,u));
 else if(theme>1.5)c=mix(lin(vec3(.91,.10,1.)),lin(vec3(.27,.06,.95)),smoothstep(.08,.9,u));
 c=mix(c,(theme<.5?lin(vec3(1.,.91,.62)):(theme<1.5?lin(vec3(.72,1.,1.)):lin(vec3(1.,.64,1.)))),cells*(1.-u)*(layer<.5?.72:.12));
 if(layer<.5)c=mix(c,vec3(1.),.38*(1.-u));
 float a=pow(max(0.,1.-u),.55)*(.18+.82*flow)*(.20+boost*.80);
 a*=layer<.5?.43:.16;
 frag=vec4(c*(layer<.5?3.8+cells*2.3:2.6+flow*.7),a);
}
