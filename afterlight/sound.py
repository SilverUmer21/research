"""Original studio-car score and synchronized electric booster sound design."""
from pathlib import Path
import wave
import numpy as np
ROOT=Path(__file__).resolve().parent;SR=48000
rng=np.random.default_rng(803);out=np.zeros((30*SR,2),np.float64)
def add(t,s,vol=1.,pan=0.):
 i=round(t*SR);n=min(len(s),len(out)-i)
 if n<=0:return
 x=np.asarray(s[:n])*vol;p=np.clip(pan,-1,1)
 out[i:i+n,0]+=x*np.sqrt((1-p)*.5);out[i:i+n,1]+=x*np.sqrt((1+p)*.5)
def tone(hz,d=1.7):
 q=np.arange(round(d*SR))/SR
 s=np.sin(2*np.pi*hz*q)*np.exp(-q*2.4)+.18*np.sin(2*np.pi*hz*2.003*q)*np.exp(-q*5.)
 return s*(1-np.exp(-q*150))*np.minimum((d-q)/.09,1)
def note(t,hz,v=.07,pan=0.):
 s=tone(hz);add(t,s,v,pan);add(t+.285,s,v*.16,-pan)
def pad(t,d,notes,v):
 q=np.arange(round(d*SR))/SR;e=np.minimum(q/1.4,1)*np.minimum((d-q)/1.5,1)
 for k,hz in enumerate(notes):
  s=np.sin(2*np.pi*hz*q)+.26*np.sin(2*np.pi*hz*1.002*q+k*.4)+.12*np.sin(2*np.pi*hz*2*q)
  add(t,s*e,v/len(notes),(-.45 if k%2 else .45))
def hit(t,v=.2,hz=55.):
 q=np.arange(round(.8*SR))/SR
 s=np.sin(2*np.pi*(hz*q+1.3*(1-np.exp(-q*30))))*np.exp(-q*8)
 s+=rng.normal(size=len(q))*.11*np.exp(-q*95);add(t,s,v)
def air(t,d,v,pan=0.,rise=False):
 q=np.arange(round(d*SR))/SR;n=rng.normal(size=len(q))
 lo=np.convolve(n,np.ones(29)/29,'same');hi=np.convolve(n,np.ones(5)/5,'same')-lo
 e=(q/d)**1.6 if rise else np.sin(np.pi*q/d)**1.5
 add(t,(lo*.7+hi*.28)*e,v,pan)
# A repeated nine-second reveal gives each car its own ignition and timbre.
from showcase import boost_at
for variant,start in enumerate((0.,9.,18.)):
    root=[73.416,82.407,87.307][variant]
    pad(start,9.,[root,root*2,root*3,root*4.5],.10)
    for k,tt in enumerate([.55,1.8,3.2,4.1]):note(start+tt,root*[4,6,8,9][k],.060,(-.35 if k%2 else .35))
    for tt in (3.,5.4):air(start+tt-.07,.22,.15);hit(start+tt,.03,150.)
    # Valve deployment, pressure rise, then the approved twin-jet character.
    for k in range(5):
        q=np.arange(round(.10*SR))/SR
        sig=(np.sin(2*np.pi*(640+variant*75)*q)+.3*np.sin(2*np.pi*1120*q))*np.exp(-q*45)
        add(start+4.0+k*.29,sig,.027,(-.3 if k%2 else .3))
    air(start+4.05,1.95,.57,0.,True)
    q=np.arange(round(1.95*SR))/SR;freq=75+170*(q/1.95)**2
    add(start+4.05,np.sin(2*np.pi*np.cumsum(freq)/SR)*(q/1.95)**2,.085)
    hit(start+6.,.32,43.654+variant*3.0);air(start+5.92,.8,.40)
    q=np.arange(9*SR)/SR
    env=np.interp(np.arange(len(q)),np.arange(0,len(q),240),[boost_at(float(t)) for t in q[::240]])
    env*=np.clip((9.-q)/.16,0,1)
    n=rng.normal(size=len(q));lo=np.convolve(n,np.ones(85)/85,'same');mid=np.convolve(n,np.ones(7)/7,'same')-lo
    roar=(lo*1.45+mid*.20)*env*(.84+.10*np.sin(2*np.pi*7.7*q)+.06*np.sin(2*np.pi*13.1*q))
    add(start,roar,.39,-.22);add(start+.012,roar,.36,.22)
    freq=58+variant*6+env*42;ph=2*np.pi*np.cumsum(freq)/SR
    add(start,(np.sin(ph)+.12*np.sin(ph*2.01))*env,.062)
    for k in range(5):
        tt=start+6.15+k*.52;hit(tt,.060,49.);note(tt,root*[8,6,9,6,8][k],.027,np.sin(k)*.5)
    for k in range(6):
        q=np.arange(round(.04*SR))/SR;add(start+3.3+k*.28,rng.normal(size=len(q))*np.exp(-q*115),.012,np.sin(k)*.4)
# The three-car lineup is a quieter resolution, allowing the colors to breathe.
air(26.85,.45,.19)
pad(26.7,3.3,[146.832,220,293.665,440],.11)
for k,hz in enumerate([293.665,440.,587.33]):note(27.15+k*.22,hz,.095)
q=np.arange(len(out))/SR;fade=np.minimum(q/.3,1)*np.clip((30-q)/.6,0,1);out*=fade[:,None]
out=np.tanh(out*1.35)*.88
with wave.open(str(ROOT/'AFTERLIGHT_score.wav'),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes(np.int16(np.clip(out,-1,1)*32767).tobytes())
print('THREE-CAR SCORE COMPLETE',flush=True)
