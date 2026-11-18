import json, os, re, sys, glob
from PIL import Image
W = sys.argv[1]
RP = glob.glob(W+'/resource_packs/*')[0]; BP = glob.glob(W+'/behavior_packs/*')[0]
issues=[]
def I(*a): issues.append(' '.join(str(x) for x in a))
def load(p):
    try:
        txt=open(p,encoding='utf-8-sig').read()
        txt=re.sub(r'^\s*//.*$','',txt,flags=re.M)
        return json.loads(txt)
    except Exception as e:
        I('JSON-ERR',p,e); return None
alljson={}
for root in (RP,BP):
    for p in glob.glob(root+'/**/*.json',recursive=True):
        alljson[p]=load(p)
# geometries
geos={}
for p in glob.glob(RP+'/models/**/*.json',recursive=True):
    d=alljson.get(p)
    if not d: continue
    for g in d.get('minecraft:geometry',[]):
        desc=g['description']; geos[desc['identifier']]=(p,g)
    for k,v in d.items():
        if k.startswith('geometry.'): I('LEGACY-GEO',p,k)
anims={}
for p in glob.glob(RP+'/animations/*.json'):
    d=alljson.get(p) or {}
    for k,v in d.get('animations',{}).items(): anims[k]=(p,v)
acs={}
for p in glob.glob(RP+'/animation_controllers/*.json'):
    d=alljson.get(p) or {}
    for k,v in d.get('animation_controllers',{}).items(): acs[k]=(p,v)
rcs={}
for p in glob.glob(RP+'/render_controllers/*.json'):
    d=alljson.get(p) or {}
    for k,v in d.get('render_controllers',{}).items(): rcs[k]=v
def tex_exists(t):
    return any(os.path.exists(RP+'/'+t+e) for e in ('.png','.tga'))
def tex_size(t):
    for e in ('.png','.tga'):
        if os.path.exists(RP+'/'+t+e): return Image.open(RP+'/'+t+e).size
# check geometry UVs against texture size and bones
def check_geo(gid, texpaths, where):
    if gid not in geos: I('MISSING-GEO',where,gid); return None
    p,g=geos[gid]; d=g['description']; tw,th=d.get('texture_width',64),d.get('texture_height',64)
    bones={b['name'] for b in g.get('bones',[])}
    names=[b['name'] for b in g.get('bones',[])]
    if len(names)!=len(set(names)): I('DUP-BONE',gid,[n for n in set(names) if names.count(n)>1])
    for b in g.get('bones',[]):
        if b.get('parent') and b['parent'] not in bones: I('BAD-PARENT',gid,b['name'],'->',b['parent'])
        for c in b.get('cubes',[]):
            uv=c.get('uv'); s=c['size']
            if isinstance(uv,list):
                u,v=uv; w=2*(s[0]+s[2]); h=s[2]+s[1]
                if u+w>tw+0.01 or v+h>th+0.01 or u<0 or v<0: I('UV-OOB',gid,b['name'],uv,s,'tex',tw,th)
            elif isinstance(uv,dict):
                for f,fd in uv.items():
                    u,v=fd['uv']; us,vs=fd.get('uv_size',[0,0])
                    for x in (u,u+us):
                        if x<-0.01 or x>tw+0.01: I('UV-OOB-face',gid,b['name'],f,fd,'tex',tw,th); break
                    for y in (v,v+vs):
                        if y<-0.01 or y>th+0.01: I('UV-OOB-face',gid,b['name'],f,fd,'tex',tw,th); break
    for t in texpaths:
        sz=tex_size(t)
        if sz and (sz[0]*th!=sz[1]*tw): I('TEX-RATIO',where,t,sz,'geo',tw,th)
    return bones
def bones_in_anim(a):
    return set((a.get('bones') or {}).keys())
