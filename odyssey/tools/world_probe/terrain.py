import sys,struct,collections,json
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ldb,nbt
DB=sys.argv[1]
kv=ldb.all_kv(DB)
sub={}
for k,v in kv.items():
    if len(k)==10 and k[8]==47:
        x,z=struct.unpack('<ii',k[:8]); y=struct.unpack('<b',k[9:10])[0]; sub[(x,z,y)]=v
def decode(v):
    ver=v[0]; i=1
    if ver==9: n=v[1]; i=3
    elif ver==8: n=v[1]; i=2
    else: return None
    hdr=v[i]; i+=1; bpb=hdr>>1
    if bpb==0:
        idx=[0]*4096
    else:
        bpw=32//bpb; nw=(4096+bpw-1)//bpw
        words=struct.unpack_from('<%dI'%nw,v,i); i+=4*nw; idx=[]
        mask=(1<<bpb)-1
        for w in words:
            for j in range(bpw):
                idx.append((w>>(j*bpb))&mask)
        idx=idx[:4096]
    ps=struct.unpack_from('<i',v,i)[0]; i+=4; pal=[]
    for _ in range(ps):
        d,i=nbt.root(v,i); pal.append(d.get('name'))
    return idx,pal  # index = x*256+z*16+y
cache={}
def blockat(x,y,z):
    cx,cz,cy=x>>4,z>>4,y>>4
    key=(cx,cz,cy)
    if key not in cache:
        cache[key]=decode(sub[key]) if key in sub else None
    d=cache[key]
    if d is None: return 'stone' if y<40 else ('water' if y<62 else 'air') if key not in sub else None
    idx,pal=d; lx,ly,lz=x&15,y&15,z&15
    return pal[idx[lx*256+lz*16+ly]].replace('minecraft:','')
def top(x,z):
    for y in range(140,30,-1):
        b=blockat(x,y,z)
        if b not in ('air','water','flowing_water',None,'seagrass','kelp','tall_grass','short_grass','light_block'):
            return y,b
    return None,None
SITES=json.loads(sys.argv[2])
for s in SITES:
    cnt=collections.Counter(); hs=[]
    for dx in range(-s['r'],s['r']+1,3):
        for dz in range(-s['r'],s['r']+1,3):
            y,b=top(s['x']+dx,s['z']+dz)
            if y and y>=62: cnt[b]+=1; hs.append(y)
    cy,cb=top(s['x'],s['z'])
    print(s['id'],'center',(s['x'],cy,s['z']),cb,'land cols',len(hs),'maxh',max(hs) if hs else None,'top blocks',cnt.most_common(8))
