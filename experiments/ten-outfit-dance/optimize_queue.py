from pathlib import Path
import json,urllib.request,copy
p=Path(__file__).resolve().parent
def get(path):return json.load(urllib.request.urlopen('http://127.0.0.1:8188'+path,timeout=120))
def post(path,data):
    r=urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8188'+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'}),timeout=120).read()
    return json.loads(r) if r else {}
jobs=json.loads((p/'video_jobs_rest.json').read_text(encoding='utf-8'));queue=get('/queue')
pending={x[1] for x in queue['queue_pending']};running={x[1] for x in queue['queue_running']}
history=get('/history')
selected=[j for j in jobs if j['video_prompt_id'] not in history and j['video_prompt_id'] not in running]
ids=[j['video_prompt_id'] for j in selected]
if ids:post('/queue',{'delete':ids})
records=[]
for j in selected:
    g=json.loads((p/(j['name']+'-video-api.json')).read_text(encoding='utf-8'))
    g['131']['inputs'].pop('first_frame',None);g['131']['inputs'].pop('last_frame',None)
    prompt=g['131']['inputs']['prompt'].split('Outfit details:')[0]
    prompt+='The exact clothing, colors and accessories are defined by the first and last reference keyframes. Preserve those clothes throughout the shot.\noverall_soundscape: Quiet indoor room tone, no speech.\nnon_diegetic_music: N/A'
    g['131']['inputs']['prompt']=prompt
    g['151']={'class_type':'MiniMaxH3AddGuide','inputs':{'positive':['131',0],'latent':['131',1],'vae':['119',0],'image':['150',0],'frame_idx':0}}
    g['152']={'class_type':'MiniMaxH3AddGuide','inputs':{'positive':['151',0],'latent':['131',1],'vae':['119',0],'image':['150',0],'frame_idx':72}}
    g['126']['inputs']['conditioning']=['152',0]
    (p/(j['name']+'-video-api.json')).write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
    result=post('/prompt',{'prompt':g});j['video_prompt_id']=result['prompt_id'];j['conditioning_mode']='shared_text_with_first_last_vae_guides';records.append(j)
    print('queued',j['name'].encode('unicode_escape').decode(),result['prompt_id'],flush=True)
kept=[j for j in jobs if j['video_prompt_id'] not in ids]
(p/'video_jobs_rest.json').write_text(json.dumps(kept+records,ensure_ascii=False,indent=2),encoding='utf-8')
print('optimized',len(records),'kept',len(kept),flush=True)
