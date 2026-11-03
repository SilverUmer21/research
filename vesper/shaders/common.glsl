// VESPER magenta cut: shared uniforms, colour science and noise.
uniform float time,charge,boost,reflectionPass,lavaKind,flowPhase,fillFront,drainFront,heartI,lampI,speed,travel,flash,board,cool;
uniform vec3 eye,lightDir;
uniform mat4 carFrame,carInverse;
uniform vec2 resolution;
const float PI=3.14159265359;
vec3 lin(vec3 c){return mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
vec3 srgb(vec3 c){return mix(c*12.92,1.055*pow(max(c,0.),vec3(1./2.4))-.055,step(vec3(.0031308),c));}
float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
float hash2(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise3(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);}
float fbm(vec3 p){float a=.5,s=0.;for(int i=0;i<4;i++){s+=a*noise3(p);p=p*2.03+vec3(1.7,9.2,3.1);a*=.5;}return s;}
// Magenta "blackbody": a temperature ramp that stays in the Vesper family.
// 0 cold crust, .25 deep violet, .5 magenta, .75 hot pink, 1 white-hot.
vec3 magma(float t){
 t=clamp(t,0.,1.2);
 vec3 c0=lin(vec3(.035,.006,.06)),c1=lin(vec3(.32,.03,.62)),c2=lin(vec3(1.,.06,.62)),c3=lin(vec3(1.,.42,.86)),c4=lin(vec3(1.,.90,1.));
 vec3 c=t<.25?mix(c0,c1,t/.25):t<.5?mix(c1,c2,(t-.25)/.25):t<.75?mix(c2,c3,(t-.5)/.25):mix(c3,c4,min(1.,(t-.75)/.25));
 return c*(.35+2.4*t*t);
}
vec3 energyColor(){return lin(vec3(1.,.045,.55));}
vec3 boosterColor(){return lin(vec3(.71,.05,1.));}
vec3 keyColor(){return lin(vec3(.88,.70,1.))*1.45;}
vec3 shadowColor(){return lin(vec3(.31,.06,.43))*1.20;}
vec3 sky(vec2 uv){float q=smoothstep(0.,1.,length(uv-vec2(.30,.62)));return mix(lin(vec3(.040,.018,.070)),lin(vec3(.005,.004,.014)),q);}
vec3 viewEye(){return reflectionPass>.5?eye*vec3(1,-1,1):eye;}
vec3 localPoint(vec3 p){return (carInverse*vec4(p,1.)).xyz;}
vec3 worldPoint(vec3 p){return (carFrame*vec4(p,1.)).xyz;}
