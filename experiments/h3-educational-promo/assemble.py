from pathlib import Path
import os,json,uuid,urllib.request,base64,sys,math
import av,numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from fractions import Fraction
R=Path(__file__).parents[1];P=R/'work/h3_promo';O=R/'outputs/H3本地能做什么-30秒';P.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
A=Path('C:/Users/Administrator/Desktop/AI-Run-Archive');FPS=24;SR=48000;W,H=720,1280;D=29.5
lines=[
('MiniMax H3，在本地真的可以为所欲为？',0,3.8),
('先让动漫角色跳舞，再换成真人风格。',3.8,7.7),
('到这一步，我已经不满足了。',7.7,10.5),
('裙子短一点，造型大胆一点，甚至……让她一口气换十套衣服！',10.5,16.9),
('但衣服换了，脸可不能跟着换。',16.9,20.1),
('首尾帧怎么控？动作怎么写？看我们的实跑记录。',20.1,24.4),
('成片和工作流，GitHub搜，H3 Video Lab。下一期，直接教你跑。',24.4,29.5)]
(O/'配音文案.json').write_text(json.dumps(lines,ensure_ascii=False,indent=2),encoding='utf-8')
if sys.argv[1]=='tts':
 for i,(text,_,_) in enumerate(lines):
  f=P/f'voice{i}.mp3'
  if f.exists():continue
  body={'user':{'uid':'h3-educational-promo'},'req_params':{'text':text,'speaker':'zh_female_vv_uranus_bigtts','audio_params':{'format':'mp3','sample_rate':24000,'speech_rate':12}}}
  req=urllib.request.Request('https://openspeech.bytedance.com/api/v3/tts/unidirectional',data=json.dumps(body).encode(),headers={'X-Api-Key':os.environ['DOUBAO_TTS_KEY'],'X-Api-Resource-Id':'seed-tts-2.0','X-Api-Request-Id':str(uuid.uuid4()),'Content-Type':'application/json'})
  chunks=[]
  with urllib.request.urlopen(req,timeout=90) as resp:
   for raw in resp:
    s=raw.decode().strip()
    if s.startswith('data:'):s=s[5:].strip()
    if not s:continue
    d=json.loads(s)
    if d.get('code',0) not in (0,20000000):raise RuntimeError('TTS unsuccessful: '+str(d.get('code')))
    if d.get('data'):chunks.append(base64.b64decode(d['data']))
  if not chunks:raise RuntimeError('No speech audio')
  f.write_bytes(b''.join(chunks));print('voice ready',i,flush=True)
 sys.exit()

def audio(path):
 parts=[];res=av.AudioResampler(format='fltp',layout='stereo',rate=SR)
 with av.open(str(path)) as c:
  for f in c.decode(audio=0):parts.extend(x.to_ndarray() for x in res.resample(f))
  parts.extend(x.to_ndarray() for x in res.resample(None))
 return np.concatenate(parts,axis=1)
mix=np.zeros((2,round(D*SR)),dtype=np.float32);fits=[]
for i,(_,start,end) in enumerate(lines):
 x=audio(P/f'voice{i}.mp3');limit=round((end-start-.15)*SR)
 # Modest timing fit; resampling speed is recorded for review.
 factor=max(1,x.shape[1]/limit)
 if factor>1:
  old=np.arange(x.shape[1]);new=np.linspace(0,x.shape[1]-1,limit);x=np.array([np.interp(new,old,row) for row in x],dtype=np.float32)
 offset=round((start+.06)*SR);mix[:,offset:offset+x.shape[1]]+=x*.92
 fits.append({'line':i,'timing_speed_factor':factor,'speech_seconds':x.shape[1]/SR,'slot_seconds':end-start})
music=audio(A/'experiments/ten-outfit-dance/ten-outfit-dance-30s.mp4')[:,:mix.shape[1]]
mix+=music*.075
mix[:,-int(.4*SR):]*=np.linspace(1,0,int(.4*SR));mix=np.clip(mix,-.97,.97)

def loadclip(path):
 out=[]
 with av.open(str(path)) as c:
  rate=float(c.streams.video[0].average_rate)
  for f in c.decode(video=0):out.append(f.to_image().convert('RGB'))
 return out,rate
anime,ar=loadclip(A/'experiments/minimax-h3/anime-gesture-dance.mp4')
real,rr=loadclip(R/'outputs/真人手势舞-画面预览-待配原曲.mp4')
outfit,fr=loadclip(A/'experiments/ten-outfit-dance/ten-outfit-dance-30s.mp4')
ref=Image.open(A/'experiments/ten-outfit-dance/01-JK黑丝.png').convert('RGB')
endref=ref.copy()
fonts={}
def ft(n,b=False):
 k=(n,b)
 if k not in fonts:fonts[k]=ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if b else 'msyh.ttc'),n)
 return fonts[k]
