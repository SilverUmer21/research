#version 330 core
#include "common.glsl"
in vec3 W;in float M;
void main(){if(M>.1)discard;if(hero>.5&&phase>.001&&field(W-origin)<phase)discard;}