used_anims=set()
for p in glob.glob(RP+'/entity/*.json'):
    d=alljson.get(p)
    if not d: continue
    ce=d['minecraft:client_entity']['description']; ident=ce['identifier']
    texs=ce.get('textures',{})
    for k,t in texs.items():
        if not tex_exists(t): I('MISSING-TEX',ident,k,t)
    allbones=set()
    for k,gid in ce.get('geometry',{}).items():
        b=check_geo(gid,list(texs.values()),ident); allbones|= (b or set())
    for k,a in ce.get('animations',{}).items():
        if a.startswith('controller.'):
            if a not in acs: I('MISSING-AC',ident,a)
            else:
                for st,sv in acs[a][1].get('states',{}).items():
                    for an in sv.get('animations',[]):
                        nm=an if isinstance(an,str) else list(an)[0]
                        if nm not in ce['animations']: I('AC-REF-UNDEFINED',ident,a,st,nm)
                    for tr in sv.get('transitions',[]):
                        for tgt in tr:
                            if tgt not in acs[a][1]['states']: I('AC-BAD-TRANSITION',a,st,tgt)
                    if 'initial_state' in acs[a][1] and acs[a][1]['initial_state'] not in acs[a][1]['states']: I('AC-BAD-INITIAL',a)
        else:
            used_anims.add(a)
            if a not in anims: I('MISSING-ANIM',ident,k,a)
            else:
                miss=bones_in_anim(anims[a][1])-allbones
                if miss: I('ANIM-UNKNOWN-BONES',ident,a,sorted(miss))
    for rc in ce.get('render_controllers',[]):
        rcn=rc if isinstance(rc,str) else list(rc)[0]
        if rcn not in rcs and not rcn.startswith('controller.render.default') : I('MISSING-RC',ident,rcn)
        elif rcn in rcs:
            for pv in rcs[rcn].get('part_visibility',[]):
                for bn in pv:
                    if bn!='*' and bn not in allbones and '*' not in bn: I('RC-UNKNOWN-BONE',ident,rcn,bn)
            for arr in rcs[rcn].get('arrays',{}).get('textures',{}).values():
                for t in arr:
                    if t.startswith('Texture.') and t[8:] not in texs: I('RC-UNKNOWN-TEX',ident,t)
    for k in ce.get('scripts',{}).get('animate',[]):
        nm=k if isinstance(k,str) else list(k)[0]
        if nm not in ce.get('animations',{}): I('ANIMATE-UNDEFINED',ident,nm)
    se=ce.get('sound_effects',{})
    # spawn egg / BP entity existence
    if not os.path.exists(BP+'/entities/'+os.path.basename(p).replace('.entity','')): I('NO-BP-ENTITY',ident)
for k in anims:
    if k not in used_anims: I('UNUSED-ANIM',k)
# attachables
for p in glob.glob(RP+'/attachables/*.json'):
    d=alljson.get(p)
    if not d: continue
    ce=d['minecraft:attachable']['description']; ident=ce['identifier']
    for k,t in ce.get('textures',{}).items():
        if not tex_exists(t) and not t.startswith('textures/misc/enchanted'): I('MISSING-TEX-ATT',ident,t)
    for k,gid in ce.get('geometry',{}).items(): check_geo(gid,[t for t in ce.get('textures',{}).values() if 'enchant' not in t],ident)
    for k,a in ce.get('animations',{}).items():
        if not a.startswith('controller.') and a not in anims: I('ATT-MISSING-ANIM',ident,a)
# item textures
it=alljson.get(RP+'/textures/item_texture.json') or {}
for k,v in it.get('texture_data',{}).items():
    t=v['textures'] if isinstance(v['textures'],str) else v['textures'][0]
    if not tex_exists(t): I('MISSING-ITEM-TEX',k,t)
for p in glob.glob(BP+'/items/*.json'):
    d=alljson.get(p)
    if not d: continue
    it_=d['minecraft:item']; comps=it_.get('components',{})
    icon=comps.get('minecraft:icon')
    ic = icon if isinstance(icon,str) else (icon or {}).get('texture') or ((icon or {}).get('textures') or {}).get('default')
    if ic not in it.get('texture_data',{}): I('ITEM-ICON-MISSING',it_['description']['identifier'],ic,'fmt',d.get('format_version'))
# sounds
sd=alljson.get(RP+'/sounds/sound_definitions.json') or {}
defs=sd.get('sound_definitions',sd)
for k,v in defs.items():
    if k=='format_version': continue
    for s in v.get('sounds',[]):
        n=s if isinstance(s,str) else s['name']
        if not any(os.path.exists(RP+'/'+n+e) for e in ('.ogg','.wav','.fsb')): I('MISSING-SOUND-FILE',k,n)
# sound ids used in scripts
used=set()
for p in glob.glob(BP+'/scripts/**/*.js',recursive=True):
    for m in re.findall(r'["\'`](odyssey\.[a-z_]+\.[a-z_0-9]+)["\'`]',open(p).read()): used.add(m)
for p in glob.glob(RP+'/**/*.json',recursive=True):
    for m in re.findall(r'"(odyssey\.[a-z_]+\.[a-z_0-9]+)"',open(p).read()): used.add(m)
langkeys=set()
for p in [RP+'/texts/en_US.lang',BP+'/texts/en_US.lang']:
    for line in open(p,encoding='utf-8'):
        if '=' in line: langkeys.add(line.split('=',1)[0].strip())
for u in sorted(used):
    if u not in defs and u not in langkeys: I('UNDEFINED-SOUND-OR-LANG',u)
for i in issues: print(i)
print('TOTAL',len(issues))
