"""Three related hypercar designs, each with its own body and energy palette."""
import numpy as np
from engine import color,lerp
STYLES=[
 {'name':'CINDER','width':1.05,'dark':'#10141c','paint':'#434b57','metal':'#74523b','vein':'#ff6417','head':'#ffcf7d','tail':'#ff224b','core':'#ff7c16'},
 {'name':'GLACIER','width':.985,'dark':'#24394b','paint':'#d3e3ed','metal':'#5a929d','vein':'#29eddf','head':'#7dffeb','tail':'#a22bff','core':'#1ee8ee'},
 {'name':'VESPER','width':1.025,'dark':'#170c26','paint':'#795b95','metal':'#9d3e82','vein':'#ff25ba','head':'#c2a0ff','tail':'#ff7f25','core':'#ed27cd'}
]
def recolor(mesh,style):
 p=STYLES[style]
 role={'veins':'vein','frontlava':'head','taillava':'tail','plasma':'core','boostercore':'head','lavachannels':'vein'}
 if mesh.name in role:
  for row in mesh.data:row[6:9]=list(color(p[role[mesh.name]]))
  return
 if mesh.name in ('veinBeds','blaze','jets','boostSparks','floor'):return
 for row in mesh.data:
  if row[10]>=0:continue
  c=np.asarray(row[6:9]);value=float(max(c))
  if row[9]>.1:
   row[6:9]=list(color(p['vein']));continue
  if value<.14:continue
  if c[2]>c[0]*1.13 and c[2]>c[1]*1.06:
   q=np.clip((value-.09)/.72,0,1)**(.95 if style!=1 else .8)
   row[6:9]=lerp(color(p['dark']),color(p['paint']),q).tolist()
  elif c[0]>c[1]*1.30:
   row[6:9]=list(color(p['metal']))
