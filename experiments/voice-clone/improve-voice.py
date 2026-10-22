from pathlib import Path
import torch, numpy as np, soundfile as sf, librosa,json
from qwen_tts import Qwen3TTSModel
p=Path(__file__).resolve().parent;dest=p/'v2';dest.mkdir(exist_ok=True)
torch.set_num_threads(6)
m=Qwen3TTSModel.from_pretrained(r'C:\Users\Administrator\Desktop\角色资产库\配音工具\models\Qwen3-TTS-1.7B-Base',device_map='cuda:0',dtype=torch.bfloat16,attn_implementation='sdpa')
prompts={}
for name,text in [('lulu','当然不会，那怎么会呢？'),('lumei','你以后不会家暴我吧，我可打不过你。')]:
    y,sr=sf.read(p/f'{name}_clean_reference.wav')
    prompts[name]=m.create_voice_clone_prompt(ref_audio=(y.astype('float32'),sr),ref_text=text,x_vector_only_mode=False)
lines=json.loads((p/'cloned_lines.json').read_text(encoding='utf-8'))
timings=[(.45,3.5),(3.65,4.6),(6.8,8.2),(8.3,10.25),(10.4,11.95),(12.0,15.0)]
results=[]
for item,(start,end) in zip(lines,timings):
    candidates=[];name=item['speaker'];reference=prompts[name][0].ref_spk_embedding.flatten().float()
    for attempt in range(2):
        torch.manual_seed(36100+item['index']*17+attempt)
        wavs,sr=m.generate_voice_clone(text=item['text'],language='Chinese',voice_clone_prompt=prompts[name],max_new_tokens=200,do_sample=True,top_p=.8,top_k=40,temperature=.7)
        y=np.asarray(wavs[0],dtype='float32');y,bounds=librosa.effects.trim(y,top_db=38)
        # Retain a short natural margin and avoid chopping quiet consonants.
        emb=m.create_voice_clone_prompt(ref_audio=(y,sr),x_vector_only_mode=True)[0].ref_spk_embedding.flatten().float()
        similarity=float(torch.nn.functional.cosine_similarity(reference,emb,dim=0))
        speed=max(1,len(y)/sr/(end-start-.03))
        score=similarity-.4*max(0,speed-1.12)
        path=dest/f"line_{item['index']}_{name}_take{attempt+1}.wav";sf.write(path,y,sr)
        candidates.append({'file':str(path),'similarity':similarity,'seconds':len(y)/sr,'speed_needed':speed,'score':score})
        print('candidate',item['index'],attempt+1,'seconds',round(len(y)/sr,2),'similarity',round(similarity,3),flush=True)
    best=max(candidates,key=lambda c:c['score'])
    results.append(dict(item,file=best['file'],seconds=best['seconds'],start=start,end=end,candidates=candidates))
    (dest/'cloned_lines.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
