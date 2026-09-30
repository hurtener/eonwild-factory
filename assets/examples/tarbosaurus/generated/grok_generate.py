"""Grok Imagine Video via OpenRouter: submit, poll, download.
usage: gen.py <name> <duration> <first_frame.png|-> <prompt>"""
import base64,json,os,sys,time,urllib.request
key=[l.split("=",1)[1].strip().strip("\"'") for l in open(os.environ.get("OPENROUTER_ENV","/Volumes/m2-extended-disk/Repos/chartworks/.env")) if l.startswith("OPENROUTER_API_KEY=")][0]
name,duration,frame,prompt=sys.argv[1],int(sys.argv[2]),sys.argv[3],sys.argv[4]
out=os.path.dirname(os.path.abspath(__file__))
def call(method,url,body=None):
    req=urllib.request.Request(url,data=json.dumps(body).encode() if body else None,method=method,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=120) as r: return r.read()
body={'model':'x-ai/grok-imagine-video-1.5','prompt':prompt,'duration':duration,'resolution':'720p','aspect_ratio':'16:9'}
if frame!='-':
    body['frame_images']=[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(open(frame,'rb').read()).decode()},'frame_type':'first_frame'}]
job=json.loads(call('POST','https://openrouter.ai/api/v1/videos',body));print('submitted',job.get('id'),job.get('status'),flush=True)
while True:
    time.sleep(10);st=json.loads(call('GET','https://openrouter.ai/api/v1/videos/'+job['id']))
    if st['status'] not in ('pending','in_progress'): break
print('status',st['status'],'cost',st.get('usage',{}).get('cost'),flush=True)
if st['status']=='completed':
    open(f'{out}/{name}.mp4','wb').write(call('GET',f"https://openrouter.ai/api/v1/videos/{job['id']}/content"));print('saved',f'{out}/{name}.mp4')
else: print(json.dumps(st)[:800])
