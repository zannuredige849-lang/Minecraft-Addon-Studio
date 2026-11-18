import sys
cx,cz,R,st=map(int,sys.argv[2:6])
sys.argv=[sys.argv[0],sys.argv[1],'[]']
exec(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'terrain.py')).read().split('SITES=json')[0])
for z in range(cz-R,cz+R+1,st):
    row=''
    for x in range(cx-R,cx+R+1,st):
        y,b=top(x,z)
        if not y or y<62: row+=' ~'
        else: row+='%2d'%min(99,y-60)
    print('%5d %s'%(z,row))
