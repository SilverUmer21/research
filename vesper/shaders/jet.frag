#version 330 core
#include "common.glsl"
in vec3 P;in vec2 U;in float layer;in float diamond;out vec4 frag;
void main(){
 float u=U.x;
 float flow=noise3(vec3(u*22.-time*11.,sin(U.y*2.*PI)*2.,cos(U.y*2.*PI)*2.));
 float streak=noise3(vec3(u*5.-time*6.,U.y*18.,1.));
 float t;float a;
 if(layer<.5){t=.86-u*.5+diamond*.45;a=(1.-smoothstep(.25,.62,u))*(.45+.55*flow)*(.30+.70*diamond)*.55;}
 else if(layer<1.5){t=.66-u*.42+diamond*.12+.10*flow;a=pow(max(0.,1.-u),.7)*(.25+.75*flow)*.30;}
 else{t=.40-u*.22+.1*streak;a=pow(max(0.,1.-u),.6)*(.3+.7*streak)*.10;}
 vec3 c=magma(t);
 if(layer>1.5)c=mix(c,boosterColor()*1.6,.55);
 a*=(.15+boost*.85);
 frag=vec4(c*(layer<.5?1.5:1.25),a);
}
