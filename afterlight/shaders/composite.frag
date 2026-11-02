#version 330 core
#include "common.glsl"
in vec2 uv;out vec4 frag;uniform sampler2D src,glow;uniform vec2 pixel,heatA0,heatB0,heatA1,heatB1;
float segment(vec2 p,vec2 a,vec2 b){vec2 d=b-a;float t=clamp(dot(p-a,d)/max(dot(d,d),.00001),0.,1.);return length(p-a-d*t);}
void main(){
 float heat=exp(-pow(min(segment(uv,heatA0,heatB0),segment(uv,heatA1,heatB1))/.016,2.))*boost;
 vec2 q=uv+vec2(sin(uv.y*170.+time*35.),cos(uv.x*140.-time*28.))*heat*.0012;
 vec3 col=texture(src,q).rgb+texture(glow,q).rgb*.34;
 float lum=dot(col,vec3(.2126,.7152,.0722));float shoulder=lum/(1.+max(0.,lum-.9)*.4);
 col*=shoulder/max(lum,.00001);col=srgb(col);col*=1.-.16*pow(length((uv-.5)*vec2(1.,.8)),1.3);frag=vec4(col,1.);
}