def text(im,xy,s,size=30,fill='white',bold=False,anchor=None):ImageDraw.Draw(im).text(xy,s,font=ft(size,bold),fill=fill,anchor=anchor,stroke_width=1,stroke_fill='#0d1722')
def panel(im,xy,fill='#172539') :ImageDraw.Draw(im).rounded_rectangle(xy,20,fill=fill)
def wrap(s,n=20):return [s[j:j+n] for j in range(0,len(s),n)]
def clipframe(frames,rate,t):return frames[min(len(frames)-1,max(0,int(t*rate)))].copy()
def build(t):
 im=Image.new('RGB',(W,H),'#0a101b')
 if t<3.8:
  k=int(t/1.25)%3;src=clipframe([anime,real,outfit][k],[ar,rr,fr][k],t if k<2 else t*3)
  label='本地生成 · 三次进化';title='真的可以为所欲为？'
 elif t<7.7:
  src=clipframe(anime,ar,t-3.8) if t<5.7 else clipframe(real,rr,t-5.7+1)
  label='01 / 动漫 → 真人风格';title='先让她动起来'
 elif t<10.5:
  src=clipframe(real,rr,t-7.7+4);label='02 / 同一个需求，继续升级';title='这还只是开始'
 elif t<20.1:
  src=clipframe(outfit,fr,(t-10.5)*3.125);label='03 / 十套完整穿搭';title='一口气换十套衣服' if t<16.9 else '换衣服，也要稳住脸'
 else:
  src=clipframe(outfit,fr,(t-20.1)*2+2);label='04 / 从成片，到工作流';title='首尾帧 × 动作提示词' if t<24.4 else '真实成片与参数，都在这里'
 stage=ImageOps.fit(src,(656,858),method=Image.Resampling.LANCZOS);im.paste(stage,(32,172))
 text(im,(34,35),'H3  /  LOCAL VIDEO LAB',25,'#c8f873',True)
 text(im,(34,84),title,39,'white',True)
 panel(im,(34,184,470,229),'#101a26');text(im,(50,194),label,21,'#d7edff')
 if 20.1<=t<24.4:
  panel(im,(54,742,666,1006),'#111e2e')
  for x,img,name in [(75,ref,'首帧 / 0'),(447,endref,'尾帧 / N−1')]:
   im.paste(ImageOps.fit(img,(166,182)),(x,762));text(im,(x+83,961),name,22,'#c8f873',True,'mm')
  text(im,(344,827),'→',48,'#c8f873',True,'mm');text(im,(344,884),'生成动作',22,'white',False,'mm')
 if t>=24.4:
  panel(im,(48,675,672,1010),'#101c2b')
  text(im,(360,716),'GitHub 搜索',28,'#c8f873',True,'mm')
  text(im,(360,781),'qiu-q /',29,'white',False,'mm')
  text(im,(360,843),'h3-video-lab',46,'white',True,'mm')
  text(im,(360,911),'成片 · 参数 · 工作流',27,'#c8f873',False,'mm')
  text(im,(360,963),'下一期，直接教你跑',24,'white',False,'mm')
 # Short subtitle cues keep vertical safe areas clear.
 cues=[(0,1.8,'MiniMax H3'),(1.8,3.8,'在本地真的可以为所欲为？'),(3.8,5.7,'先让动漫角色跳舞'),(5.7,7.7,'再换成真人风格'),(7.7,10.5,'到这一步，我已经不满足了'),(10.5,12.5,'裙子短一点，造型大胆一点'),(12.5,13.4,'甚至……'),(13.4,16.9,'让她一口气换十套衣服！'),(16.9,20.1,'但衣服换了，脸可不能跟着换'),(20.1,22.3,'首尾帧怎么控？动作怎么写？'),(22.3,24.4,'看我们的实跑记录'),(24.4,27,'成片和工作流，GitHub 搜'),(27,29.5,'h3-video-lab · 下一期教你跑')]
 sub=next(s for start,end,s in cues if start<=t<end)
 for j,s in enumerate(wrap(sub,18)):text(im,(360,1082+j*45),s,32,'white',True,'mm')
 text(im,(34,1205),'AI生成 · 成年虚拟人物 · 豆包合成配音',18,'#9aadc0')
 ImageDraw.Draw(im).rounded_rectangle((34,1252,34+int(652*t/D),1258),3,fill='#c8f873')
 return im
if sys.argv[1]=='preview':
 sheet=Image.new('RGB',(720*3,1280*2))
 for i,t in enumerate([1,6,12,16,22,27]):sheet.paste(build(t),((i%3)*720,(i//3)*1280))
 sheet.resize((1080,1280)).save(O/'分镜预览.jpg');sys.exit()
dst=O/'MiniMaxH3-本地能做什么-29.5秒.mp4';cursor=0
with av.open(str(dst),'w') as c:
 v=c.add_stream('libx264',rate=FPS);v.width=W;v.height=H;v.pix_fmt='yuv420p';v.options={'crf':'19','preset':'fast'}
 a=c.add_stream('aac',rate=SR);a.layout='stereo';a.bit_rate=160000
 for i in range(round(D*FPS)):
  im=build(i/FPS);vf=av.VideoFrame.from_image(im);vf.pts=i;vf.time_base=Fraction(1,FPS)
  for packet in v.encode(vf):c.mux(packet)
  limit=round((i+1)*SR/FPS)
  while cursor<limit:
   end=min(limit,cursor+1024);af=av.AudioFrame.from_ndarray(np.ascontiguousarray(mix[:,cursor:end]),format='fltp',layout='stereo');af.sample_rate=SR;af.pts=cursor;af.time_base=Fraction(1,SR)
   for packet in a.encode(af):c.mux(packet)
   cursor=end
  if i%120==0:print('frame',i,flush=True)
 for packet in v.encode(None):c.mux(packet)
 for packet in a.encode(None):c.mux(packet)
with av.open(str(dst)) as c:
 s=c.streams.video[0];report={'width':s.width,'height':s.height,'fps':float(s.average_rate),'frames':sum(1 for _ in c.decode(video=0)),'duration':float(s.duration*s.time_base),'voice':'zh_female_vv_uranus_bigtts','voice_fitting':fits,'new_H3_generation':False,'source_archive':'local-ai-run-archive','upscaled_from_low_resolution_sources':True}
with av.open(str(dst)) as c:report['audio_decoded_samples']=sum(f.samples for f in c.decode(audio=0))
(O/'制作核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False),flush=True)
