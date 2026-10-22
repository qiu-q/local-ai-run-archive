from pathlib import Path
import json,copy,shutil,urllib.request,sys
p=Path(__file__).resolve().parent;root=p.parents[1];comfy=Path(r'C:\Users\Administrator\Desktop\MiniMax-H3\ComfyUI')
jobs=json.loads((p/'image_jobs.json').read_text(encoding='utf-8'));h=json.load(urllib.request.urlopen('http://127.0.0.1:8188/history'))
gbase=json.loads((root/'work/real_dance/真人手势舞-API.json').read_text(encoding='utf-8'))
records=[]
for i,item in enumerate(jobs):
    record=h.get(item['prompt_id'],{})
    if record.get('status',{}).get('status_str')!='success':raise RuntimeError('Outfit image is not ready: '+str(i+1))
    f=record['outputs']['10']['images'][0];src=comfy/'output'/f['subfolder']/f['filename'];image=f'outfit10_{i+1:02d}.png';shutil.copy2(src,comfy/'input'/image)
    g=copy.deepcopy(gbase)
    prompt='integrated_multimodal_description: One continuous vertical 9:16 realistic live-action fashion dance clip, with the exact same original 22-year-old adult woman, same face, chestnut long straight hair, same room, same full-body framing and exact outfit shown in the first frame. Preserve her garment colors, accessories, opaque fabrics, legwear and shoes throughout. Keep her face and body identity stable. Camera is fixed and shows her full body from head to shoes. She performs one small cheerful hand-gesture dance phrase: she begins making a heart at upper chest height, gently sways her shoulders and hips once, opens both hands outward beside her cheeks with a friendly head tilt, and then smoothly brings her hands back together into the same small heart at upper chest height as the ending frame. Her feet stay planted or make only a tiny weight shift. Relaxed natural movement, warm friendly smile, subtle hair and fabric movement, clear two hands and five fingers per hand, stable background, realistic skin and clothing texture, soft natural daylight. No scene cut, no garment change inside this clip, no extra person, no text or subtitles, no speaking. This is a tasteful adult fashion lookbook dance. Outfit details: '+item['outfit']+'\noverall_soundscape: Quiet indoor room tone and very subtle fabric movement. No speech.\nnon_diegetic_music: N/A'
    g['131']['inputs'].update(prompt=prompt,width=352,height=608,length=73,first_frame=['150',0],last_frame=['150',0])
    g['150']={'class_type':'LoadImage','inputs':{'image':image}}
    g['129']['inputs']['noise_seed']=519830000+i
    g['92']['inputs']['filename_prefix']=f'video/Outfit10_{i+1:02d}'
    (p/f"{item['name']}-video-api.json").write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
    if len(sys.argv)>1 and sys.argv[1]=='first' and i>0:continue
    if len(sys.argv)>1 and sys.argv[1]=='rest' and i==0:continue
    req=urllib.request.Request('http://127.0.0.1:8188/prompt',data=json.dumps({'prompt':g}).encode(),headers={'Content-Type':'application/json'})
    r=json.load(urllib.request.urlopen(req));records.append(dict(item,video_prompt_id=r['prompt_id'],image_file=str(src)));print(i+1,r['prompt_id'],flush=True)
(p/('video_jobs_'+(sys.argv[1] if len(sys.argv)>1 else 'all')+'.json')).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
