import sys,json
sys.argv=[sys.argv[0],sys.argv[1],'[]']+sys.argv[2:]
exec(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'terrain.py')).read().split('SITES=json')[0])
BAD={'oak_leaves','spruce_leaves','water','flowing_water','lava','glowstone','oak_fence','hay_block','dark_oak_log','oak_log','air',None,'lodestone','dandelion','poppy','short_grass','tall_grass'}
def safe(x,z,maxr=12):
    for r in range(0,maxr+1):
        for dx in range(-r,r+1):
            for dz in range(-r,r+1):
                if max(abs(dx),abs(dz))!=r: continue
                y,b=top(x+dx,z+dz)
                if y and y>=62 and b not in BAD and blockat(x+dx,y+1,z+dz) in ('air','short_grass','tall_grass','dandelion','poppy') and blockat(x+dx,y+2,z+dz)=='air':
                    return (x+dx,y+1,z+dz,b)
    return None
for q in json.loads(sys.argv[3]):
    print(q['name'], (q['x'],q['z']), '->', safe(q['x'],q['z'],q.get('r',12)))
