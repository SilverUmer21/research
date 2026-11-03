#version 330 core
#include "common.glsl"
// blitzedo letters: molten prism lava faces, obsidian sides with glowing seams, a light sweep.
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
uniform float rise,sweep,settle;
vec2 cell(vec2 p){vec2 i=floor(p),f=fract(p);float d1=8.,d2=8.;
 for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec2 g=vec2(x,y);vec2 o=vec2(hash2(i+g),hash2(i+g+17.3));o=.5+.42*sin(time*.5+6.28*o);
  float d=length(g+o-f);if(d<d1){d2=d1;d1=d;}else if(d<d2)d2=d;}
 return vec2(d1,d2-d1);}
void main(){
 vec3 n=normalize(N),v=normalize(viewEye()-W);
 float u=U.x,h=U.y;
 float churn=fbm(vec3(u*9.-time*.5,h*4.,time*.4));
 vec2 wp=vec2(u*95.,h*26.)+vec2(fbm(vec3(u*20.,h*6.,time*.3)),fbm(vec3(u*20.+5.,h*6.,time*.3)))*2.4;
 vec2 vc=cell(wp+vec2(-time*1.2,time*.6));
 float crack=1.-smoothstep(.0,.14,vc.y);
 vec3 hue=ring(u*1.25+h*.25-time*.22+churn*.35);
 float hot=1.-settle;                       // white-hot as it erupts, cooling into colour
 float t=.55+.25*churn+.2*crack+.35*hot;
 float sw=exp(-sq((u-sweep)/.025));
 vec3 col;
 if(M<.5){                                  // front face
   float flowv=fbm(vec3(u*30.-time*.8,h*8.,time*.5));
   col=heat(hue,mix(t*.55+.12*flowv,t+.15,crack))*(.75+.6*hot);
   col+=vec3(2.4)*sw;
 }else{                                     // sides and back: obsidian, lit by its own glow
   float rim=sq(1.-abs(dot(n,v)));
   col=lin(vec3(.03,.02,.05))+hue*.10*rim+heat(hue,.7)*crack*.25;
   col+=vec3(.6)*sw*rim;
 }
 // Molten seam where the letters meet the floor.
 col+=heat(hue,1.)*exp(-abs(W.y)*6.)*rise*.8;
 frag=vec4(col*logoI,1.);
}
