from pathlib import Path
import json, numpy as np, soundfile as sf, librosa, av, shutil
from fractions import Fraction
root=Path(__file__).resolve().parents[2];p=root/'work/voice_clone/v2'
# Reuse the verified typography and fictional GPT UI, rebuilding from the original uncaptioned video.
prefix=(root/'work/lulu_yes/finish_video.py').read_text(encoding='utf-8-sig').split('audio=[];')[0]
ctx={'__file__':str(root/'work/lulu_yes/finish_video.py')};exec(prefix,ctx)
timings=[(.45,3.5),(3.55,4.7),(6.8,8.2),(8.3,10.25),(10.4,11.95),(12.0,15.0)]
lines=json.loads((p/'cloned_lines.json').read_text(encoding='utf-8'))
ctx['segments']=[(a,b,item['text']) for item,(a,b) in zip(lines,timings)]
duration=362/24;sr=48000;n=round(duration*sr)
back,rate=sf.read(p/'yes_backing.wav',always_2d=True)
back=librosa.resample(back.T,orig_sr=rate,target_sr=sr)
mix=np.zeros((2,n),dtype='float32');k=min(n,back.shape[1]);mix[:,:k]=back[:,:k]*.35
def atempo(y,rate,speed):
    g=av.filter.Graph()
    a=g.add_abuffer(sample_rate=rate,format='fltp',layout='mono',time_base=Fraction(1,rate))
    b=g.add('atempo',str(speed));c=g.add('abuffersink');a.link_to(b);b.link_to(c);g.configure()
    f=av.AudioFrame.from_ndarray(y.astype('float32')[None,:],format='fltp',layout='mono');f.sample_rate=rate;f.time_base=Fraction(1,rate)
    g.push(f);g.push(None);parts=[]
    while True:
        try:parts.append(g.pull().to_ndarray()[0])
        except (av.error.EOFError,av.error.BlockingIOError):break
    return np.concatenate(parts)

retiming=[]
for item,(a,b) in zip(lines,timings):
    y,rate=sf.read(item['file']);y,_=librosa.effects.trim(y,top_db=32)
    available=b-a-.04;speed=max(1,len(y)/rate/available)
    if speed>1.005:y=atempo(y,rate,speed)
    y=librosa.resample(y,orig_sr=rate,target_sr=sr)
    # Consistent dialogue level and short fades at edit boundaries.
    rms=np.sqrt(np.mean(y*y));gain=min(.14/max(rms,1e-6),4);y=y*gain
    fade=min(240,len(y)//20);y[:fade]*=np.linspace(0,1,fade);y[-fade:]*=np.linspace(1,0,fade)
    start=round(a*sr);length=min(len(y),n-start);mix[:,start:start+length]+=y[:length]
    sf.write(p/f"fitted_{item['index']}.wav",y,sr)
    retiming.append({'line':item['index'],'start':a,'end':a+length/sr,'speed':speed})
for a in [4.15,5.95]:
    tt=np.arange(1200)/sr;y=.12*np.sin(2*np.pi*2200*tt)*np.exp(-tt*270);off=round(a*sr);mix[:,off:off+len(y)]+=y
peak=np.max(np.abs(mix));mix*=min(1,.96/peak)
sf.write(p/'替换后完整音轨.wav',mix.T,sr)
src=Path(r'C:\Users\Administrator\Desktop\MiniMax-H3\ComfyUI\output\video\Lulu_Yes_Work_01_00001_.mp4')
dst=root/'outputs/噜噜的工伤-点Yes-声线优化第二版.mp4'
with av.open(str(src)) as c,av.open(str(dst),'w') as out:
    v=c.streams.video[0];fps=v.average_rate
    ov=out.add_stream('libx264',rate=fps);ov.width=v.width;ov.height=v.height;ov.pix_fmt='yuv420p';ov.options={'crf':'18','preset':'medium'}
    oa=out.add_stream('aac',rate=sr);oa.layout='stereo';oa.bit_rate=160000
    cursor=0
    for i,f in enumerate(c.decode(video=0)):
        im=ctx['draw_frame'](f.to_image(),i/float(fps));vf=av.VideoFrame.from_image(im);vf.pts=i;vf.time_base=1/fps
        for packet in ov.encode(vf):out.mux(packet)
        limit=min(round((i+1)*sr/float(fps)),n)
        while cursor<limit:
            end=min(cursor+1024,limit);af=av.AudioFrame.from_ndarray(np.ascontiguousarray(mix[:,cursor:end]),format='fltp',layout='stereo');af.sample_rate=sr;af.time_base=Fraction(1,sr);af.pts=cursor
            for packet in oa.encode(af):out.mux(packet)
            cursor=end
    for packet in ov.encode(None):out.mux(packet)
    for packet in oa.encode(None):out.mux(packet)
with av.open(str(dst)) as c:
    v=c.streams.video[0];meta={'frames':sum(1 for _ in c.decode(video=0)),'width':v.width,'height':v.height,'duration':float(v.duration*v.time_base)}
with av.open(str(dst)) as c:meta['decoded_audio_frames']=sum(1 for _ in c.decode(audio=0))
meta['dialogue_retiming']=retiming
(p/'replacement_verification.json').write_text(json.dumps(meta,indent=2))
assets=Path(r'C:\Users\Administrator\Desktop\角色资产库\水豚噜噜角色素材包')
shutil.copy2(dst,assets/'二创成片'/dst.name)
dest=assets/'声音素材'/'声线优化第二版';dest.mkdir(parents=True,exist_ok=True)
outdir=root/'outputs/噜噜噜妹-声线优化第二版试听';outdir.mkdir(exist_ok=True)
for srcname,target in [('lulu_clean_reference.wav','噜噜-去配乐参考.wav'),('lumei_clean_reference.wav','噜妹-去配乐参考.wav'),('line_1_lulu.wav','噜噜-复刻对白试听.wav'),('line_3_lumei.wav','噜妹-复刻对白试听.wav')]:
    shutil.copy2(p/srcname,outdir/target);shutil.copy2(p/srcname,dest/target)
note='依据用户指定参考视频7654573990954078833提取角色对白；HDemucs人声分离，按角色台词边界截取，Qwen3-TTS 1.7B Base本地少样本复刻。\n样本约3-4秒，可能残留分离伪影、房间混响或细微音效。此版本为试配，未做口型重新生成，语气和相似度并非完全复现。\n原视频和原配音成片均保留。新视频已去掉原生对白，混入分离后的背景声与新对白。\n'
(outdir/'制作说明.txt').write_text(note,encoding='utf-8');(dest/'制作说明.txt').write_text(note,encoding='utf-8')
print(json.dumps(meta))
