import sys,json,os
import render as R
from PIL import Image
os.makedirs('review/stills',exist_ok=True)
js=json.load(open(sys.argv[1],encoding='utf-8')); idx=[int(x) for x in sys.argv[2].split(',')]
ims=[]
for i in idx:
    sc=js['scenes'][i]; n=len(sc['beats'])
    bt=[k*3.0 for k in range(n)]; bd=[3.0]*n
    plan=[{'sc':sc,'bt':bt,'bd':bd,'t0':0,'len':n*3+1}]
    a=R.frame(n*3-0.2,plan,n*3+1,js['section_label'])
    ims.append(Image.fromarray(a).resize((640,360)))
sh=Image.new('RGB',(1280,360*((len(ims)+1)//2)),'white')
for k,im in enumerate(ims): sh.paste(im,((k%2)*640,(k//2)*360))
sh.save(sys.argv[3])
