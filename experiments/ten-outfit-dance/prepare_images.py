import json,urllib.request,copy
from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[1]
base=json.loads((root/'work/qwen_edit/水杯换场景-API.json').read_text(encoding='utf-8'))
base['4']['inputs']['image']='adult_dancer_reference.png'
base['6']['inputs']['resolution']=768
costumes=[
('01-JK黑丝','A navy-and-white Japanese collegiate inspired outfit for an adult fashion model: white short-sleeve blouse, navy ribbon bow, navy plaid pleated skirt ending above the knee, opaque black tights covering both legs, black loafers.'),
('02-洛丽塔白丝','An elegant pastel blue and ivory Lolita fashion dress, modest high neckline, puff sleeves, layered lace-trimmed knee-length bell skirt, small matching hair bow, opaque white tights and white Mary Jane shoes.'),
('03-经典女仆','A classic black and white cosplay maid costume: modest black knee-length dress with puff sleeves and white collar, crisp white apron and small lace headband, opaque white tights and black Mary Jane shoes.'),
('04-红白巫女','A traditional-inspired red and white shrine maiden cosplay: white wide-sleeved kimono top, red sash and long red hakama trousers reaching the ankles, white tabi socks and simple red sandals.'),
('05-蓝白魔法少女','A tasteful blue-and-white magical heroine cosplay for an adult: fitted white sailor-collar top, royal blue bow and knee-length blue pleated skirt, white gloves, opaque white tights, blue knee-high costume boots, a small blue hair bow.'),
('06-哥特洛丽塔','A black and burgundy Gothic Lolita fashion outfit: modest fitted high-neck bodice, lace puff sleeves, layered knee-length bell skirt, small burgundy hair bow, opaque black tights and black lace-up ankle boots.'),
('07-精灵幻想','An ivory and pale green fantasy elven heroine costume: opaque modest high-neck long-sleeve tunic dress to the knees, gold trim, thin gold belt, opaque cream leggings, elegant green ankle boots and a delicate gold leaf headband.'),
('08-未来战术服','A blue, white and silver futuristic game heroine cosplay: fully opaque tailored long-sleeve jacket with high collar, white fitted full-length trousers, blue belt and white boots. Fashionable practical fabric costume, no armor covering the face.'),
('09-魔女黑丝','A burgundy and black storybook witch cosplay: black knee-length dress with long sleeves, burgundy capelet, narrow belt, opaque black tights, black ankle boots and a small black pointed witch hat. Face clearly visible.'),
('10-粉白偶像','A pink and white idol stage cosplay: opaque modest white blouse with pink bow, short pastel pink jacket, layered knee-length pink-and-white skirt, opaque white tights, white ankle boots, and small pink hair ribbons.')]
common='Edit <image1>. This is the same original 22-year-old adult woman. Preserve her recognizable facial identity, chestnut brown long straight hair, skin tone and natural adult proportions. Make a photorealistic full-body fashion portrait of her in the same simple pale beige room and gray doorway. Move the camera back enough to show her entire head, legs and both shoes, with a small margin above and below. She stands naturally facing the camera, making a small heart with both hands at upper chest height, smiling gently. Replace her clothing with the following outfit, and remove the previous outfit completely: '
end=' Keep the same face and hairstyle; only add the listed small costume accessories. Natural soft daylight and realistic fabric details, coherent hands, two arms and two legs, no extra people, no text, no watermark. This is fully clothed adult fashion cosplay, opaque fabrics and normal catalog posing.'
jobs=[]
for i,(name,outfit) in enumerate(costumes):
 g=copy.deepcopy(base);g['6']['inputs']['prompt']=common+outfit+end;g['8']['inputs']['seed']=22612310+i;g['10']['inputs']['filename_prefix']='Outfit10/'+name
 (p/f'{name}-image-api.json').write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
 req=urllib.request.Request('http://127.0.0.1:8188/prompt',data=json.dumps({'prompt':g}).encode(),headers={'Content-Type':'application/json'})
 r=json.load(urllib.request.urlopen(req));jobs.append({'name':name,'outfit':outfit,'prompt_id':r['prompt_id']});print(i+1,r['prompt_id'],flush=True)
(p/'image_jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
