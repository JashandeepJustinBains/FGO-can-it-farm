import json
from units.skills import Skills
p='f:/FGO-opensource/FGO-can-it-farm/example_servant_data/1.json'
with open(p,'r',encoding='utf-8') as f:
    data=json.load(f)
# Call helper as unbound method to avoid constructing Skills
inst = object.__new__(Skills)
found = Skills._collect_skill_svts_from_data(inst, data)
print('found skillSvts count=', len(found))
for i,e in enumerate(found[:12]):
    print(i, e.get('svtId'), e.get('num'), e.get('priority'))
