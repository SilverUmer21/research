"""Original low-slung coupe, with separate wheels, glass and exposed cabin plasma."""
import math
import numpy as np
from engine import trans,rot,scale,color,lerp,smooth,normalize

def build_car(mesh,ellipsoid,torus,wire,transform_new,style=0):
    body=mesh('shell',True);inside=mesh('interior',True);glow=mesh('filament',True)
    lamps=mesh('frontlava',True);tails=mesh('taillava',True);channels=mesh('lavachannels',True);glass=mesh('glass',True);plasma=mesh('plasma',True)
    # Long wedge profile, faceted shoulders and a distinct hood/trunk.
    sections=[(-2.28,.88,.35,.80),(-1.95,.99,.31,.90),(-1.32,.94,.30,.94),(-.55,.88,.30,.91),(.40,.86,.30,.91),(1.30,.94,.32,.84),(1.98,.94,.37,.73),(2.28,.82,.41,.65)]
    rings=[]
    for x,w,b,t in sections:
        rings.append([(x,t+.025,0),(x,t,w*.65),(x,t-.075,w*.96),(x,b+.13,w),(x,b,w*.81),(x,b,-w*.81),(x,b+.13,-w),(x,t-.075,-w*.96),(x,t,-w*.65)])
    for j in range(len(rings)-1):
        for k in range(9):
            kk=(k+1)%9;c=['#5258b8','#394ba3','#22336b','#101b33','#0c152b','#101b33','#22336b','#394ba3','#5258b8'][k]
            body.face([rings[j][k],rings[j+1][k],rings[j+1][kk],rings[j][kk]][::-1],c)
    body.face(rings[0][::-1],'#253763');body.face(rings[-1],'#3b4e93')
    body.box((0,.28,0),(4.25,.14,1.72),'#080f22',.055)
    # Real wheel openings and separate layered fender lips.
    for xx in (-1.38,1.38):
        for side in (-1,1):
            st=len(body.data);body.torus((xx,.45,side*.98),.475,.070,'#4a5bac',axis='z',n=40,m=10,start=.03,end=math.pi-.03)
            for row in body.data[st:]:row[9]=-.8
            st=len(body.data);body.torus((xx,.45,side*1.055),.485,.015,'#ed419c',axis='z',n=40,m=8,start=.07,end=math.pi-.07)
            for row in body.data[st:]:row[9]=-.7
    # Wide, closed fender shells: annular side faces and a curved top surface.
    for xx in (-1.38,1.38):
        for side in (-1,1):
            for k in range(32):
                a=.045+k*(math.pi-.09)/32;b=.045+(k+1)*(math.pi-.09)/32
                def fp(rad,t,z):return (xx+rad*math.cos(t),.44+rad*math.sin(t),side*z)
                body.face(([fp(.464,a,1.115),fp(.563,a,1.115),fp(.563,b,1.115),fp(.464,b,1.115)])[::side],'#394e9c')
                start=len(body.data)
                body.face(([fp(.563,a,.78),fp(.563,b,.78),fp(.563,b,1.115),fp(.563,a,1.115)])[::side],'#4b5db6')
                for row in body.data[start:]:row[3:6]=normalize((row[0]-xx,row[1]-.44,0)).tolist()
                body.face(([fp(.464,a,.78),fp(.464,a,1.115),fp(.464,b,1.115),fp(.464,b,.78)])[::side],'#101b36')
    body.surface_data=[row.copy() for row in body.data]
    # Sculpted rocker panels, door creases and hot side vents.
    for side in (-1,1):
        body.box((-.02,.40,side*.94),(2.0,.17,.18),'#111d40',.045)
        wire(body,[(-1.12,.88,side*.93),(-.76,.57,side*.96),(.55,.57,side*.93),(.80,.86,side*.88)],.011,'#0b1535')
        body.box((-.18,.79,side*.945),(.28,.035,.028),'#95b7ed',.01)
        for j in range(4):body.box((-.94+j*.15,.71,side*.976),(.062,.19,.035),'#081125',.014)
        # Race mirror and its stem, attached to the A-pillar.
        wire(body,[(.45,1.02,side*.77),(.50,1.05,side*1.11)],.028,'#253b71')
        body.box((.52,1.07,side*1.15),(.25,.12,.20),'#5b6ac5',.045)
        wire(glow,[(.59,1.075,side*1.20),(.44,1.075,side*1.20)],.008,'#41fff0',mat=.55)
    # Front: a low splitter, dark intake and sharply segmented light signatures.
    body.box((2.23,.50,0),(.19,.24,1.69),'#0a1530',.055)
    body.box((2.34,.37,0),(.25,.085,1.96),'#172448',.025)
    for yy in (.46,.51,.56):body.box((2.337,yy,0),(.024,.012,1.30),'#273553',.004)
    for side in (-1,1):
        wire(lamps,[(2.315,.66,side*.24),(2.32,.68,side*.71),(2.22,.76,side*.82)],.019,'#26dcff',mat=2.6)
        lamps.box((2.325,.688,side*.49),(.028,.083,.49),'#1eb9ff',.014,em=2.6)
        wire(glow,[(2.33,.42,side*.30),(2.33,.42,side*.74)],.009,'#ff4d9f',mat=.7)
        # Hood seams and thin laser traces follow the body contour.
    # Rear diffuser and a proper aero wing on two supports.
    body.box((-2.30,.54,0),(.13,.24,1.72),'#0a1129',.03)
    for z in (-.64,-.32,0,.32,.64):body.box((-2.37,.33,z),(.31,.17,.035),'#0b1730',.008)
    for side in (-1,1):
        body.box((-2.02,1.00,side*.65),(.13,.34,.08),'#172442',.022)
        body.box((-2.20,1.18,side*1.20),(.52,.30,.045),'#3c498d',.016)
        wire(tails,[(-2.354,.80,side*.15),(-2.354,.80,side*.78)],.019,'#ff238c',mat=2.6)
        tails.box((-2.366,.795,side*.49),(.035,.086,.55),'#f02fbb',.014,em=2.6)
    body.box((-2.16,1.17,0),(.48,.09,2.42),'#4859ab',.035)
    wire(glow,[(-2.375,1.19,-1.15),(-2.375,1.19,1.15)],.008,'#f63ca2',mat=.40)
    for side in (-1,1):
        for z in (.30,.47,.64):
            body.box((-2.389,.795,side*z),(.012,.085,.014),'#10162c',.004)
            body.box((2.344,.688,side*z),(.009,.081,.010),'#131d35',.003)
    # Four separated panes expose the plasma cabin. There is no opaque bubble.
    rear=(-1.27,.95);rearTop=(-.86,1.57);frontTop=(.02,1.57);front=(.68,.94)
    for side in (-1,1):
        pts=[(rear[0],rear[1],side*.80),(rearTop[0],rearTop[1],side*.64),(frontTop[0],frontTop[1],side*.64),(front[0],front[1],side*.77)]
        glass.face(pts if side==1 else pts[::-1],'#476da4',em=-3)
        wire(body,[*pts,pts[0]],.033,'#17274a')
        wire(body,[(-.72,.97,side*.80),(-.68,1.57,side*.64)],.018,'#263765')
    # Slightly curved windshield strips, so the highlight rolls across the glass.
    for j in range(12):
        z0=-.77+j*1.54/12;z1=-.77+(j+1)*1.54/12
        def wind(z,top):
            if top:return (.02+.055*(z/.77)**2,1.57-.025*(z/.77)**2,z*.64/.77)
            return (.68-.035*(z/.77)**2,.94,z)
        glass.face([wind(z0,False),wind(z1,False),wind(z1,True),wind(z0,True)],'#426ca8',em=-3)
    glass.face([(-1.27,.95,-.80),(-.86,1.57,-.64),(-.86,1.57,.64),(-1.27,.95,.80)],'#4866ac',em=-3)
    glass.face([(-.86,1.57,-.64),(.02,1.57,-.64),(.02,1.57,.64),(-.86,1.57,.64)],'#39548d',em=-3)
    for side in (-1,1):
        wire(glow,[(-1.25,.955,side*.79),(-.85,1.58,side*.65),(.01,1.58,side*.65),(.67,.95,side*.78)],.0085,'#a056ff',mat=.64)
    # A solid rear roof section gives the glazing a proper coupe silhouette.
    body.box((-.67,1.595,0),(.48,.065,1.32),'#3b4e93',.025)
    body.box((-.21,1.595,0),(.45,.045,.085),'#233966',.018)
    wire(glow,[(-.89,1.624,-.61),(-.89,1.624,.61)],.006,'#4bfbe1',mat=.40)
    # Cabin architecture: two dark seat silhouettes and a central suspended reactor.
    inside.box((-.38,.96,0),(1.65,.065,1.28),'#111729',.025)
    for side in (-1,1):
        inside.box((-.70,1.08,side*.46),(.38,.24,.30),'#221833',.045)
        inside.box((-.88,1.27,side*.46),(.12,.43,.30),'#301939',.045)
        wire(inside,[(-.90,1.37,side*.58),(-.90,1.09,side*.58),(-.65,1.01,side*.58)],.018,'#d94c73')
    inside.box((.39,1.01,0),(.28,.14,1.20),'#15253e',.035)
    torus(inside,(.19,1.17,.43),.118,.014,'#754b79',axis='x',mat=-1,n=28)
    for a in (0,2.1,4.2):wire(inside,[(.19,1.17,.43),(.19,1.17+math.cos(a)*.1,.43+math.sin(a)*.1)],.009,'#8b6a98')
    glow.box((.35,1.15,.41),(.026,.065,.15),'#50e8ff',.007,em=.5)
    wire(glow,[(.41,1.09,-.56),(.41,1.09,.56)],.012,'#ff6629',mat=1.2)
    for xx in (-.54,.08):
        torus(inside,(xx,1.24,0),.25,.022,'#67345b',axis='x',mat=-1,n=40)
    ellipsoid(plasma,(-.24,1.23,0),(.43,.24,.23),'#ff5b17',mat=2.6,n=48,ny=24)
    # Three twisting conductive paths are visible through the windscreen and roof.
    for k in range(3):
        pts=[(-.63+j*.0076,1.23+.185*math.cos(j*.10+k*math.pi*2/3),.19*math.sin(j*.10+k*math.pi*2/3)) for j in range(105)]
        wire(plasma,pts,.012,'#ffb745',mat=2.6)
    for side in (-1,1):
        wire(plasma,[(-1.12,.995,side*.60),(-.63,1.47,side*.49),(-.11,1.45,side*.48),(.45,1.07,side*.62)],.007,'#ff7f23',mat=2.6)
    # Interior sill light and real inlaid brand plaque.
    for side in (-1,1):
        wire(glow,[(-1.15,.974,side*.69),(.48,.974,side*.69)],.011,'#ff3d28',mat=1.35)
    body.box((-.12,.713,.980),(.80,.108,.010),'#111823',.012)
    body.label((-.12,.713,.989),.74,.085,'brand')
    body.box((.66,.60,.975),(.17,.13,.010),'#111823',.010)
    body.label((.66,.60,.984),.13,.105,'number'+str(style))
    # Reusable tire + turbine rim assembly. Rotation is driven by distance/radius.
    wheel=mesh('wheel',True)
    wheel.cylinder((0,0,0),.397,.29,'#080d1b',axis='z',n=48)
    for side in (-1,1):
        torus(wheel,(0,0,side*.105),.352,.083,'#0b1121',axis='z',mat=-.25,n=56)
        wheel.cylinder((0,0,side*.168),.287,.022,'#17223e',axis='z',n=40)
        torus(wheel,(0,0,side*.187),.261,.016,'#7384cb',axis='z',mat=-1,n=48)
        torus(wheel,(0,0,side*.190),.234,.008,'#52dcca',axis='z',mat=.48,n=48)
        wheel.cylinder((0,0,side*.193),.082,.028,'#a2b5dd',axis='z',n=24)
        for k in range(7):
            ang=k*2*math.pi/7
            wheel.box((.145,0,side*.189),(.25,.042,.026),'#525d9f',.012,M=rot(ang+.2,'z'))
    for k in range(36):
        a=k*2*math.pi/36
        wheel.box((.407,0,0),(.024,.042,.21),'#11182b',.008,M=rot(a,'z'))
    # Solid flying buttresses make the roof and rear quarter one sculpted form.
    for side in (-1,1):
        z=lambda q:side*q
        A=(-.88,1.57,z(.64));B=(-1.72,.96,z(.85));C=(-1.45,.93,z(.97));D=(-.74,1.56,z(.70))
        body.face([A,B,C,D][::side],'#34468b')
        body.face([D,C,(-1.31,.91,z(.86)),(-.71,1.51,z(.61))][::side],'#18264c')
        # Black recessed side scoop with a sharp painted surround.
        scoop=[(-.88,.70,z(.953)),(-.55,.79,z(.956)),(.42,.56,z(.960)),(.19,.43,z(.968))]
        body.face(scoop[::-side],'#080d17')
        wire(body,[scoop[0],scoop[1],scoop[2]],.021,'#5868a7')
        for j in range(3):
            body.box((-.57+j*.19,.602-j*.033,z(.970)),(.12,.023,.035),'#273953',.006)
        # A pair of canards and a deep front splitter give the nose real aero layers.
        for j in range(2 if style!=1 else 1):
            x=1.95-j*.11;y=.44+j*.12
            pts=[(x+.38,y,z(.78)),(x+.24,y+.025,z(1.13)),(x-.19,y+.055,z(1.08)),(x-.10,y+.025,z(.80))]
            body.face(pts[::-side],'#233454');body.face([(xx,yy-.025,zz) for xx,yy,zz in pts][::side],'#0b1425')
            wire(body,[pts[1],pts[2]],.009,'#91a0c9')
        # Physical fender louvers, each sitting in a dark recess.
        for xx in (-1.38,1.38):
            for j in range(3 if style==1 else 4):
                a=.65+j*.18;px=xx+.571*math.cos(a);py=.44+.571*math.sin(a)
                body.box((px,py,z(.93)),(.080,.018,.22),'#0b1326',.006,M=trans(px,py,z(.93))@rot(a-math.pi/2,'z')@trans(-px,-py,-z(.93)))
    # A raised central bonnet spine and paired NACA-like vent pockets.
    body.face([(.73,.960,0),(1.88,.787,0),(1.68,.825,.15),(.84,.953,.17)][::-1],'#4759a5')
    body.face([(.73,.960,0),(.84,.953,-.17),(1.68,.825,-.15),(1.88,.787,0)][::-1],'#344991')
    if style==0:
        # Cinder: a higher double-element track wing.
        body.box((-2.02,1.29,0),(.23,.055,2.30),'#374778',.018)
    elif style==2:
        # Vesper: a dorsal fin and tall swept endplates.
        for side in (-1,1):
            body.face([(-.72,1.61,side*.055),(-1.52,1.12,side*.055),(-1.78,1.31,side*.055),(-.85,1.83,side*.055)][::-side],'#3b3979')
            body.face([(-2.38,1.13,side*1.22),(-2.40,1.47,side*1.22),(-1.91,1.25,side*1.22),(-1.90,1.10,side*1.22)][::-side],'#32306a')
    # Lower, longer greenhouse and distinct aero proportions for each sibling.
    width=[1.05,.985,1.025][style];extension=[.16,-.035,.23][style]
    for data in [part.data for part in (body,inside,glow,lamps,tails,channels,glass,plasma,wheel)]+[body.surface_data]:
        for row in data:
            x,y,z=row[:3]
            if x>1.75:x+=extension*(x-1.75)/.60
            if y>.96:y=.96+(y-.96)*.84
            if x<-1.80 and y>.86:y=.86+(y-.86)*[1.26,.76,1.08][style]
            row[:3]=[x,y,z*width]
            # Correct normals for the longitudinal and vertical deformation.
            sx=1.+extension/.60 if row[0]>1.75 else 1.;sy=.84 if row[1]>.96 else 1.
            row[3:6]=normalize(np.asarray(row[3:6])/np.array([sx,sy,width])).tolist()
    return body,inside,wheel

