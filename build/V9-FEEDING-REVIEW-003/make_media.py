"""Encode exact native-speed review frames without altering the candidate."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def encode(view):
    frames=HERE/'render'/f'{view}-candidate-frames'
    assert len(list(frames.glob('frame-*.png')))==144
    output=HERE/f'feeding-{view}.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-framerate','24','-i',str(frames/'frame-%04d.png'),
                    '-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    facts=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
       '-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(output)]))['streams'][0]
    assert facts['avg_frame_rate']=='24/1' and facts['nb_read_frames']=='144'
    assert float(facts['duration'])==6 and facts['width']==960 and facts['height']==540
    return {'view':view,'path':str(output.relative_to(ROOT)),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),**facts}

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:media=list(pool.map(encode,['side','front','rear']))
    sheet=Image.new('RGB',(1440,850),(20,24,22));draw=ImageDraw.Draw(sheet)
    for i,frame in enumerate([1,50,59,73,99,109]):
        image=Image.open(HERE/'render/side-candidate-frames'/f'frame-{frame:04d}.png').resize((480,270))
        x=i%3*480;y=i//3*290;sheet.paste(image,(x,y+20));draw.text((x+8,y+4),f'scene {frame} | {(frame-1)/24:.3f}s',fill='white')
    for i,view in enumerate(['front','rear']):
        image=Image.open(HERE/'render'/f'{view}-candidate-frames/frame-0057.png').resize((480,270))
        sheet.paste(image,(i*480,580));draw.text((i*480+8,584),view+' | 2.333s',fill='white')
    sheet.save(HERE/'feeding-review-sheet.jpg',quality=92)
    receipt=json.loads((HERE/'receipt.json').read_text())
    result={'candidate_sha256':receipt['candidate_sha256'],'profile_sha256':receipt['profile_sha256'],
            'renderer_sha256':hashlib.sha256((HERE/'render_feeding.py').read_bytes()).hexdigest(),
            'status':'LOCAL_MEDIA_COMPLETE_NOT_USER_ACCEPTED','media':media}
    report=ROOT/'reports/V9-FEEDING-REVIEW-003';report.mkdir(parents=True,exist_ok=True)
    (report/'media-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
