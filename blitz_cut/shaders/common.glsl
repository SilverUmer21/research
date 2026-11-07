// THE HIJACK: shared uniforms, prism colour science, noise, dissolve.
uniform float time,charge,boost,reflectionPass,lavaKind,flowPhase,fillFront,drainFront,heartI,lampI,flash,cool,alive,dissolve,desat,logoI;
uniform vec3 eye,lightDir,mixW,ownGlow;
uniform vec2 fronts;          // x: cyan present where local x > fronts.x; y: orange present where local x < fronts.y
uniform mat4 carFrame,carInverse;
uniform vec2 resolution;
const float PI=3.14159265359;
float sq(float x){return x*x;}
vec3 lin(vec3 c){return mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
vec3 srgb(vec3 c){return mix(c*12.92,1.055*pow(max(c,0.),vec3(1./2.4))-.055,step(vec3(.0031308),c));}
float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
float hash2(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise3(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);}
float fbm(vec3 p){float a=.5,s=0.;for(int i=0;i<4;i++){s+=a*noise3(p);p=p*2.03+vec3(1.7,9.2,3.1);a*=.5;}return s;}
// The three energies of the series, and the prism ring that mixes them.
vec3 MAG(){return lin(vec3(1.,.04,.58));}
vec3 CYA(){return lin(vec3(.02,.90,1.));}
vec3 ORA(){return lin(vec3(1.,.36,.02));}
vec3 ring(float n){
 // magenta -> violet -> cyan -> lime -> orange -> red -> magenta
 n=fract(n)*6.;
 vec3 c[7];c[0]=MAG();c[1]=lin(vec3(.42,.10,1.));c[2]=CYA();c[3]=lin(vec3(.45,1.,.12));c[4]=ORA();c[5]=lin(vec3(1.,.06,.12));c[6]=MAG();
 int i=int(floor(n));float f=smoothstep(0.,1.,fract(n));
 vec3 a=c[0],b=c[1];
 for(int k=0;k<6;k++){if(k==i){a=c[k];b=c[k+1];}}
 return mix(a,b,f);
}
// Colour of energy at band position n for the energies present (w = magenta, cyan, orange).
vec3 prism(float n,vec3 w){
 float s=w.x+w.y+w.z;if(s<.001)return MAG();
 float bm=pow(.5+.5*cos(2.*PI*n),3.)*w.x,bc=pow(.5+.5*cos(2.*PI*(n-.333)),3.)*w.y,bo=pow(.5+.5*cos(2.*PI*(n-.667)),3.)*w.z;
 vec3 sep=(MAG()*bm+CYA()*bc+ORA()*bo)/max(bm+bc+bo,.0001);
 float all3=min(w.x,min(w.y,w.z));
 return mix(sep,ring(n),all3*.85);
}
vec3 avgEnergy(vec3 w){float s=w.x+w.y+w.z;return s<.001?MAG():(MAG()*w.x+CYA()*w.y+ORA()*w.z)/s;}
// Temperature for any hue: crust, deep, hue, hot, white-hot.
vec3 heat(vec3 h,float t){
 t=clamp(t,0.,1.2);
 vec3 c0=h*.02+lin(vec3(.03,.008,.05)),c1=h*.30,c2=h,c3=mix(h,vec3(1.),.42),c4=mix(h,vec3(1.),.86);
 vec3 c=t<.25?mix(c0,c1,t/.25):t<.5?mix(c1,c2,(t-.25)/.25):t<.75?mix(c2,c3,(t-.5)/.25):mix(c3,c4,min(1.,(t-.75)/.25));
 return c*(.35+2.4*t*t);
}
vec3 keyColor(){return lin(vec3(.86,.74,1.))*1.35;}
vec3 shadowColor(){return lin(vec3(.26,.07,.40))*1.15;}
vec3 sky(vec2 uv){float q=smoothstep(0.,1.,length(uv-vec2(.30,.62)));return mix(lin(vec3(.036,.016,.066)),lin(vec3(.004,.003,.012)),q);}
vec3 viewEye(){return reflectionPass>.5?eye*vec3(1,-1,1):eye;}
vec3 localPoint(vec3 p){return (carInverse*vec4(p,1.)).xyz;}
vec3 worldPoint(vec3 p){return (carFrame*vec4(p,1.)).xyz;}
// Energies present at a car-local point (the steal floods in from the nose and the tail).
vec3 localMix(vec3 lp){return vec3(mixW.x,mixW.y*step(fronts.x,lp.x),mixW.z*step(lp.x,fronts.y));}
// Capture dissolve: returns -1 to discard, else edge glow amount.
float dissolveEdge(vec3 lp){
 if(dissolve<=0.)return 0.;
 float n=fbm(lp*2.6+vec3(0.,dissolve*.3,0.))*.85+.15*(1.-clamp((lp.y-.2)/1.5,0.,1.));
 float th=dissolve*1.15;
 if(n<th)return -1.;
 return 1.-smoothstep(0.,.06,n-th);
}
