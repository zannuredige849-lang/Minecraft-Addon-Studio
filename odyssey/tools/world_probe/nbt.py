import struct
def rd(b,i,t):
    if t==1: return struct.unpack_from('<b',b,i)[0],i+1
    if t==2: return struct.unpack_from('<h',b,i)[0],i+2
    if t==3: return struct.unpack_from('<i',b,i)[0],i+4
    if t==4: return struct.unpack_from('<q',b,i)[0],i+8
    if t==5: return struct.unpack_from('<f',b,i)[0],i+4
    if t==6: return struct.unpack_from('<d',b,i)[0],i+8
    if t==7: n=struct.unpack_from('<i',b,i)[0];return b[i+4:i+4+n],i+4+n
    if t==8: n=struct.unpack_from('<H',b,i)[0];return b[i+2:i+2+n].decode('utf8','replace'),i+2+n
    if t==9:
        et=b[i];n=struct.unpack_from('<i',b,i+1)[0];i+=5;l=[]
        for _ in range(n): v,i=rd(b,i,et);l.append(v)
        return l,i
    if t==10:
        d={}
        while True:
            tt=b[i];i+=1
            if tt==0: return d,i
            n=struct.unpack_from('<H',b,i)[0];k=b[i+2:i+2+n].decode('utf8','replace');i+=2+n
            d[k],i=rd(b,i,tt)
    if t==11: n=struct.unpack_from('<i',b,i)[0];return list(struct.unpack_from('<%di'%n,b,i+4)),i+4+4*n
    if t==12: n=struct.unpack_from('<i',b,i)[0];return list(struct.unpack_from('<%dq'%n,b,i+4)),i+4+8*n
    raise Exception('tag %d'%t)
def root(b,i=0):
    t=b[i];n=struct.unpack_from('<H',b,i+1)[0];i+=3+n
    return rd(b,i,t)
