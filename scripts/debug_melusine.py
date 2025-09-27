import json

# Load Mélusine data
with open('example_servant_data/312.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== Mélusine (312) Skill 3 Analysis ===")
skills_3 = [s for s in data['skills'] if s.get('num') == 3]
for i, skill in enumerate(skills_3):
    print(f"Skill {i+1}:")
    print(f"  ID: {skill.get('id')}")
    print(f"  Priority: {skill.get('priority')}")
    print(f"  Name: {skill.get('name')}")
    print()

print("=== All Skills Analysis ===")
for skill in data['skills']:
    print(f"Slot {skill.get('num')}: ID {skill.get('id')}, Priority {skill.get('priority')}, Name: {skill.get('name')}")