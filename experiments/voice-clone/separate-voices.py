from pathlib import Path
import av, numpy as np, torch, torchaudio, wave, json
root=Path(__file__).resolve().parent.parent
p=root/'work/voice_clone';p.mkdir(exist_ok=True)
torch.set_num_threads(6)
bundle=torchaudio.pipelines.HDEMUCS_HIGH_MUSDB_PLUS
model=bundle.get_model().cuda().eval()
def load(path):
    data=[];rs=av.AudioResampler(format='fltp',layout='stereo',rate=44100)
    with av.open(str(path)) as c:
        for f in c.decode(audio=0):data.extend(r.to_ndarray() for r in rs.resample(f))
        data.extend(r.to_ndarray() for r in rs.resample(None))
    return np.concatenate(data,axis=1)
def save(path,x,sr=44100):
    if x.ndim==1:x=x[None,:]
    with wave.open(str(path),'wb') as f:
        f.setnchannels(x.shape[0]);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((np.clip(x.T,-1,1)*32767).astype('<i2').tobytes())
for name,path in [('reference',root/'outputs/水豚噜噜角色素材包/来源视频.mp4'),('yes',root/'outputs/噜噜的工伤-只负责点Yes.mp4')]:
    x=load(path);ref=torch.from_numpy(x).cuda();mean=ref.mean();std=ref.std();xnorm=(ref-mean)/std
    result=torch.zeros((4,2,x.shape[1]),device='cuda');weights=torch.zeros(x.shape[1],device='cuda')
    chunk=44100*6;overlap=44100
    with torch.inference_mode():
        for start in range(0,x.shape[1],chunk-overlap):
            stop=min(start+chunk,x.shape[1]);v=model(xnorm[:,start:stop][None])[0]
            env=torch.ones(stop-start,device='cuda')
            if start:env[:overlap]=torch.linspace(0,1,overlap,device='cuda')
            if stop<x.shape[1]:env[-overlap:]=torch.linspace(1,0,overlap,device='cuda')
            result[:,:,start:stop]+=v*env;weights[start:stop]+=env
            if stop==x.shape[1]:break
    result=(result/weights.clamp_min(1e-6)*std).cpu().numpy()
    vocals=result[model.sources.index('vocals')];backing=result.sum(0)-vocals
    save(p/f'{name}_vocals.wav',vocals);save(p/f'{name}_backing.wav',backing)
    print(name,'separated',flush=True)
