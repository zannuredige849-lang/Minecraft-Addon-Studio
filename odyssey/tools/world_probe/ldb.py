import sys,zlib,struct,glob,collections
def varint(b,i):
    r=s=0
    while True:
        c=b[i];i+=1;r|=(c&0x7f)<<s;s+=7
        if c<0x80: return r,i
def read_block(f,off,size):
    f.seek(off);raw=f.read(size+5);data,ct=raw[:size],raw[size]
    if ct==0: return data
    if ct in(2,): return zlib.decompress(data)
    if ct==4: return zlib.decompress(data,-15)
    raise Exception('comp %d'%ct)
def entries(blk):
    n=struct.unpack('<I',blk[-4:])[0]; end=len(blk)-4-4*n; i=0; last=b''
    while i<end:
        sh,i=varint(blk,i);ns,i=varint(blk,i);vl,i=varint(blk,i)
        k=last[:sh]+blk[i:i+ns];i+=ns;v=blk[i:i+vl];i+=vl;last=k
        yield k,v
def sst(path):
    with open(path,'rb') as f:
        f.seek(-48,2);ft=f.read(48);i=0
        _,i=varint(ft,i);_,i=varint(ft,i);io,i=varint(ft,i);isz,i=varint(ft,i)
        idx=read_block(f,io,isz)
        for k,v in entries(idx):
            o,j=varint(v,0);s,j=varint(v,j)
            for kk,vv in entries(read_block(f,o,s)): yield kk,vv
def log(path):
    data=open(path,'rb').read();i=0;rec=b''
    out=[]
    while i+7<=len(data):
        crc,ln,t=struct.unpack('<IHB',data[i:i+7]);i+=7;rec+=data[i:i+ln];i+=ln
        if t in(1,4):
            # batch
            seq,cnt=struct.unpack('<QI',rec[:12]);j=12
            for _ in range(cnt):
                tag=rec[j];j+=1;kl,j=varint(rec,j);k=rec[j:j+kl];j+=kl
                if tag==1: vl,j=varint(rec,j);v=rec[j:j+vl];j+=vl
                else: v=None
                out.append((k+b'\x00'*8,v))
            rec=b''
        if (i%32768)>32768-7: i+=32768-(i%32768)
    return out
def all_kv(db):
    d={}
    for p in sorted(glob.glob(db+'/*.ldb')):
        for k,v in sst(p): d[k[:-8]]=v
    for p in sorted(glob.glob(db+'/*.log')):
        for k,v in log(p):
            if v is None: d.pop(k[:-8],None)
            else: d[k[:-8]]=v
    return d
if __name__=='__main__':
    d=all_kv(sys.argv[1]); chunks=collections.Counter(); other=[]
    for k in d:
        if len(k) in (9,10,13,14) and k[8] in range(0x2b,0x80) or (len(k)>=9 and len(k)<=14):
            x,z=struct.unpack('<ii',k[:8]); chunks[(x,z)]+=1
        else: other.append(k)
    print('keys',len(d),'chunks',len(chunks))
    xs=[c[0] for c in chunks]; zs=[c[1] for c in chunks]
    if xs: print('chunk x',min(xs),max(xs),'z',min(zs),max(zs))
    print([k[:40] for k in d if not (9<=len(k)<=14)][:60])
