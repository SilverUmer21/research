#version 330 core
#include "common.glsl"
// blitzedo in glass: dark violet glass holding two layers of flowing prism lava veins (parallax depth),
// glowing hearts in the bowls, chrome-prism bevels, a crystallising fill front, a light sweep
// and a heartbeat that runs through every letter.
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
uniform float tnow,glassFill,sweepPos,beatP,heartWave;
uniform vec4 bowls[4];          // u, v (m) of the counters of b, e, d, o; w = on
vec2 cell(vec2 p,float tt){vec2 i=floor(p),f=fract(p);float d1=8.,d2=8.;
 for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec2 g=vec2(x,y);vec2 o=vec2(hash2(i+g),hash2(i+g+17.3));o=.5+.42*sin(tt*.7+6.28*o);
  float d=length(g+o-f);if(d<d1){d2=d1;d1=d;}else if(d<d2)d2=d;}
 return vec2(d1,d2-d1);}
float veins(vec2 q,float tt){
 vec2 w=q+vec2(fbm(vec3(q*.8,tt*.15)),fbm(vec3(q*.8+4.,tt*.15)))*1.4;
 vec2 c=cell(w*2.2+vec2(tt*.35,-tt*.12),tt);
 return 1.-smoothstep(0.,.07,c.y);
}
void main(){
 vec3 n=normalize(N);vec3 v=normalize(viewEye()-W);
 float u=U.x,h=U.y;
 // Crystallising fill: the glass grows in from the strokes, left to right.
 float edgeN=fbm(vec3(u*1.7,h*1.7,3.));
 float fill=glassFill*16.5-(u+edgeN*1.6);
 if(fill<0.)discard;
 float front=exp(-fill*fill*5.);
 vec3 r=reflect(-v,n);float F=.04+.96*pow(1.-max(dot(n,v),0.),5.);
 vec3 env=mix(lin(vec3(.05,.02,.09)),toRed(ring(r.y*.4+r.z*.05+time*.05),r.y)*.9,smoothstep(-.2,.6,r.y))+toRed(ring(r.z*.08-time*.1),r.z*.1)*sq(max(-r.y,0.))*.6;
 float spec=pow(max(dot(r,normalize(vec3(-.6,.7,.3))),0.),60.);
 float sweep=exp(-sq((u+h*.55-sweepPos)/.45))*pow(max(dot(r,normalize(vec3(-1.,.2,0.))),0.),3.);
 vec3 col;
 // Two lava layers seen through the glass at different depths.
 vec2 Q=vec2(u,h);vec2 par=vec2(v.z,v.y)/max(.25,-v.x);
 float v1=veins(Q+par*.12,time),v2=veins(Q*1.6+par*.34+7.,time*1.3);
 vec3 hue1=toRed(ring(u*.06+h*.08-time*.22+fbm(vec3(Q,time*.2))*.3),u*.09+h*.1-time*.3),hue2=toRed(ring(u*.06+.33-time*.18),u*.05+.4-time*.2);
 float pulse=1.+.8*beatP+1.6*heartWave*exp(-sq((u-(tnow-3.05)*14.)/1.5));
 float body=fbm(vec3(Q*.9+par*.5,time*.25));
 float cool=1.-.3*brandRed;
 vec3 lava=heat(hue1,(.42+.3*v1)*cool)*v1*1.25*pulse+heat(hue2,.40*cool)*v2*.5*pulse+heat(toRed(ring(u*.05-time*.12+body),body+u*.03),.30)*smoothstep(.45,.8,body)*.55;
 float hearts=0.;
 for(int i=0;i<4;i++){float d=length(Q-bowls[i].xy);hearts+=exp(-d*d*6.)*bowls[i].w;}
 lava+=heat(toRed(ring(time*.3+u*.05),time*.2),.8)*hearts*(.6+.8*beatP+heartWave);
 if(M<.5||M>2.5){                           // front and back faces: glass over lava
   col=mix(lin(vec3(.03,.01,.06)),lin(vec3(.06,.0,.01)),brandRed)+lava*(.85-F*.4)+env*F*1.2+vec3(1.)*spec*.9;
   col+=RED(u*.05+h*.12-time*.15)*(.30+.25*body+.35*beatP)*brandRed;   // the letters glow red from within
 }else if(M<1.5){                           // bevel: chrome that reflects the prism world
   col=toRed(ring(dot(r,vec3(.2,.9,.3))*.6+u*.04-time*.25),dot(r,vec3(.2,.9,.3))+u*.03)*(1.2+2.2*F)*.9+vec3(1.)*spec*2.;
 }else{                                     // sides: deep glass, lava glimpsed edge-on
   col=lin(vec3(.02,.01,.04))+lava*.35+env*F*.9;
 }
 col+=mix(vec3(1.),lin(vec3(1.,.55,.5)),brandRed)*.75*sweep*(M<1.5?2.2:1.);
 col+=heat(vec3(1.,.8,1.),1.)*front*1.5;
 float fog=smoothstep(30.,80.,length(eye-W));col=mix(col,sky(gl_FragCoord.xy/resolution),fog);
 frag=vec4(col,1.);
}
