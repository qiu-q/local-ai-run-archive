from pathlib import Path
from fractions import Fraction
import av,json,hashlib,shutil,os,uuid,urllib.request,base64,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
R=Path(__file__).parents[1];A=Path('C:/Users/Administrator/Desktop/AI-Run-Archive');O=R/'outputs/Codex小知识-AI短剧教程';O.mkdir(exist_ok=True)
W,H,FPS,SR=720,1280,24,48000;D=44
voice_lines=[
 ('一天一个Codex小知识，我们今天来学习AI小短剧。先看成片。',0,5.9),
 ('第一步，写好反转。两个角色，一个矛盾，一个笑点。',21.083333,25.2),
 ('第二步，准备角色参考图，定好外观、服装和场景。',25.25,29.36),
 ('第三步，让Codex编排任务，交给本地H3生成。',29.416667,33.53),
 ('第四步，调整配音，补上字幕、弹窗和音效。',33.583333,37.95),
 ('成片和工作流已经免费公开，有需要的自取。',38.5,43.8)]
vp=R/'work/lulu_tutorial_voice';vp.mkdir(exist_ok=True)
if len(sys.argv)>1 and sys.argv[1]=='tts':
 for k,(line,_,_) in enumerate(voice_lines):
  path=vp/f'{k}.mp3'
  if path.exists():continue
  body={'user':{'uid':'lulu-tutorial'},'req_params':{'text':line,'speaker':'zh_female_vv_uranus_bigtts','audio_params':{'format':'mp3','sample_rate':24000,'speech_rate':8}}}
  req=urllib.request.Request('https://openspeech.bytedance.com/api/v3/tts/unidirectional',data=json.dumps(body).encode(),headers={'X-Api-Key':os.environ['DOUBAO_TTS_KEY'],'X-Api-Resource-Id':'seed-tts-2.0','X-Api-Request-Id':str(uuid.uuid4()),'Content-Type':'application/json'})
  chunks=[]
  with urllib.request.urlopen(req,timeout=90) as resp:
   for raw in resp:
    s=raw.decode().strip()
    if s.startswith('data:'):s=s[5:].strip()
    if not s:continue
    v=json.loads(s)
    if v.get('code',0) not in (0,20000000):raise RuntimeError('TTS failed')
    if v.get('data'):chunks.append(base64.b64decode(v['data']))
  if not chunks:raise RuntimeError('No speech returned')
  path.write_bytes(b''.join(chunks));print('voice',k,flush=True)
 sys.exit()
src=A/'experiments/voice-clone/lulu-yes-voice-v2.mp4'
frames=[]
with av.open(str(src)) as c:
 for f in c.decode(video=0):frames.append(f.to_image().convert('RGB'))
assert len(frames)==362
def read_audio(path):
 parts=[];rs=av.AudioResampler(format='fltp',layout='stereo',rate=SR)
 with av.open(str(path)) as c:
  for f in c.decode(audio=0):parts.extend(x.to_ndarray() for x in rs.resample(f))
  parts.extend(x.to_ndarray() for x in rs.resample(None))
 return np.concatenate(parts,axis=1)
mix=np.zeros((2,D*SR),dtype=np.float32);original=read_audio(src);start=6*SR;n=round(362/FPS*SR);mix[:,start:start+n]=original[:,:n]
bed=read_audio(A/'experiments/ten-outfit-dance/ten-outfit-dance-30s.mp4')
for lo,hi in [(0,6),(6+362/FPS,D)]:
 count=round((hi-lo)*SR);b=np.tile(bed,(1,2))[:,:count].copy()*.12
 fade=min(12000,count//2);b[:,:fade]*=np.linspace(0,1,fade);b[:,-fade:]*=np.linspace(1,0,fade)
 off=round(lo*SR);mix[:,off:off+count]+=b
voice_report=[]
for k,(_,lo,hi) in enumerate(voice_lines):
 x=read_audio(vp/f'{k}.mp3');limit=round((hi-lo-.1)*SR);factor=max(1,x.shape[1]/limit)
 if factor>1:
  old=np.arange(x.shape[1]);new=np.linspace(0,x.shape[1]-1,limit);x=np.array([np.interp(new,old,row) for row in x],dtype=np.float32)
 off=round(lo*SR);mix[:,off:off+x.shape[1]]+=x*.9;voice_report.append({'line':k,'start':lo,'duration':x.shape[1]/SR,'speed_factor':factor})
mix=np.clip(mix,-.98,.98)
fonts={}
def ft(n,b=False):
 if (n,b) not in fonts:fonts[n,b]=ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if b else 'msyh.ttc'),n)
 return fonts[n,b]
