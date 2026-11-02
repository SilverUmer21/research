"""Export all three original cars with static emissive veins and booster hardware."""
import json,struct
from pathlib import Path
import numpy as np
from showcase import World,Mesh,atlas,ROOT
from styles import STYLES

def capture(mesh,gl):
    mesh.count=len(mesh.data);mesh.export_data=np.asarray(mesh.data,dtype=np.float32)
Mesh.upload=capture

def export(variant):
    atlas();world=World(None,variants=(variant,));blob=bytearray();views=[];accessors=[];materials=[];gmeshes=[];nodes=[];ids={}
    def buf(data,target=None):
        while len(blob)%4:blob.append(0)
        off=len(blob);blob.extend(data);v={'buffer':0,'byteOffset':off,'byteLength':len(data)}
        if target:v['target']=target
        views.append(v);return len(views)-1
    def acc(a,kind,position=False):
        a=np.asarray(a,dtype='<f4');v=buf(a.tobytes(),34962);item={'bufferView':v,'componentType':5126,'count':len(a),'type':kind}
        if position:item.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        accessors.append(item);return len(accessors)-1
    iv=buf((ROOT/'atlas.png').read_bytes())
    for name,mesh in world.meshes.items():
        if not mesh.hero or not len(mesh.export_data):continue
        tri=mesh.export_data.reshape(-1,3,12);groups={}
        for i,row in enumerate(tri[:,0]):
            em=round(float(row[9]),3)
            if name=='veins':key=('vein',)
            elif row[10]>=0:key=('label',)
            elif em>.1:key=('emissive',em,*np.round(row[6:9],4))
            else:key=('metal' if em<-.5 else 'paint',)
            groups.setdefault(key,[]).append(i)
        prim=[]
        for key,which in groups.items():
            v=tri[which].reshape(-1,12);pbr={'baseColorFactor':[1,1,1,1],'metallicFactor':.55 if key[0]=='metal' else 0.,'roughnessFactor':.33 if key[0]=='metal' else .46}
            mat={'name':name+' / '+key[0],'pbrMetallicRoughness':pbr,'doubleSided':True}
            attrs={'POSITION':acc(v[:,:3],'VEC3',True),'NORMAL':acc(v[:,3:6],'VEC3')}
            if name=='glass':pbr.update(baseColorFactor=[.65,.70,.92,.20],metallicFactor=0.,roughnessFactor=.12);mat['alphaMode']='BLEND'
            if key[0]=='label':
                pbr['baseColorTexture']={'index':0};uv=v[:,10:12].copy();uv[:,1]=1-uv[:,1];attrs['TEXCOORD_0']=acc(uv,'VEC2')
            else:
                c=v[:,6:9];c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);attrs['COLOR_0']=acc(c,'VEC3')
            if key[0] in ('emissive','vein'):
                c=v[0,6:9];c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);c=c/max(float(c.max()),.001)
                mat['emissiveFactor']=c.tolist();mat['extensions']={'KHR_materials_emissive_strength':{'emissiveStrength':2.0 if key[0]=='vein' else float(key[1])}}
                if key[0]=='vein':attrs['TEXCOORD_0']=acc(v[:,10:12],'VEC2');mat['extras']={'flowCoordinates':'UV.x is distance along the artery; UV.y is its cross-section. Animated shader supplied in shaders/vein.frag.'}
            materials.append(mat);prim.append({'attributes':attrs,'material':len(materials)-1,'mode':4})
        ids[name]=len(gmeshes);gmeshes.append({'name':name,'primitives':prim})
    objects,*_=world.objects(0.,variant=variant)
    for i,(m,M) in enumerate(objects):
        if m.hero and m.name in ids:nodes.append({'name':m.name+'_'+str(i),'mesh':ids[m.name],'matrix':M.T.flatten().tolist()})
    name=STYLES[variant]['name']
    d={'asset':{'version':'2.0','generator':'Original Blitzedo AFTERLIGHT '+name},'extensionsUsed':['KHR_materials_emissive_strength'],'scene':0,'scenes':[{'name':name,'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':gmeshes,'materials':materials,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(blob)}],'images':[{'bufferView':iv,'mimeType':'image/png'}],'textures':[{'source':0,'sampler':0}],'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}]}
    j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);blob.extend(b'\0'*((-len(blob))%4))
    b=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
    p=ROOT/'models'/f'{name}.glb';p.write_bytes(b);print('EXPORTED',name,len(b),'bytes',len(nodes),'parts',flush=True)
if __name__=='__main__':
    (ROOT/'models').mkdir(exist_ok=True)
    for v in range(3):export(v)
