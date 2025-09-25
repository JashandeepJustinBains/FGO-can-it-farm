from units import skills
print('module file:', skills.__file__)
Skills = skills.Skills
print('Skills attrs:')
print('\n'.join(sorted([a for a in dir(Skills) if not a.startswith('__')])))
print('\nHas _collect_skill_svts_from_data? ->', hasattr(Skills, '_collect_skill_svts_from_data'))
