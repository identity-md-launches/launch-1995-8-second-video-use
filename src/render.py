"""Deterministic reference-image puppet animation. Run from repository root.

Requires Python 3, Pillow and numpy. The reference PNG is bundled in assets/.
Frames and silent audio are intermediates, written under test/scratch/.
"""
from pathlib import Path
import math
import wave
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test/scratch/frames'
OUT.mkdir(parents=True, exist_ok=True)
im = Image.open(ROOT / 'assets/reference.png').convert('RGB')
W, H = im.size
FPS, COUNT = 24, 192

# Hand traced silhouette. This retains the original photographic texture.
outline = [(501,109),(524,104),(573,119),(601,144),(588,115),
 (581,85),(587,65),(599,61),(609,70),(613,94),(623,108),
 (631,91),(643,89),(650,100),(648,119),(664,140),
 (661,133),(679,123),(697,120),(715,124),(728,135),(749,134),
 (759,126),(761,115),(759,100),(766,91),(777,92),(784,105),
 (786,80),(792,65),(804,64),(813,73),(815,96),(811,117),
 (806,134),(843,112),(867,107),(880,112),(878,146),
 (871,181),(855,204),(831,218),(837,254),(840,287),
 (837,320),(822,345),(791,367),(779,382),(793,404),
 (800,432),(826,431),(849,441),(862,455),(842,465),
 (821,466),(830,490),(844,520),(842,552),(831,576),
 (815,593),(800,589),(789,574),(785,602),(785,644),
 (782,663),(791,686),(792,707),(778,712),(741,712),
 (731,700),(725,680),(727,664),(721,612),(700,607),
 (703,665),(697,681),(705,706),(697,719),(666,723),
 (652,715),(647,695),(642,682),(637,668),(621,684),
 (599,683),(590,675),(592,644),(586,602),(575,577),
 (564,612),(558,650),(563,678),(557,695),(526,698),
 (514,690),(511,673),(515,649),(514,604),(518,576),
 (523,543),(523,493),(527,457),(536,438),(522,421),
 (515,401),(517,381),(529,363),(546,355),(558,360),
 (570,383),(580,399),(603,400),(626,404),(647,393),
 (657,376),(637,365),(614,348),(598,326),(590,296),
 (586,269),(591,230),(571,225),(545,215),(524,200),
 (510,178),(503,150)]
mask = Image.new('L', im.size)
ImageDraw.Draw(mask).polygon(outline, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(1.0))
rgba = im.convert('RGBA'); rgba.putalpha(mask)

# Interpolate the unoccupied background on each scanline, preserving floor light.
arr = np.array(im).astype(float)
bg = arr.copy()
for y in range(H):
    left = arr[y, 455:480].mean(axis=0)
    right = arr[y, 910:935].mean(axis=0)
    for x in range(480, 910):
        u = (x-480)/430
        bg[y,x] = left*(1-u)+right*u
background = Image.fromarray(np.uint8(bg)).filter(ImageFilter.GaussianBlur(2))

def smooth(x):
    x = max(0., min(1., x)); return x*x*(3-2*x)

def pulse(t,a,b):
    return math.sin(math.pi*max(0,min(1,(t-a)/(b-a))))**2 if a<t<b else 0.

# Back of the puppet is an explicitly illustrated approximation for the brief spin.
back = Image.new('RGBA', im.size)
d = ImageDraw.Draw(back)
d.polygon(outline, fill=(142,87,44,255))
d.ellipse((585,140,840,371),fill=(164,105,57,255))
d.ellipse((592,150,829,360),fill=(175,114,65,255))
d.polygon([(650,376),(780,377),(815,445),(800,591),(781,672),
 (727,672),(719,605),(700,605),(699,679),(641,679),(611,490)],fill=(24,28,27,255))
d.line([(711,405),(713,581)],fill=(45,49,44),width=3)
for x,y,r in [(619,186,8),(648,167,9),(673,184,7),(703,168,9),
 (735,185,7),(768,166,8),(797,190,7),(548,449,7),(575,433,8),
 (599,448,8),(557,475,7),(585,465,8),(548,501,6)]:
    d.ellipse((x-r,y-r,x+r,y+r),fill=(231,212,165,255))
back.putalpha(mask)
back = back.filter(ImageFilter.GaussianBlur(1.2))
# Rounded illumination and fine grain give the otherwise unseen rear a softer
# dimensional appearance. Retain the source ears, antlers and lower hoof texture.
ba=np.array(back).astype(float)
yy,xx=np.mgrid[:H,:W]
rng=np.random.default_rng(41)
shade=.63+.43*np.exp(-((xx-670)/150)**2-((yy-235)/430)**2)
grain=rng.normal(0,1.5,(H,W))
ba[:,:,:3]=np.clip(ba[:,:,:3]*shade[:,:,None]+grain[:,:,None],0,255)
rim=np.exp(-((xx-826)/12)**2)*np.exp(-((yy-275)/170)**2)
ba[:,:,1]+=rim*28;ba[:,:,2]+=rim*21
back=Image.fromarray(np.uint8(np.clip(ba,0,255)))
detail=Image.new('L',im.size);dd=ImageDraw.Draw(detail)
dd.rectangle((0,0,W,120),fill=255)
dd.polygon([(495,106),(560,102),(601,160),(595,220),(544,213),(508,180)],fill=255)
dd.polygon([(818,152),(852,111),(878,107),(876,169),(849,211),(828,220)],fill=255)
dd.rectangle((0,680,W,H),fill=255)
detail=np.minimum(np.array(detail.filter(ImageFilter.GaussianBlur(2))),np.array(mask))
bits=rgba.copy();bits.putalpha(Image.fromarray(detail))
back=Image.alpha_composite(back,bits)

