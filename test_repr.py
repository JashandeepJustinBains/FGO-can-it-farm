#!/usr/bin/env python3

# Simple test script to verify our repr implementations work

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test Skills repr
from units.skills import Skills

# Create test skills data
test_skills_data = [
    {
        'id': 1001,
        'name': 'Test Skill A',
        'num': 1,
        'coolDown': [0, 0, 0, 0, 0, 0, 0, 0, 0, 8],
        'functions': [
            {
                'funcType': 'addState',
                'funcTargetType': 'ptOne',
                'functvals': [],
                'svals': [{}] * 9 + [{'Value': 30, 'Turn': 3}],
                'buffs': [
                    {
                        'name': 'ATK Up',
                        'svals': [{}] * 9 + [{'Value': 30, 'Turn': 3}]
                    }
                ]
            }
        ]
    },
    {
        'id': 1002,
        'name': 'Test Skill A Enhanced',
        'num': 1,
        'coolDown': [0, 0, 0, 0, 0, 0, 0, 0, 0, 7],
        'functions': [
            {
                'funcType': 'addState',
                'funcTargetType': 'ptOne',
                'functvals': [],
                'svals': [{}] * 9 + [{'Value': 50, 'Turn': 3}],
                'buffs': [
                    {
                        'name': 'ATK Up',
                        'svals': [{}] * 9 + [{'Value': 50, 'Turn': 3}]
                    }
                ]
            }
        ]
    }
]

print("Testing Skills repr:")
skills = Skills(test_skills_data)
print(repr(skills))
print()

# Test NP repr
from units.np import NP

test_np_data = [
    {
        'id': 2001,
        'name': 'Test Noble Phantasm',
        'card': 'buster',
        'functions': [
            {
                'funcType': 'damageNp',
                'svals': [
                    {'Value': 600},
                    {'Value': 800}, 
                    {'Value': 900},
                    {'Value': 950},
                    {'Value': 1000}
                ],
                'svals2': [
                    {'Value': 700},
                    {'Value': 900}, 
                    {'Value': 1000},
                    {'Value': 1050},
                    {'Value': 1100}
                ]
            }
        ]
    },
    {
        'id': 2002,
        'name': 'Test Noble Phantasm Enhanced',
        'card': 'buster',
        'functions': [
            {
                'funcType': 'damageNp',
                'svals': [
                    {'Value': 800},
                    {'Value': 1000}, 
                    {'Value': 1100},
                    {'Value': 1150},
                    {'Value': 1200}
                ]
            }
        ]
    }
]

print("Testing NP repr:")
nps = NP(test_np_data)
print(repr(nps))
print()

print("All tests completed successfully!")