def tx(im,xy,s,n=30,col='#292725',b=False,anchor=None):ImageDraw.Draw(im).text(xy,s,font=ft(n,b),fill=col,anchor=anchor)
def box(im,xy,col='#ffffff'):ImageDraw.Draw(im).rounded_rectangle(xy,24,fill=col)
def fit(im,pic,rect):
 x,y,w,h=rect;v=ImageOps.contain(pic,(w,h),Image.Resampling.LANCZOS);im.paste(v,(x+(w-v.width)//2,y+(h-v.height)//2))
ref=Image.open(A/'experiments/minimax-h3/lulu-first-frame.png').convert('RGB')
repo=Image.open(R/'work/h3_promo/github-user-image.png').convert('RGB')
def header(im,tag):
 tx(im,(36,30),'一天一个 Codex 小知识',25,'#a15336',True);tx(im,(684,37),tag,18,'#6a6760',False,'ra')
def step_header(im,num,title,sub):
 header(im,'AI短剧制作 / 实跑拆解');tx(im,(36,103),num,70,'#a15336',True);tx(im,(142,120),title,44,b=True);tx(im,(38,210),sub,26,'#69645e')
def bottom(im,a,b):
 box(im,(36,1002,684,1188),'#e9e2d6');tx(im,(62,1030),a,29,b=True);tx(im,(62,1090),b,25,'#615b53')
def legacy_build(i):
 t=i/FPS
 # Extend the opening by four seconds; retain the existing tutorial cards.
 if i<144:i=min(i,47)
 else:i-=96
 im=Image.new('RGB',(W,H),'#f4f0e9')
 if i<48:
  header(im,'今天学习 AI 小短剧');tx(im,(36,112),'AI短剧怎么做？',53,b=True);tx(im,(38,194),'我们今天来学习AI小短剧，先看成片',26,'#69645e')
  fit(im,frames[20],(36,275,648,835));box(im,(70,1080,650,1180),'#292725');tx(im,(360,1130),'15秒，看懂一个反转',32,'white',True,'mm')
 elif i<410:
  im=Image.new('RGB',(W,H),'#111820');tx(im,(360,38),'先看成片｜噜噜的工伤',25,'#f4f0e9',True,'mm');fit(im,frames[i-48],(40,80,640,1132));tx(im,(360,1250),'本地 H3 生成 · 角色配音第二版',19,'#c3c9cf',False,'mm')
 elif i<510:
  step_header(im,'01','先写一个反转','先把故事讲明白，再生成画面')
  for y,label,body in [(320,'人物','噜噜嘴硬，噜妹拆台'),(480,'矛盾','他天天抱怨工作太累'),(640,'反转','所谓工作，只是在点 Yes')]:
   box(im,(36,y,684,y+126));tx(im,(62,y+20),label,22,'#a15336',True);tx(im,(62,y+64),body,32,b=True)
  bottom(im,'两个角色 + 一个矛盾 + 一个反转','先写成能在15秒内讲完的小故事')
 elif i<610:
  step_header(im,'02','定好角色','准备参考图，写清外观、服装与场景');fit(im,ref,(36,285,648,650));bottom(im,'同一对角色，沿用同一张参考图','尽量稳住长相和穿搭，生成后仍要检查')
 elif i<710:
  step_header(im,'03','编排生成流程','Codex 整理任务，本地 H3 生成画面')
  for y,title,desc in [(320,'角色图 + 剧本','镜头、动作、对白、声场'),(500,'ComfyUI / MiniMax H3','416 × 736 · 362帧 · 24fps'),(680,'生成结果','约15.08秒，再进入剪辑')]:
   box(im,(36,y,684,y+132));tx(im,(62,y+24),title,31,b=True);tx(im,(62,y+78),desc,25,'#69645e')
  tx(im,(360,470),'↓',32,'#a15336',True,'mm');tx(im,(360,650),'↓',32,'#a15336',True,'mm');bottom(im,'提示词里的时间，是镜头意图','实际时长由帧数与帧率决定')
 elif i<816:
  step_header(im,'04','补齐后期','对白配音、字幕和电脑弹窗分别处理');fit(im,frames[160],(36,288,648,490))
  for y,label,col in [(800,'画面  |  H3生成 → 剪辑','#dce7df'),(858,'对白  |  两个角色分开试配','#e6dcca'),(916,'叠加  |  字幕 / 模拟弹窗 / 音效','#ead9cf')]:box(im,(36,y,684,y+48),col);tx(im,(57,y+8),label,23)
  bottom(im,'角色对白 + 解说，分段呈现','保留原短剧音轨，教程段配步骤解说')
 else:
  header(im,'项目与工作流');tx(im,(36,98),'成片和流程，免费公开',43,b=True);fit(im,repo,(36,180,648,890));tx(im,(360,1133),'有需要的自取',33,'#a15336',True,'mm')
 if not 48<=i<410:
  tx(im,(36,1230),'AI生成画面 · 原有角色对白 · 教程仅步骤字幕',18,'#777168')
  ImageDraw.Draw(im).rectangle((36,1263,36+int(648*t/D),1268),fill='#a15336')
 return im

# Motion editorial version: real moving source footage plus animated teaching overlays.
intro_frames=[]
with av.open('C:/Users/Administrator/Desktop/MiniMax-H3/ComfyUI/output/video/Lulu_Yes_Work_01_00001_.mp4') as intro_container:
 for intro_frame in intro_container.decode(video=0):intro_frames.append(intro_frame.to_image().convert('RGB'))
def smooth(x):
 x=max(0,min(1,x));return 1-(1-x)**3
def moving(pic,size,progress,zoom=.045):
 w,h=size;base=ImageOps.fit(pic,size,Image.Resampling.LANCZOS)
 z=1+zoom*max(0,min(1,progress));base=base.resize((round(w*z),round(h*z)),Image.Resampling.LANCZOS)
 dx=(base.width-w)//2;dy=(base.height-h)//2
 return base.crop((dx,dy,dx+w,dy+h))
def shot(sec):
 return frames[min(len(frames)-1,max(0,round(sec*FPS)))].copy()
def caption(im,t):
 cues=[(0,2.45,'一天一个 Codex 小知识'),(2.45,4.75,'我们今天来学习 AI 小短剧'),(4.75,6,'先看成片'),
 (21.0833,22.7,'第一步，写好反转'),(22.7,25.25,'两个角色，一个矛盾，一个笑点'),
 (25.25,27.2,'第二步，准备角色参考图'),(27.2,29.4167,'定好外观、服装和场景'),
 (29.4167,31.4,'第三步，让 Codex 编排任务'),(31.4,33.5833,'交给本地 H3 生成'),
 (33.5833,35.2,'第四步，调整配音'),(35.2,38,'补上字幕、弹窗和音效'),
 (38.5,40.8,'成片和工作流已经免费公开'),(40.8,44,'有需要的自取')]
 sub=next((v for a,b,v in cues if a<=t<b),'')
 if sub:
  d=ImageDraw.Draw(im);width=d.textlength(sub,font=ft(29,True));x=max(18,(720-width-44)//2)
  box(im,(x,1124,720-x,1190),'#252623');tx(im,(360,1156),sub,29,'#ffffff',True,'mm')
def teaching_top(im,num,title):
 header(im,'实跑拆解');tx(im,(36,100),num,65,'#a15336',True);tx(im,(144,119),title,43,b=True)
def build(i):
 t=i/FPS
 if 144<=i<506:
  return legacy_build(i)
 im=Image.new('RGB',(720,1280),'#f4f0e9')
 if t<6:
  # Three moving shots replace the former six-second still.
  k=min(2,int(t/2));sec=[.5,4.2,10.5][k]+t%2
  source=intro_frames[min(len(intro_frames)-1,round(sec*FPS))].copy()
  im=moving(source,(720,1280),(t%2)/2,.035)
  shade=Image.new('RGBA',(720,1280));arr=np.zeros((1280,720,4),dtype=np.uint8);arr[:,:,:3]=np.array([8,15,20]);arr[:,:,3]=np.clip((np.arange(1280)[:,None]-650)*.38,0,215).astype(np.uint8)
  im=Image.alpha_composite(im.convert('RGBA'),Image.fromarray(arr)).convert('RGB')
  box(im,(32,32,430,88),'#18232b');tx(im,(52,48),'一天一个 Codex 小知识',25,'#f5f0e8',True)
  offset=round((1-smooth((t%2)/.35))*35)
  title=['AI短剧，怎么做？','先看真实成片','再拆完整流程'][k]
  tx(im,(40,875+offset),title,53,'white',True)
  tx(im,(42,961),['两个角色 · 一个反转','噜噜 × 噜妹','剧本 → 角色 → 生成 → 后期'][k],28,'#f3dfbf')
 elif t<25.25:
  u=t-506/24;teaching_top(im,'01','先写一个反转')
  srcf=shot(4+u);fit(im,srcf,(36,235,648,535))
  items=[('人物','噜噜嘴硬，噜妹拆台'),('矛盾','他天天抱怨工作太累'),('反转','原来只是在点 Yes')]
  for k,(label,body) in enumerate(items):
   y=795+k*90;off=round((1-smooth((u-k*.3)/.35))*65);highlight=min(2,int(u/1.2))==k
   box(im,(36+off,y,684+off,y+74),'#e7d0b9' if highlight else '#ffffff');tx(im,(56+off,y+22),label,23,'#a15336',True);tx(im,(143+off,y+20),body,27,b=True)
 elif t<29.416667:
  u=t-25.25;teaching_top(im,'02','定好角色')
  v=moving(ref,(648,770),u/4.1667,.065);im.paste(v,(36,235))
  for k,(name,y) in enumerate([('外观',330),('服装',530),('场景',790)]):
   if u>=k*.8:
    x=50+round((1-smooth((u-k*.8)/.3))*35);box(im,(x,y,x+123,y+54),'#29322d');tx(im,(x+22,y+12),name,25,'#fff6e9',True)
  tx(im,(360,1053),'同一对角色，沿用同一张参考图',27,'#615b53',True,'mm')
 elif t<33.583333:
  u=t-29.416667;teaching_top(im,'03','编排生成流程')
  for k,(title,desc) in enumerate([('角色参考 + 剧本','镜头 / 动作 / 对白 / 声场'),('Codex → ComfyUI','本地 MiniMax H3 工作流'),('视频生成结果','416 × 736 · 362帧 · 24fps')]):
   y=245+k*170;off=round((1-smooth((u-k*.28)/.35))*80);on=min(2,int(u/.95))==k
   box(im,(36+off,y,684+off,y+128),'#e7d0b9' if on else '#ffffff');tx(im,(61+off,y+20),title,31,b=True);tx(im,(61+off,y+76),desc,25,'#69645e')
   if k<2:tx(im,(360,y+150),'↓',27,'#a15336',True,'mm')
  # Actual animated result is shown beneath the explanatory flow diagram.
  fit(im,shot(u+5),(36,785,648,295));tx(im,(658,1045),'流程示意',18,'#a15336',False,'ra')
 elif t<38:
  u=t-33.583333;teaching_top(im,'04','补齐后期')
  fit(im,shot(3+u),(36,225,648,590))
  labels=[('画面','#91ad9d'),('角色对白','#ba9e75'),('字幕 / 弹窗','#b97d68')]
  for k,(label,col) in enumerate(labels):
   y=835+k*78;tx(im,(36,y+12),label,21,b=True)
   box(im,(183,y,684,y+51),'#e6e0d6')
   d=ImageDraw.Draw(im)
   for j in range(35):
    h=8+int(abs(np.sin(j*2.1+k+i*.18))*27);x=198+j*13
    d.rectangle((x,y+25-h//2,x+7,y+25+h//2),fill=col)
   x=193+int((u/4.4167)%1*477);d.line((x,y-3,x,y+54),fill='#292725',width=3)
  tx(im,(655,1085),'后期轨道示意',18,'#777168',False,'ra')
 else:
  header(im,'免费公开');tx(im,(36,102),'成片和流程，都在这里',43,b=True)
  # Gentle camera move keeps the real user-provided repository screenshot legible.
  fit(im,repo,(36,195,648,890))
  d=ImageDraw.Draw(im);d.rounded_rectangle((36,195,684,1085),radius=18,outline='#d5c4ae',width=2)
 caption(im,t)
 tx(im,(36,1230),'AI生成画面 · 合成解说 · 真实成片与流程示意',18,'#777168' if t>=6 else '#e5e0d8')
 ImageDraw.Draw(im).rectangle((36,1263,36+int(648*t/D),1268),fill='#a15336')
 return im

sheet=Image.new('RGB',(1080,1280))
for k,i in enumerate([18,82,540,654,840,970]):sheet.paste(build(i).resize((360,640)),((k%3)*360,(k//3)*640))
sheet.save(O/'动态精剪版-分镜预览.jpg')
import sys
if len(sys.argv)>1 and sys.argv[1]=='preview':sys.exit()
dst=O/'一天一个Codex小知识-AI短剧教程-动态精剪版.mp4';cursor=0
with av.open(str(dst),'w') as c:
 v=c.add_stream('libx264',rate=FPS);v.width=W;v.height=H;v.pix_fmt='yuv420p';v.options={'crf':'19','preset':'fast'}
 a=c.add_stream('aac',rate=SR);a.layout='stereo';a.bit_rate=160000
 for i in range(D*FPS):
  vf=av.VideoFrame.from_image(build(i));vf.pts=i;vf.time_base=Fraction(1,FPS)
  for pk in v.encode(vf):c.mux(pk)
  limit=(i+1)*SR//FPS
  while cursor<limit:
   end=min(cursor+1024,limit);af=av.AudioFrame.from_ndarray(np.ascontiguousarray(mix[:,cursor:end]),format='fltp',layout='stereo');af.sample_rate=SR;af.pts=cursor;af.time_base=Fraction(1,SR)
   for pk in a.encode(af):c.mux(pk)
   cursor=end
  if i%192==0:print('frame',i,flush=True)
 for pk in v.encode(None):c.mux(pk)
 for pk in a.encode(None):c.mux(pk)
with av.open(str(dst)) as c:
 s=c.streams.video[0];report={'width':s.width,'height':s.height,'fps':float(s.average_rate),'duration':float(s.duration*s.time_base),'frames':sum(1 for _ in c.decode(video=0)),'source_frames_preserved':362,'source_clip_start_seconds':6,'source_clip_end_seconds':506/24,'new_voiceover':True,'voice_segments':voice_report,'new_model_inference':False,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_audio_preserved_before_aac_encoding':True}
with av.open(str(dst)) as c:report['audio_samples']=sum(f.samples for f in c.decode(audio=0))
(O/'动态精剪版-制作核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
desktop=Path('C:/Users/Administrator/Desktop/AI短剧教程');desktop.mkdir(exist_ok=True);shutil.copy2(dst,desktop/dst.name);print(json.dumps(report,ensure_ascii=False))
