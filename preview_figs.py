import json,glob,os
import render as R
from PIL import Image
ims=[];names=[]
for p in sorted(glob.glob('scripts/*.json')):
    js=json.load(open(p,encoding='utf-8'))
    for i,sc in enumerate(js['scenes']):
        if sc['type']=='figure':
            n=len(sc['beats']); bt=[k*3.0 for k in range(n)]; bd=[3.0]*n
            plan=[{'sc':sc,'bt':bt,'bd':bd,'t0':0,'len':n*3+1}]
            for t in (n*3-0.2,):
                ims.append(Image.fromarray(R.frame(t,plan,n*3+1,js['section_label'])).resize((640,360))); names.append((p,i,sc['kind']))
print(len(ims)); 
cols=2
for part in range(0,len(ims),8):
    chunk=ims[part:part+8]; sh=Image.new('RGB',(1280,360*((len(chunk)+1)//2)),'white')
    for k,im in enumerate(chunk): sh.paste(im,((k%2)*640,(k//2)*360))
    sh.save(f'review/stills/figs{part//8}.png')
print(names)
