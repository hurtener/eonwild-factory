"""Encode exactly two native Sprint cycles and full consecutive-frame sheets."""
import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image,ImageDraw,ImageFont
parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);args=parser.parse_args()
p=args.directory
receipts={}
font=ImageFont.load_default(size=17)
for view in ['side','front','rear']:
    folder=p/f'{view}-native-cycle'
    frames=sorted(folder.glob('frame-*.png'))
    if len(frames)!=23:raise RuntimeError(f'{view}: expected23 native frames, got{len(frames)}')
    video=p/f'sprint-{view}-2cycles.mp4'
    subprocess.run(['ffmpeg','-v','error','-framerate','24','-i',str(folder/'frame-%04d.png'),'-vf','loop=loop=1:size=23:start=0','-frames:v','46','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate,duration','-of','json',str(video)],text=True))
    receipts[view]=probe['streams'][0]
    for first in range(0,23,12):
        chosen=frames[first:first+12]
        sheet=Image.new('RGB',(1440,310*((len(chosen)+2)//3)),'#eeeeee');draw=ImageDraw.Draw(sheet)
        for i,path in enumerate(chosen):
            im=Image.open(path).convert('RGB');im.thumbnail((480,280),Image.Resampling.LANCZOS)
            x,y=i%3*480,i//3*310;sheet.paste(im,(x,y))
            frame=first+i+1
            draw.text((x+6,y+284),f'{view} f{frame:02d}  t={(frame-1)/24:.3f}s',fill='black',font=font)
        sheet.save(p/f'{view}-frames-{first+1:02d}-{min(first+12,23):02d}.png')
(p/'media-receipt.json').write_text(json.dumps({'source_frames_per_cycle':23,'fps':24,'cycles':2,'speed_stretch':False,'native_duration_s':23/24,'views':receipts},indent=2)+'\n')
print(json.dumps(receipts,indent=2))
