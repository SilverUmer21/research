#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
uniform sampler2D shadowmap,reflectionMap;
void main(){
 vec3 v=normalize(eye-W);vec3 s=L.xyz/L.w*.5+.5;float sh=0.;
 for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)sh+=step(texture(shadowmap,s.xy+vec2(x,y)*2.8/3072.).r,s.z-.0006);sh/=9.;
 vec2 uv=gl_FragCoord.xy/resolution;vec3 reflected=vec3(0.);
 for(int k=0;k<5;k++){float a=float(k)*1.256637;reflected+=texture(reflectionMap,uv+vec2(cos(a),sin(a))*.0014).rgb/5.;}
 float fr=pow(1.-abs(v.y),4.);
 vec3 base=lin(vec3(.027,.033,.052));vec3 col=base*(.8-sh*.6);
 col+=reflected*(.12+fr*.19);
 for(int j=0;j<3;j++){
   if(sceneMode<.5&&j>0)continue;
   float th=sceneMode>.5?float(j):theme;vec2 c=sceneMode>.5?vec2((float(j)-1.)*.1,(float(j)-1.)*3.4):vec2(0.);
   float cabin=exp(-length(W.xz-c-vec2(-.24,0.))*2.4);col+=energy(th)*cabin*.030;
   for(int i=0;i<2;i++){
     vec2 q=W.xz-c-vec2(-3.1,(float(i)*2.-1.)*.53);float p=exp(-q.x*q.x*.35-q.y*q.y*9.);
     vec3 bc=th<.5?lin(vec3(1.,.40,.035)):(th<1.5?lin(vec3(.05,.38,1.)):lin(vec3(.7,.05,1.)));
     col+=bc*p*(sceneMode>.5?.025:boost)*.09;
   }
 }
 col=mix(col,sky(uv),smoothstep(9.,45.,length(eye-W))*.90);frag=vec4(col,1.);
}
