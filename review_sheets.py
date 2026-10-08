import sys,glob,os
from moviepy.editor import VideoFileClip
from PIL import Image
os.makedirs('review/sheets',exist_ok=True)
for p in sorted(glob.glob('review/s*/**/*.mp4',recursive=True)):
    name=os.path.basename(p)[:-4]
    out=f'review/sheets/{name}.jpg'
    if os.path.exists(out): continue
    c=VideoFileClip(p); n=12; step=c.duration/n
    ims=[Image.fromarray(c.get_frame(step*i+step/2)).resize((427,240)) for i in range(n)]
    c.close()
    sh=Image.new('RGB',(427*3,240*4),'white')
    for i,im in enumerate(ims): sh.paste(im,((i%3)*427,(i//3)*240))
    sh.save(out,quality=80)
    print(name,round(step*n))
