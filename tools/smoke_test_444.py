import sys
sys.path.insert(0, r"f:\FGO-opensource\FGO-can-it-farm")
from units.Servant import Servant

def print_skills(s):
    print(f"Servant {s.id} name={s.name} ascension={s.ascension} variant={s.variant_svt_id}")
    for i in range(1,4):
        try:
            sk = s.skills.get_skill_by_num(i)
            if sk:
                print(f" slot {i}: id={sk.get('id')} name={sk.get('name')} cooldown={sk.get('cooldown')}")
            else:
                print(f" slot {i}: <None>")
        except Exception as e:
            print(f" slot {i}: error {e}")

if __name__ == '__main__':
    s = Servant(444, ascension=1)
    print_skills(s)
    print('\n--- Changing ascension to 3 ---\n')
    s.change_ascension(3)
    print_skills(s)
