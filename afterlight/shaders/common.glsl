uniform float time,phase,charge,hero,warm,boost,brake,reflectionPass,lavaKind,theme,sceneMode;
uniform vec3 eye,origin,lightDir;
uniform mat4 carFrame,carInverse;
uniform vec2 resolution;
const float PI=3.14159265359;
vec3 lin(vec3 c){return mix(c/12.92,pow((c+.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
vec3 srgb(vec3 c){return mix(c*12.92,1.055*pow(max(c,0.),vec3(1./2.4))-.055,step(vec3(.0031308),c));}
float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
float noise3(vec3 p){vec3 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);}
float field(vec3 p){return 1.;}
vec3 viewEye(){return reflectionPass>.5?eye*vec3(1,-1,1):eye;}
vec3 localPoint(vec3 p){return (carInverse*vec4(p,1.)).xyz;}
vec3 worldPoint(vec3 p){return (carFrame*vec4(p,1.)).xyz;}
vec3 energy(float t){if(t<.5)return lin(vec3(1.,.22,.025));if(t<1.5)return lin(vec3(.025,.92,.79));return lin(vec3(1.,.045,.55));}
vec3 energyColor(){return energy(theme);}
vec3 keyColor(){if(theme<.5)return lin(vec3(1.,.89,.78))*1.48;if(theme<1.5)return lin(vec3(.76,.9,1.))*1.40;return lin(vec3(.88,.70,1.))*1.50;}
vec3 shadowColor(){if(theme<.5)return lin(vec3(.32,.16,.29))*1.20;if(theme<1.5)return lin(vec3(.18,.24,.49))*1.20;return lin(vec3(.31,.06,.43))*1.20;}
vec3 sky(vec2 uv){float q=smoothstep(0.,.95,length(uv-vec2(.32,.45)));return mix(lin(vec3(.028,.035,.07)),lin(vec3(.004,.006,.016)),q);}
