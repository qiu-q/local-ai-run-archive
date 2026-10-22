from pathlib import Path
import json,urllib.request,copy
root=Path(__file__).resolve().parent.parent;p=root/'work/qwen_edit';p.mkdir(exist_ok=True)
g={
 '1':{'class_type':'UNETLoader','inputs':{'unet_name':'qwen_image_2.1_int8_convrot.safetensors','weight_dtype':'default'}},
 '2':{'class_type':'CLIPLoader','inputs':{'clip_name':'qwen3vl_8b_int8_convrot.safetensors','type':'qwen_image','device':'default'}},
 '3':{'class_type':'VAELoader','inputs':{'vae_name':'qwen_image_2.1_vae_bf16.safetensors'}},
 '4':{'class_type':'LoadImage','inputs':{'image':'portrait_model_denim.png'}},
 '5':{'class_type':'LoadImage','inputs':{'image':'clothing_light_blue_denim_shirt.png'}},
 '6':{'class_type':'TextEncodeQwenImage21','inputs':{'clip':['2',0],'vae':['3',0],'prompt':'','negative_prompt':'','resolution':768,'images.image_1':['4',0],'images.image_2':['5',0]}},
 '7':{'class_type':'QwenImage21Cache','inputs':{'model':['1',0],'device':'auto','dtype':'int8'}},
 '8':{'class_type':'KSampler','inputs':{'model':['7',0],'positive':['6',0],'negative':['6',1],'latent_image':['6',2],'seed':2285113,'steps':25,'cfg':1,'sampler_name':'euler','scheduler':'simple','denoise':1}},
 '9':{'class_type':'VAEDecode','inputs':{'samples':['8',0],'vae':['3',0]}},
 '10':{'class_type':'SaveImage','inputs':{'images':['9',0],'filename_prefix':'Qwen21_TryOn'}}}
g['6']['inputs']['prompt']='Edit <image1>: replace only the adult male model\'s dark green zip-neck top with the light blue denim button-up shirt shown in <image2>. Match the reference garment\'s light washed denim color, pointed collar, front button placket, single chest pocket, cuff construction, stitching and realistic denim texture. Fit the shirt naturally on his torso and shoulders, with correct fabric folds and perspective. Preserve the same person, face, skin tone, hair, downward head angle, body proportions, pose, camera crop, studio lighting and gray-blue background from <image1>. The shirt should be worn buttoned, not layered over the original green top. Remove the original green collar completely. Photorealistic fashion catalog quality. No added text or logos.'
cup=copy.deepcopy(g);cup.pop('5');cup['4']['inputs']['image']='sample_white_mug.jpg';cup['6']['inputs'].pop('images.image_2')
cup['6']['inputs']['prompt']='Edit <image1>: keep exactly the same plain white ceramic mug, its cylindrical body, rounded lip, smooth glossy glaze and curved handle on the right. Preserve its product shape, proportions, orientation and blank unprinted surface. Replace the plain gray tabletop and background with a refined cozy lifestyle product photography scene: place the mug on a light oak table next to a bright window, warm soft morning sunlight from the left, a folded beige linen napkin beside the mug, softly blurred green plants in the distant background. Keep the mug as the only drinkware, fully visible and the main subject. Natural contact shadow, realistic reflections, premium commercial photograph, calm warm neutral palette, no text, no logos, no people. Keep the existing camera angle and the mug position in the lower half of the portrait composition.'
cup['8']['inputs']['seed']=2285114;cup['10']['inputs']['filename_prefix']='Qwen21_Mug_Scene'
for name,graph in [('模特换装',g),('水杯换场景',cup)]:
 (p/f'{name}-API.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf-8')
 (p/f'{name}-提示词.txt').write_text(graph['6']['inputs']['prompt'],encoding='utf-8-sig')
if __name__=='__main__':
 import sys
 name=sys.argv[1] if len(sys.argv)>1 else '模特换装'
 graph=g if name=='模特换装' else cup
 req=urllib.request.Request('http://127.0.0.1:8188/prompt',data=json.dumps({'prompt':graph}).encode(),headers={'Content-Type':'application/json'})
 try:
  result=json.load(urllib.request.urlopen(req));(p/f'{name}-job.json').write_text(json.dumps(result));print(json.dumps(result))
 except urllib.error.HTTPError as e:print(e.read().decode());raise
