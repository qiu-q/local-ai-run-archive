from pathlib import Path
import json,av,numpy as np,shutil,zipfile
from fractions import Fraction
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent;root=p.parents[1];out=root/'outputs/十套换装';out.mkdir(exist_ok=True)
jobs=json.loads((p/'image_jobs.json').read_text(encoding='utf-8'))
comfy=Path(r'C:\Users\Administrator\Desktop\MiniMax-H3\ComfyUI');srcs=[comfy/f'output/video/Outfit10_{i:02d}_00001_.mp4' for i in range(1,11)]
if not all(x.is_file() for x in srcs):raise RuntimeError('Some clips are not ready')
music=comfy/'output/video/Real_Hand_Dance_01_00001_.mp4'
parts=[];rs=av.AudioResampler(format='fltp',layout='stereo',rate=48000)
with av.open(str(music)) as c:
    for f in c.decode(audio=0):parts.extend(r.to_ndarray() for r in rs.resample(f))
    parts.extend(r.to_ndarray() for r in rs.resample(None))
bed=np.concatenate(parts,axis=1);period=15*48000
if bed.shape[1]<period:bed=np.pad(bed,((0,0),(0,period-bed.shape[1])))
bed=bed[:,:period];audio=np.tile(bed,(1,2))
# Brief crossfade at the one music loop boundary, retaining a 15s loop period.
fade=4800;tail=bed[:,-fade:].copy();head=bed[:,:fade].copy();t=np.linspace(0,1,fade)
audio[:,period:period+fade]=tail*(1-t)+head*t
audio[:,:4800]*=np.linspace(0,1,4800);audio[:,-9600:]*=np.linspace(1,0,9600)
audio*=.85;audio=np.clip(audio,-.98,.98).astype('float32')
font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc',20);small=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',14)
dst=root/'outputs/成年模特-十套换装舞蹈-30秒.mp4';verification=[]
with av.open(str(dst),'w') as output:
    v=output.add_stream('libx264',rate=24);v.width=352;v.height=608;v.pix_fmt='yuv420p';v.options={'crf':'17','preset':'medium'}
    a=output.add_stream('aac',rate=48000);a.layout='stereo';a.bit_rate=160000
    cursor=0;frame_index=0
    for k,source in enumerate(srcs):
        motions=[];previous=None;frames=0
        with av.open(str(source)) as c:
            for local,f in enumerate(c.decode(video=0)):
                if local>=72:break
                im=f.to_image().convert('RGB')
                gray=np.array(im.resize((44,76)).convert('L'),dtype='float32')
                if previous is not None:motions.append(float(np.mean(np.abs(gray-previous))))
                previous=gray
                # A short flash masks the outfit cut; frames remain fully animated.
                if k>0 and local<4:im=Image.blend(im,Image.new('RGB',im.size,'white'),[.65,.35,.13,0][local])
                d=ImageDraw.Draw(im)
                d.text((18,20),f'{k+1:02d} / 10',font=small,fill='white',stroke_width=1,stroke_fill='#333333')
                title=jobs[k]['name'].split('-',1)[1]
                d.text((176,566),title,font=font,anchor='mm',fill='white',stroke_width=2,stroke_fill='#29232b')
                if local==36:im.save(p/f'clip{k+1:02d}_middle.png')
                vf=av.VideoFrame.from_image(im);vf.pts=frame_index;vf.time_base=Fraction(1,24)
                for packet in v.encode(vf):output.mux(packet)
                limit=round((frame_index+1)*48000/24)
                while cursor<limit:
                    end=min(cursor+1024,limit);af=av.AudioFrame.from_ndarray(np.ascontiguousarray(audio[:,cursor:end]),format='fltp',layout='stereo');af.sample_rate=48000;af.time_base=Fraction(1,48000);af.pts=cursor
                    for packet in a.encode(af):output.mux(packet)
                    cursor=end
                frames+=1;frame_index+=1
        if frames!=72:raise RuntimeError('Incorrect clip frame count')
        verification.append({'outfit':jobs[k]['name'],'frames_used':frames,'mean_frame_change':float(np.mean(motions))})
        clips=out/'单套舞蹈片段';clips.mkdir(exist_ok=True);shutil.copy2(source,clips/(jobs[k]['name']+'.mp4'))
    for packet in v.encode(None):output.mux(packet)
    for packet in a.encode(None):output.mux(packet)
with av.open(str(dst)) as c:
    vs=c.streams.video[0];meta={'width':vs.width,'height':vs.height,'fps':float(vs.average_rate),'duration':float(vs.duration*vs.time_base),'frames':sum(1 for _ in c.decode(video=0)),'outfits':verification}
with av.open(str(dst)) as c:meta['audio_frames']=sum(1 for _ in c.decode(audio=0))
(p/'verification.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
wf=out/'工作流';wf.mkdir(exist_ok=True)
for f in p.glob('*-api.json'):shutil.copy2(f,wf/f.name)
shutil.copy2(p/'adult_dancer_reference.png',out/'原成年模特参考.png')
shutil.copy2(p/'verification.json',out/'生成检查记录.json')
(out/'制作说明.txt').write_text('十套换装连续转场｜30秒\n\nQwen Image 2.1基于同一位22岁原创成年模特生成十套全身造型，再用本地MiniMax H3逐套生成动作。每套使用72帧，24fps，总计720帧30秒。\n动作重新生成，不是原舞蹈的逐帧换装。服装为风格化Cos造型，不指定具体动漫角色。背景音乐复用此前本地AI生成的原创舞曲，不是抖音原视频歌曲。\n画面原生352x608。源造型图576x1024。人物面部、手部与服装仍可能有轻微生成漂移。\n十套：JK黑丝、洛丽塔白丝、经典女仆、红白巫女、蓝白魔法少女、哥特洛丽塔、精灵幻想、未来战术服、魔女黑丝、粉白偶像。\n',encoding='utf-8-sig')
desktop=Path(r'C:\Users\Administrator\Desktop\十套换装舞蹈');desktop.mkdir(exist_ok=True)
shutil.copy2(dst,desktop/dst.name)
for f in ['十套造型总览.png','制作说明.txt']:shutil.copy2(out/f,desktop/f)
with zipfile.ZipFile(root/'outputs/十套换装-造型与工作流.zip','w',zipfile.ZIP_DEFLATED) as z:
    for f in out.rglob('*'):
        if f.is_file():z.write(f,Path('十套换装')/f.relative_to(out))
print(json.dumps(meta,ensure_ascii=True))
