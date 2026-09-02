"""Encode completed fixed-view sequences and record exact media provenance."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REPORT=ROOT/'reports/V9-FEEDING-REVIEW-001'


def encode(view):
    frames=HERE/'render-coupled'/f'{view}-candidate-frames'
    assert len(list(frames.glob('frame-*.png')))==144,view
    output=HERE/f'feeding-{view}.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(frames/'frame-%04d.png'),
                    '-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)],check=True)
    facts=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
                    '-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(output)]))['streams'][0]
    assert facts['avg_frame_rate']=='24/1' and int(facts['nb_read_frames'])==144
    assert facts['width']==960 and facts['height']==540 and abs(float(facts['duration'])-6)<1e-6
    return {'view':view,'path':str(output.relative_to(ROOT)),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),**facts}


if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        media=list(pool.map(encode,['side','front','rear']))
    sheet=Image.new('RGB',(1440,850),(20,24,22))
    draw=ImageDraw.Draw(sheet)
    for i,frame in enumerate([1,48,61,81,97,116]):
        img=Image.open(HERE/'render-coupled/side-candidate-frames'/f'frame-{frame:04d}.png').resize((480,270))
        x=(i%3)*480;y=(i//3)*290
        sheet.paste(img,(x,y+20));draw.text((x+8,y+4),f'scene {frame} | source {(frame-1)/24:.3f}s',fill='white')
    for i,view in enumerate(['front','rear']):
        img=Image.open(HERE/'render-coupled'/f'{view}-candidate-frames/frame-0061.png').resize((480,270))
        x=i*480;sheet.paste(img,(x,580));draw.text((x+8,584),view+' | 2.500s',fill='white')
    sheet.save(HERE/'feeding-review-sheet.jpg',quality=92)
    receipt=json.loads((HERE/'receipt.json').read_text())
    out={'status':'LOCAL_MEDIA_COMPLETE_NOT_VISUAL_ACCEPTANCE','candidate_sha256':receipt['candidate_sha256'],
         'profile_sha256':receipt['profile_sha256'],'renderer_sha256':hashlib.sha256((HERE/'render_feeding.py').read_bytes()).hexdigest(),
         'source_time_mapping':'(scene_frame-1)/24; no speedup','media':media}
    REPORT.mkdir(parents=True,exist_ok=True)
    (REPORT/'media-verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))