# Isolate original lenses so their actual black glass can slide down over the eyes.
gm = Image.new('L', im.size); gd = ImageDraw.Draw(gm)
gd.ellipse((655,122,730,177),fill=255)
gd.ellipse((750,122,817,177),fill=255)
gd.line([(727,144),(750,144)],fill=255,width=5)
gm = gm.filter(ImageFilter.GaussianBlur(.6))
glasses = im.convert('RGBA'); glasses.putalpha(gm)
# Fur-colored cap, used only after the glasses move. Rounded spots restore forehead detail.
repair_mask=gm.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(2))
ca=np.zeros((H,W,4),dtype=np.uint8)
for py in range(106,194):
    for px in range(632,837):
        top=141+.0038*(px-739)**2
        sx=int(709+(px-645)*.23)
        sy=int(190+max(0,py-top)*.7)
        color=arr[sy,sx]
        ca[py,px,:3]=color
        ca[py,px,3]=repair_mask.getpixel((px,py))
cap=Image.fromarray(ca)

def deform(layer,t):
    # Continuous mesh motion, with fixed feet and separately weighted shoulders,
    # head and forehooves. Inverse mapping keeps the detailed fur intact.
    shim = math.sin(t*math.pi*6)*pulse(t,.15,2.1)
    point1=pulse(t,2.05,2.85); point2=pulse(t,2.85,3.65)
    nod=math.sin((t-6.05)*math.pi*2)*pulse(t,6.05,7.1)
    bounce=5*math.sin(t*math.pi*4)*pulse(t,.15,7.7)
    reset=1-smooth((t-7.4)/.5)
    tilt=1.6*shim+.8*math.sin(t*5)*pulse(t,.2,3.6)
    mesh=[]; step=32
    def source(x,y):
        head=math.exp(-((y-242)/160)**4)
        body=math.exp(-((y-470)/135)**2)
        hoofL=math.exp(-((x-665)/43)**2-((y-614)/70)**2)
        hoofR=math.exp(-((x-815)/40)**2-((y-553)/52)**2)
        dx=(shim*7*body + head*tilt*(y-380)/60
            +point1*hoofL*48-point2*hoofR*35)*reset
        dy=(bounce*math.sin(math.pi*max(0,min(1,(720-y)/650)))
            +shim*(x-710)*body*.055 -point1*hoofL*88
            -point2*hoofR*53 +nod*head*8)*reset
        return x-dx,y-dy
    for y in range(0,H,step):
        for x in range(0,W,step):
            x1=min(W,x+step);y1=min(H,y+step)
            mesh.append(((x,y,x1,y1),(*source(x,y),*source(x,y1),
                *source(x1,y1),*source(x1,y))))
    return layer.transform(im.size,Image.Transform.MESH,mesh,Image.Resampling.BICUBIC)

for i in range(COUNT):
    t = i/(COUNT-1)*8
    if '--spin-only' in sys.argv and not 3.7<t<4.85:
        continue
    if '--glasses-only' in sys.argv and not 5.05<t<7.8:
        continue
    layer=rgba.copy()
    down=smooth((t-5.05)/.65)*(1-smooth((t-7.15)/.65))
    if down:
        layer=Image.alpha_composite(layer,Image.blend(Image.new('RGBA',im.size),cap,down))
        # Slide and slightly enlarge the original glasses to cover the eyes.
        crop=glasses.crop((645,116,825,183))
        crop=crop.resize((int(180*(1+.06*down)),int(67*(1+.1*down))),Image.Resampling.LANCZOS)
        layer.alpha_composite(crop,(int(645-6*down),int(116+105*down)))
    layer=deform(layer,t)
    if 3.7<t<4.85:
        angle=2*math.pi*smooth((t-3.7)/1.15)
        c=math.cos(angle)
        if c<0: layer=deform(back,t)
        # Foreshortening about the planted vertical axis suggests a fast axial turn.
        crop=layer.crop((480,40,900,735))
        width=max(12,int(420*abs(c)))
        crop=crop.resize((width,695),Image.Resampling.BICUBIC)
        if math.sin(angle)<0: crop=crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        layer=Image.new('RGBA',im.size)
        layer.alpha_composite(crop,(690-width//2,40))
    frame=background.convert('RGBA')
    # Stable, softly grounded contact shadow throughout the dance.
    shadow=Image.new('RGBA',im.size)
    ImageDraw.Draw(shadow).ellipse((512,678,832,725),fill=(0,0,0,80))
    frame=Image.alpha_composite(frame,shadow.filter(ImageFilter.GaussianBlur(13)))
    frame=Image.alpha_composite(frame,layer).convert('RGB')
    # Exact source image at both loop endpoints, with short seamless settling.
    settle=max(1-smooth(t/.25),smooth((t-7.7)/.3))
    if settle: frame=Image.blend(frame,im,settle)
    frame.save(OUT/f'{i:04d}.png',compress_level=2)
    if i%24==0: print(f'Rendered {i}/{COUNT}',flush=True)

with wave.open(str(ROOT/'test/scratch/silence.wav'),'wb') as w:
    w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000)
    w.writeframes(bytes(48000*8*4))
print(f'Rendered {COUNT} frames at {W}x{H}; endpoints equal the supplied reference.')
