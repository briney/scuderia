"""Exact official processor expansion with bounded image-array memory."""


import base64


import gc


import io


import os


from .io import require,SETTINGS,LIMIT,digest


MODEL_REPO='Qwen/Qwen3.8-27B'


REVISION='1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0'


# Cache path is an explicit deployment input.


def processor(cache):
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    from transformers import AutoProcessor
    return AutoProcessor.from_pretrained(MODEL_REPO,revision=REVISION,cache_dir=str(cache),token=False,trust_remote_code=False,local_files_only=True)


class Counter:
    def __init__(self,proc):
        self.proc=proc; self.images={}
    def count(self,wire):
        from PIL import Image
        proc=self.proc
        require(len(wire['messages'])==1 and wire['messages'][0]['role']=='user','count-one-user-message')
        parts=[]; replacements=[]; grids=[]
        merged=proc._merge_kwargs(proc.valid_processor_kwargs,tokenizer_init_kwargs=proc.tokenizer.init_kwargs,return_tensors='np')
        for part in wire['messages'][0]['content']:
            if part['type']=='text': parts.append(part); continue
            require(part['type']=='image_url','count-image-type')
            url=part['image_url']['url']; require(url.startswith('data:image/png;base64,'),'count-image-format')
            raw=base64.b64decode(url.split(',',1)[1],validate=True); h=digest(raw)
            if h not in self.images:
                image=Image.open(io.BytesIO(raw)).convert('RGB')
                data,repl=proc._process_images([image],**merged['images_kwargs'])
                grid=data['image_grid_thw'].tolist()[0]
                self.images[h]=(repl[0],grid)
                del data,image; gc.collect()
            repl,grid=self.images[h]; replacements.append(repl); grids.append(grid)
            parts.append(dict(type='image',image='source-image'))
        text=proc.apply_chat_template([dict(role='user',content=parts)],tokenize=False,add_generation_prompt=True)
        expanded,_=proc.get_text_with_replacements([text],images_replacements=replacements)
        kwargs=dict(merged['text_kwargs']); kwargs.pop('return_mm_token_type_ids',None); kwargs.pop('return_text_replacement_offsets',None)
        encoded=proc.tokenizer(expanded,**kwargs)
        n=len(encoded['input_ids'][0])
        image_tokens=sum(g[0]*g[1]*g[2]//(proc.image_processor.merge_size**2) for g in grids)
        return dict(prompt_tokens_local=n,image_tokens_local=image_tokens,image_grid_thw=grids,
            chat_template_tokens_before_image_expansion=len(proc.tokenizer.encode(text,add_special_tokens=False)),images=len(grids),
            reserved_completion_tokens=SETTINGS['max_tokens'],context_limit=LIMIT,fits=n+SETTINGS['max_tokens']<=LIMIT,
            model_repo=MODEL_REPO,revision=REVISION,local_files_only=True,
            method='Official processor image expansion, chat template and tokenizer; sequential arrays, no image/token estimate.')


def reference_full_count(proc,wire):
    """Reference algorithm copied from the accepted count_full_inputs.full_count."""
    from PIL import Image
    parts=[]; images=[]
    for part in wire['messages'][0]['content']:
        if part['type']=='text': parts.append(part)
        else:
            raw=base64.b64decode(part['image_url']['url'].split(',',1)[1],validate=True)
            image=Image.open(io.BytesIO(raw)).convert('RGB'); images.append(image)
            parts.append(dict(type='image',image=image))
    text=proc.apply_chat_template([dict(role='user',content=parts)],tokenize=False,add_generation_prompt=True)
    processed=proc(text=[text],images=images,return_tensors='np')
    return dict(prompt_tokens_local=len(processed['input_ids'][0]),image_grid_thw=processed['image_grid_thw'].tolist())
