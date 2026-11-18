import sys,json
sys.argv=[sys.argv[0],sys.argv[1],'[]']+sys.argv[2:]
exec(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'terrain.py')).read().split('SITES=json')[0])
for q in json.loads(sys.argv[3]):
    x,z=q[0],q[1]; ys=q[2] if len(q)>2 else range(62,70)
    print((x,z), [ (y,blockat(x,y,z)) for y in ys])
