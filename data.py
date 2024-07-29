from bidict import bidict

traits_dict={
    "2": "genderFemale",
    "107": "classShielder",
    "201": "attributeEarth",
    "300": "alignmentLawful",
    "303": "alignmentGood",
    "403": "threeStarServant",
    "1000": "servant",
    "2001": "humanoid",
    "2008": "weakToEnumaElish",
    "2009": "riding",
    "2011": "skyOrEarthServant",
    "2631": "hominidaeServant",
    "2654": "livingHuman",
    "2780": "hasCostume",
    "2795": "knightsOfTheRound",
    "5000": "canBeInBattle",
    "800100": "unknown",
    "3": "genderUnknown",
    "100": "classSaber",
    "202": "attributeHuman",
    "302": "alignmentNeutral",
    "305": "alignmentBalanced",
    "404": "fourStarServant",
    "2075": "saberClassServant",
    "2356": "feminineLookingServant",
    "2858": "standardClassServant",
    "102600": "unknown",
    "104": "classCaster",
    "301": "alignmentChaotic",
    "502300": "unknown",
    "1": "genderMale",
    "200": "attributeSky",
    "2000": "divine",
    "2012": "brynhildsBeloved",
    "2037": "skyOrEarthExceptPseudoAndDemiServant",
    "2040": "divineOrDemonOrUndead",
    "2113": "king",
    "2851": "servantsWithSkyAttribute",
    "101900": "unknown",
    "101": "classLancer",
    "304": "alignmentEvil",
    "301700": "unknown",
    "502500": "unknown",
    "501600": "unknown",
    "102": "classArcher",
    "201000": "unknown",
    "110": "classAvenger",
    "405": "fiveStarServant",
    "2007": "saberface",
    "1100300": "unknown",
    "400": "zeroStarServant",
    "1100100": "unknown",
    "103": "classRider",
    "2114": "greekMythologyMales",
    "400200": "unknown",
    "105": "classAssassin",
    "601500": "unknown",
    "2883": "FSNServant",
    "200100": "unknown",
    "600300": "unknown",
    "502000": "unknown",
    "1004": "demonBeast",
    "1132": "oni",
    "2002": "dragon",
    "2019": "demonic",
    "2734": "shuten",
    "602100": "unknown",
    "502200": "unknown",
    "106": "classBerserker",
    "2735": "genji",
    "702300": "unknown",
    "2810": "fairyTaleServant",
    "402300": "unknown",
    "2667": "childServant",
    "702200": "unknown",
    "601900": "unknown",
    "401200": "unknown",
    "2010": "arthur",
    "302000": "unknown",
    "200200": "unknown",
    "2797": "divineSpirit",
    "501200": "unknown",
    "102000": "unknown",
    "200800": "unknown",
    "100700": "unknown",
    "600900": "unknown",
    "201400": "unknown",
    "203": "attributeStar",
    "101200": "unknown",
    "500900": "unknown",
    "308": "alignmentSummer",
    "2632": "demonicBeastServant",
    "2838": "summerModeServant",
    "2850": "hasGoddessMetamorphosis",
    "302400": "unknown",
    "202600": "unknown",
    "200300": "unknown",
    "502700": "unknown",
    "2881": "groupServant",
    "202500": "unknown",
    "402400": "unknown",
    "602400": "unknown",
    "302500": "unknown",
    "108": "classRuler",
    "900400": "unknown",
    "2355": "illya",
    "502800": "unknown",
    "202700": "unknown",
    "101000": "unknown",
    "2847": "levitating",
    "600800": "unknown",
    "2006": "moon",
    "2466": "associatedToTheArgo",
    "200500": "unknown",
    "2849": "defender",
    "300300": "unknown",
    "302600": "unknown",
    "2835": "immuneToPigify",
    "202000": "unknown",
    "300800": "unknown",
    "401800": "unknown",
    "501800": "unknown",
    "302700": "unknown",
    "1100400": "unknown",
    "2005": "wildbeast",
    "302800": "unknown",
    "114": "classBeastII",
    "204": "attributeBeast",
    "9935400": "unknown",
    "201200": "unknown",
    "500800": "unknown",
    "113": "classBeastI",
    "9935530": "unknown",
    "101700": "unknown",
    "602500": "unknown",
    "702400": "unknown",
    "202300": "unknown",
    "201600": "unknown",
    "1100500": "unknown",
    "2840": "ryozanpaku",
    "602600": "unknown",
    "401": "oneStarServant",
    "201300": "unknown",
    "102900": "unknown",
    "2839": "shinsengumiServant",
    "702500": "unknown",
    "702600": "unknown",
    "109": "classAlterEgo",
    "2781": "mechanical",
    "1000200": "unknown",
    "1000100": "unknown",
    "103000": "unknown",
    "115": "classMoonCancer",
    "2300100": "unknown",
    "1000300": "unknown",
    "116": "classBeastIIIR",
    "9939130": "unknown",
    "503000": "unknown",
    "300100": "unknown",
    "602700": "unknown",
    "702700": "unknown",
    "402500": "unknown",
    "900500": "unknown",
    "2666": "giant",
    "702800": "unknown",
    "2004": "roman",
    "503200": "unknown",
    "103100": "unknown",
    "602800": "unknown",
    "2721": "nobunaga",
    "702900": "unknown",
    "402700": "unknown",
    "300500": "unknown",
    "202800": "unknown",
    "302900": "unknown",
    "402600": "unknown",
    "303000": "unknown",
    "202100": "unknown",
    "602900": "unknown",
    "301400": "unknown",
    "103200": "unknown",
    "603000": "unknown",
    "603100": "unknown",
    "402": "twoStarServant",
    "300600": "unknown",
    "1172": "threatToHumanity",
    "1000400": "unknown",
    "1000500": "unknown",
    "503300": "unknown",
    "303100": "unknown",
    "503400": "unknown",
    "117": "classForeigner",
    "2731": "existenceOutsideTheDomain",
    "2500100": "unknown",
    "303200": "unknown",
    "202200": "unknown",
    "2500200": "unknown",
    "603200": "unknown",
    "100100": "unknown",
    "300700": "unknown",
    "202900": "unknown",
    "503500": "unknown",
    "703000": "unknown",
    "503600": "unknown",
    "1100600": "unknown",
    "402800": "unknown",
    "402900": "unknown",
    "203000": "unknown",
    "503800": "unknown",
    "1000700": "unknown",
    "300900": "unknown",
    "603300": "unknown",
    "403000": "unknown",
    "203100": "unknown",
    "103300": "unknown",
    "2837": "valkyrie",
    "303300": "unknown",
    "503900": "unknown",
    "203200": "unknown",
    "303400": "unknown",
    "603400": "unknown",
    "703100": "unknown",
    "301000": "unknown",
    "2076": "superGiant",
    "2300200": "unknown",
    "103400": "unknown",
    "2500300": "unknown",
    "103500": "unknown",
    "1000800": "unknown",
    "504000": "unknown",
    "703200": "unknown",
    "103600": "unknown",
    "303500": "unknown",
    "900600": "unknown",
    "400100": "unknown",
    "2833": "yuMeiren",
    "603500": "unknown",
    "403100": "unknown",
    "303600": "unknown",
    "900700": "unknown",
    "103700": "unknown",
    "603600": "unknown",
    "504100": "unknown",
    "504200": "unknown",
    "1000900": "unknown",
    "603700": "unknown",
    "2003": "dragonSlayer",
    "400600": "unknown",
    "118": "classBeastIIIL",
    "9941730": "unknown",
    "403200": "unknown",
    "900800": "unknown",
    "603900": "unknown",
    "2848": "obstacleMaker",
    "2300300": "unknown",
    "103900": "unknown",
    "203400": "unknown",
    "703300": "unknown",
    "203300": "unknown",
    "504300": "unknown",
    "400800": "unknown",
    "1100700": "unknown",
    "306": "alignmentMadness",
    "703500": "unknown",
    "303800": "unknown",
    "403500": "unknown",
    "103800": "unknown",
    "203500": "unknown",
    "303900": "unknown",
    "403400": "unknown",
    "504400": "unknown",
    "603800": "unknown",
    "401100": "unknown",
    "703400": "unknown",
    "703600": "unknown",
    "203600": "unknown",
    "403600": "unknown",
    "104000": "unknown",
    "900900": "unknown",
    "304000": "unknown",
    "604000": "unknown",
    "1100900": "unknown",
    "203700": "unknown",
    "401400": "unknown",
    "104100": "unknown",
    "203900": "unknown",
    "203800": "unknown",
    "403900": "unknown",
    "404000": "unknown",
    "2500400": "unknown",
    "204000": "unknown",
    "403800": "unknown",
    "104200": "unknown",
    "2615": "genderCaenisServant",
    "304100": "unknown",
    "401500": "unknown",
    "304200": "unknown",
    "2500500": "unknown",
    "703700": "unknown",
    "304300": "unknown",
    "504500": "unknown",
    "2300400": "unknown",
    "204200": "unknown",
    "703800": "unknown",
    "304400": "unknown",
    "2500700": "unknown",
    "401700": "unknown",
    "104500": "unknown",
    "404100": "unknown",
    "901000": "unknown",
    "104400": "unknown",
    "204100": "unknown",
    "2500600": "unknown",
    "403700": "unknown",
    "1001000": "unknown",
    "104700": "unknown",
    "104600": "unknown",
    "100200": "unknown",
    "401900": "unknown",
    "304600": "unknown",
    "104800": "unknown",
    "104900": "unknown",
    "1101000": "unknown",
    "604100": "unknown",
    "901100": "unknown",
    "703900": "unknown",
    "504600": "unknown",
    "2500800": "unknown",
    "1177": "fae",
    "704000": "unknown",
    "500100": "unknown",
    "105000": "unknown",
    "204300": "unknown",
    "304800": "unknown",
    "304700": "unknown",
    "604200": "unknown",
    "404200": "unknown",
    "120": "classPretender",
    "2800100": "unknown",
    "105100": "unknown",
    "204400": "unknown",
    "504800": "unknown",
    "500200": "unknown",
    "901200": "unknown",
    "1101100": "unknown",
    "404500": "unknown",
    "704100": "unknown",
    "2501000": "unknown",
    "204500": "unknown",
    "404600": "unknown",
    "504900": "unknown",
    "1101200": "unknown",
    "305000": "unknown",
    "500500": "unknown",
    "505000": "unknown",
    "404300": "unknown",
    "404400": "unknown",
    "121": "classBeastIV",
    "5010": "notBasedOnServant",
    "2500900": "unknown",
    "2800200": "unknown",
    "1001100": "unknown",
    "105300": "unknown",
    "1001200": "unknown",
    "1001300": "unknown",
    "500700": "unknown",
    "2821": "havingAnimalsCharacteristics",
    "504700": "unknown",
    "304900": "unknown",
    "404700": "unknown",
    "105200": "unknown",
    "104300": "unknown",
    "704200": "unknown",
    "901300": "unknown",
    "305100": "unknown",
    "505100": "unknown",
    "404800": "unknown",
    "501400": "unknown",
    "204600": "unknown",
    "1001400": "unknown",
    "2800300": "unknown",
    "105400": "unknown",
    "704300": "unknown",
    "1101400": "unknown",
    "901400": "unknown",
    "505200": "unknown",
    "604500": "unknown",
    "501500": "unknown",
    "604400": "unknown",
    "604300": "unknown",
    "704400": "unknown",
    "105500": "unknown",
    "901500": "unknown",
    "604600": "unknown",
    "404900": "unknown",
    "2800400": "unknown",
    "305300": "unknown",
    "1001500": "unknown",
    "501900": "unknown",
    "1101500": "unknown",
    "604700": "unknown",
    "2800500": "unknown",
    "2501100": "unknown",
    "901600": "unknown",
    "204700": "unknown",
    "1001600": "unknown",
    "124": "classBeast",
    "3300100": "unknown",
    "604800": "unknown",
    "105700": "unknown",
    "502100": "unknown",
    "604900": "unknown",
    "305400": "unknown",
    "704600": "unknown",
    "204800": "unknown",
    "105600": "unknown",
    "505300": "unknown",
    "704700": "unknown",
    "405000": "unknown",
    "1101600": "unknown",
    "2501200": "unknown",
    "600100": "unknown",
    "901700": "unknown",
    "204900": "unknown",
    "2800600": "unknown",
    "2501300": "unknown",
    "205000": "unknown",
    "205100": "unknown",
    "105800": "unknown",
    "405200": "unknown",
    "704800": "unknown",
    "205200": "unknown",
    "100300": "unknown",
    "600200": "unknown",
    "901800": "unknown",
    "405300": "unknown",
    "105900": "unknown",
    "1101800": "unknown",
    "505400": "unknown",
    "106000": "unknown",
    "405500": "unknown",
    "1101300": "unknown",
    "605000": "unknown",
    "1101700": "unknown",
    "601000": "unknown",
    "2800700": "unknown",
    "127": "classUOlgaMarieFlare",
    "128": "unknown",
    "2501400": "unknown",
    "704900": "unknown",
    "505500": "unknown",
    "1001700": "unknown",
    "601100": "unknown",
    "601200": "unknown",
    "601300": "unknown",
    "601400": "unknown",
    "601700": "unknown",
    "700100": "unknown",
    "700200": "unknown",
    "700300": "unknown",
    "100500": "unknown",
    "700500": "unknown",
    "700600": "unknown",
    "700700": "unknown",
    "700900": "unknown",
    "701000": "unknown",
    "701100": "unknown",
    "701300": "unknown",
    "701500": "unknown",
    "701600": "unknown",
    "900100": "unknown",
    "100800": "unknown",
    "200900": "unknown",
    "502600": "unknown",
    "500300": "unknown",
    "200600": "unknown",
    "301600": "unknown",
    "400300": "unknown",
    "400900": "unknown",
    "501700": "unknown",
    "102700": "unknown",
    "202400": "unknown",
    "101300": "unknown",
    "301300": "unknown",
    "300200": "unknown",
    "101400": "unknown",
    "402200": "unknown",
    "500400": "unknown",
    "600500": "unknown",
    "100900": "unknown",
    "201100": "unknown",
    "301900": "unknown",
    "501000": "unknown",
    "101800": "unknown",
    "501100": "unknown",
    "600700": "unknown",
    "700400": "unknown",
    "112": "classGrandCaster",
    "1700100": "unknown",
    "201500": "unknown",
    "300400": "unknown",
    "601800": "unknown",
    "301100": "unknown",
    "301200": "unknown",
    "700800": "unknown",
    "102200": "unknown",
    "100600": "unknown",
    "102800": "unknown",
    "602300": "unknown",
    "900200": "unknown",
    "400400": "unknown",
    "201800": "unknown",
    "1100200": "unknown",
    "701400": "unknown",
    "702000": "unknown",
    "401300": "unknown",
    "6000": "unknown",
    "6001": "unknown",
    "6002": "unknown",
    "9941880": "unknown",
    "1003": "artificialDemon",
    "2720": "unknown",
    "1118": "dragonType",
    "1001": "human",
    "1002": "undead",
    "2018": "undeadOrDemon",
    "1110": "lamia",
    "1122": "shadow",
    "1104": "ghost",
    "1117": "wyvern",
    "2241": "unknown",
    "2568": "unknown",
    "2227": "unknown",
    "2233": "unknown",
    "1102": "skeleton",
    "1106": "golem",
    "2768": "unknown",
    "2769": "unknown",
    "2770": "unknown",
    "2771": "unknown",
    "2772": "unknown",
    "1105": "automata",
    "9942100": "unknown",
    "1113": "chimera",
    "1107": "spellBook",
    "1005": "demonUnused",
    "1121": "demonGodPillar",
    "6036": "unknown",
    "2863": "unknown",
    "2866": "unknown",
    "2868": "unknown",
    "2870": "unknown",
    "2864": "unknown",
    "2869": "unknown",
    "2865": "unknown",
    "2867": "unknown",
    "9936990": "unknown",
    "9936980": "unknown",
    "2808": "unknown",
    "1108": "homunculus",
    "1119": "demon",
    "2807": "unknown",
    "2687": "unknown",
    "2882": "unknown",
    "2050": "unknown",
    "2015": "unknown",
    "2049": "unknown",
    "2178": "unknown",
    "2430": "unknown",
    "2552": "unknown",
    "2567": "unknown",
    "2565": "unknown",
    "2554": "unknown",
    "2556": "unknown",
    "2557": "unknown",
    "2235": "unknown",
    "2551": "unknown",
    "2555": "unknown",
    "1120": "handOrDoor",
    "1133": "hand",
    "2174": "unknown",
    "2481": "unknown",
    "6021": "unknown",
    "9942000": "unknown",
    "2239": "unknown",
    "2749": "enemyLittleBigTenguTsuwamonoEnemy",
    "2757": "unknown",
    "2417": "unknown",
    "2079": "unknown",
    "2815": "unknown",
    "2812": "unknown",
    "1100": "soldier",
    "2814": "unknown",
    "6034": "unknown",
    "6035": "unknown",
    "2679": "unknown",
    "1112": "werebeast",
    "2900": "unknown",
    "2902": "unknown",
    "1103": "zombie",
    "2688": "unknown",
    "2017": "unknown",
    "2047": "unknown",
    "1134": "door",
    "9939140": "unknown",
    "2891": "unknown",
    "2501500": "unknown",
    "2480": "unknown",
    "9939210": "unknown",
    "2813": "unknown",
    "2550": "unknown",
    "2232": "unknown",
    "2549": "unknown",
    "2806": "unknown",
    "6026": "unknown",
    "6027": "unknown"
}
# base damage multiplier for classes
base_multipliers = [
    1.0,  # Shielder
    1.0,  # Saber
    0.95, # Archer
    1.05, # Lancer
    1.0,  # Rider
    0.9,  # Caster
    0.9,  # Assassin
    1.1,  # Berserker
    1.1,  # Ruler
    1.1,  # Avenger
    1.0,  # MoonCancer
    1.0,  # Alterego
    1.0,  # Foreigner
    1.0,  # Pretender
]

# class indices used for getting correct class advantage
class_indices = bidict({ # character.className
    "shielder": 0,
    "saber": 1,
    "archer": 2,
    "lancer": 3,
    "rider": 4,
    "caster": 5,
    "assassin": 6,
    "berserker": 7,
    "ruler": 8,
    "avenger": 9,
    "moonCancer": 10,
    "alterEgo": 11,
    "foreigner": 12,
    "pretender": 13,
    "beast": 14
})

#
attribute = [
    # MAN EARTH SKY STAR BEAST 
    [1, 0.9, 1.1, 1, 1], # MAN
    [1.1, 1, 0.9, 1, 1], # EARTH
    [0.9, 1.1, 1, 1, 1], # SKY
    [1, 1, 1, 1, 1.1],   # STAR
    [1, 1, 1, 1.1, 1]    # BEAST
]

#
class_advantage_matrix = [
    # Shielder
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    # Saber
    [1.0, 0.5, 2.0, 1.0, 1.0, 1.0, 2.0, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5, 1.0],
    # Archer
    [1.0, 2.0, 0.5, 1.0, 1.0, 1.0, 2.0, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5, 1.0],
    # Lancer
    [1.0, 0.5, 2.0, 1.0, 1.0, 1.0, 2.0, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5, 1.0],
    # Rider
    [1.0, 1.0, 1.0, 1.0, 2.0, 0.5, 2.0, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5, 2.0],
    # Caster
    [1.0, 1.0, 1.0, 0.5, 1.0, 2.0, 2.0, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5, 2.0],
    # Assassin
    [1.0, 1.0, 1.0, 2.0, 0.5, 1.0, 2.0, 0.5, 1.0, 1.0, 1.0, 1.0, 0.5, 2.0],
    # Berserker
    [1.0, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 0.5, 1.5],
    # Ruler
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 0.5, 2.0, 1.0, 1.0, 2.0, 1.0],
    # Avenger
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 1.0, 0.5, 1.0, 1.0, 2.0, 1.0],
    # MoonCancer
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 0.5, 2.0, 1.0, 1.0, 1.0, 2.0, 1.0],
    # Alterego
    [1.0, 0.5, 0.5, 0.5, 1.5, 1.5, 1.5, 2.0, 1.0, 1.0, 1.0, 2.0, 0.5, 2.0],
    # Foreigner
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 1.0, 1.0, 1.0, 0.5, 2.0, 2.0, 2.0],
    # Pretender
    [1.0, 1.5, 1.5, 1.5, 0.5, 0.5, 0.5, 2.0, 1.0, 1.0, 1.0, 2.0, 0.5, 2.0]
]

#
character_list = bidict({
    1:"Mash",
    10:"d'Eon",
    100:"Blavatsky",
    101:"Rama",
    102:"Li Shuwen",
    103:"Thomas Edison",
    104:"Geronimo",
    105:"Billy",
    106:"Jeanne Alter",
    107:"A┼ïra Mainiiu",
    108:"Iskandar",
    109:"Emiya (Assassin)",
    11:"Emiya",
    110:"Hassan of the Hundred Personas",
    111:"Iri",
    112:"Shuten-Douji",
    113:"Xuanzang Sanzang",
    114:"Minamoto-no-Raikou",
    115:"Sakata Kintoki (Rider)",
    116:"Ibaraki-Douji",
    117:"Fuuma \"Evil-wind\" Kotarou",
    118:"Ozymandias",
    119:"Altria (Lancer)",
    12:"Gilgamesh",
    120:"Nitocris",
    121:"Lancelot (Saber)",
    122:"Tristan",
    123:"Gawain",
    124:"Hassan of the Serenity",
    125:"Tawara Touta",
    126:"Bedivere",
    127:"Da Vinci",
    128:"Tamamo Summer",
    129:"Altria (Summer)",
    13:"Robin Hood",
    130:"Marie Antoinette (Caster)",
    131:"Anne Bonny",
    132:"Mordred (Summer)",
    133:"Sc├í (Assassin)",
    134:"Kiyohime (Lancer)",
    135:"Martha (Ruler)",
    136:"Illya",
    137:"Chloe",
    138:"Elisabeth (saber Brave)",
    139:"Cleopatra",
    14:"Atalante",
    140:"Vlad III (Lancer)",
    141:"Jeanne Alter Santa Lily",
    142:"Ishtar",
    143:"Enkidu",
    144:"Quetzalcoatl",
    145:"Gilgamesh (kid)",
    146:"Medusa (Lancer)",
    147:"Gorgon",
    148:"Jaguar Warrior",
    # 149:"Tiamat", # ignore
    15:"Euryale",
    150:"Merlin",
    # 151:"Demon King Goetia", # ignore
    # 152:"King Solomon", # ignore
    153:"Miyamoto Musashi",
    154:"\"First Hassan\"",
    155:"Heroine X Alter",
    156:"Moriarty",
    157:"Emiya Alter",
    158:"Hessian Lobo",
    159:"Yan Qing",
    16:"Arash",
    160:"Arthur",
    161:"Hijikata Toshizo",
    162:"Chacha",
    163:"Meltryllis",
    164:"Passionlip",
    165:"Suzuka Gozen",
    166:"BB",
    167:"Sessyoin Kiara",
    # 168:"Heaven's Hole", # ignore
    169:"Scheherazade",
    17:"C├║ Chulainn",
    170:"Wu Zetian",
    171:"Penthesilea",
    172:"Columbus",
    173:"Sherlock Holmes",
    174:"Bunyan",
    175:"Nero (Caster)",
    176:"Fran (Summer)",
    177:"Nitocris (Assassin)",
    178:"Oda Nobunaga (Berserker)",
    179:"Maid Alter",
    18:"Elisabeth (Lancer)",
    180:"Blavatsky (Archer)",
    181:"Minamoto-no-Raikou (Lancer)",
    182:"Ishtar (Summer)",
    183:"P─ürvat─½",
    184:"Tomoe Gozen",
    185:"Mochizuki Chiyome",
    186:"Houzouin Inshun",
    187:"Yagyu Tajima-no-kami",
    188:"Katou \"Black Kite\" Danzo",
    189:"Osakabehime",
    19:"Benkei",
    190:"Mecha Eli-chan",
    191:"Mecha Eli-chan Mk.II",
    192:"Circe",
    193:"Nezha",
    194:"Queen of Sheba",
    195:"Abigail Williams",
    196:"Ereshkigal",
    197:"Attila The San(ta)",
    198:"Katsushika Hokusai",
    199:"Semiramis",
    2:"Altria",
    20:"C├║ Chulainn (Prototype)",
    200:"Asagami Fujino",
    201:"Anastasia",
    202:"Atalante Alter",
    203:"Avicebron",
    204:"Salieri",
    205:"Ivan the Terrible",
    206:"Achilles",
    207:"Chiron",
    208:"Sieg",
    209:"Majin Okita Souji",
    21:"Leonidas",
    210:"Okada Izo",
    211:"Sakamoto Ryouma",
    212:"Napoleon",
    213:"Sigurd",
    214:"Valkyrie",
    215:"Sc├íthach-Skadi",
    216:"Jeanne (Archer)",
    217:"Ibaraki-Douji (Lancer)",
    218:"Ushiwakamaru (Assassin)",
    219:"Jeanne Alter (Berserker)",
    22:"Romulus",
    220:"BB (Summer)",
    221:"Medb (Summer)",
    222:"Heroine XX",
    223:"Diarmuid (Saber)",
    224:"Sitonai",
    225:"Shuten-Douji (Caster)",
    226:"Xiang Yu",
    227:"Prince of Lan Ling",
    228:"Qin Liangyu",
    229:"Qin Shi Huang",
    23:"Medusa",
    230:"Yu Mei-ren",
    231:"Red Hare",
    232:"Bradamante",
    233:"Quetzalcoatl (Samba/Santa)",
    234:"Beni-Enma",
    235:"Li Shuwen (Assassin)",
    236:"Miyu",
    237:"Murasaki Shikibu",
    238:"Kingprotea",
    239:"Kama",
    24:"Georgios",
    # 240:"Kama/Mara", # ignore
    241:"Sima Yi",
    242:"Astraea",
    243:"Gray",
    244:"Ganesha",
    245:"Lakshmi Bai",
    246:"William Tell",
    247:"Arjuna (Alter)",
    248:"A┼¢vatth─üman",
    249:"Asclepius",
    25:"Teach",
    250:"Demon King Nobunaga",
    251:"Mori Nagayoshi",
    252:"Nagao Kagetora",
    253:"Da Vinci (Rider)",
    254:"Jason",
    255:"Paris",
    256:"Gareth",
    257:"Bartholomew",
    258:"Chen Gong",
    259:"Charlotte Corday",
    26:"Boudica",
    260:"Salome",
    261:"Miyamoto Musashi (Berserker)",
    262:"Osakabehime (Summer)",
    263:"Carmilla (Summer)",
    264:"Katsushika Hokusai (Saber)",
    265:"Altria (Ruler)",
    266:"Lambdaryllis",
    267:"Okita Souji (Assassin)",
    268:"S. Ishtar",
    269:"Calamity Jane",
    27:"Ushiwakamaru",
    270:"Astolfo (Saber)",
    271:"Florence Nightingale Santa",
    272:"Super Orion",
    273:"Mandricardo",
    274:"Europa",
    275:"Yang Guifei",
    276:"Sei Shounagon",
    277:"Odysseus",
    278:"Dioscuri",
    279:"Caenis",
    28:"Alexander",
    280:"Romulus=Quirinus",
    281:"Voyager",
    282:"Kijyo Koyo",
    283:"Utsumi Erice",
    284:"Altria (Castoria)",
    285:"Sessyoin Kiara (MoonCancer)",
    286:"Illya (Summer)",
    287:"Brynhild (Summer)",
    288:"Yu Mei-ren (Lancer)",
    289:"Abigail Williams (Summer)",
    29:"Marie Antoinette",
    290:"Tomoe Gozen (Summer)",
    291:"Murasaki Shikibu (Rider)",
    292:"Himiko",
    293:"Saito Hajime",
    294:"Oda Nobukatsu",
    295:"Gogh",
    296:"Nemo",
    297:"Ashiya Douman",
    298:"Watanabe-no-Tsuna",
    299:"Ibuki-Douji",
    3:"Saber Alter",
    30:"Martha",
    300:"Vritra",
    301:"Santa Karna",
    302:"Senji Muramasa",
    303:"Taira-no-Kagekiyo",
    304:"Kiichi Hogen",
    305:"Amor",
    306:"Galatea",
    307:"Miss Crane",
    308:"Idol X Alter",
    309:"Morgan",
    31:"Medea",
    310:"Barghest",
    311:"Baobhan Sith",
    312:"M├⌐lusine",
    313:"Percival",
    314:"Koyanskaya of Light",
    315:"Habetrot",
    316:"Oberon",
    317:"Majin Saber",
    318:"Anastasia & Viy",
    319:"Charlotte Corday (Caster)",
    32:"Gilles (Caster)",
    320:"Da Vinci (Summer)",
    321:"Kama (Avenger)",
    322:"Caenis (Summer)",
    323:"Sei Shounagon (Berskerer)",
    324:"Jacques de Molay",
    325:"Zenobia",
    326:"Elisabeth (Rider)",
    327:"Izumo-no-Okuni",
    328:"Ranmaru X",
    329:"Sakamoto Ryouma (Lancer)",
    33:"Andersen",
    330:"Martha Santa",
    331:"Taigong Wang",
    332:"Nikitich",
    # 333:"Beast IV", # ignore
    334:"Koyanskaya of Dark",
    335:"Hephaist├¡on",
    336:"Bazett",
    337:"Hai B├á Tr╞░ng",
    338:"Taisui Xingjun",
    339:"Super Bunyan",
    34:"Shakespeare",
    340:"Daikokuten",
    341:"Mary Anning",
    342:"K┼ìnstant├«nos XI",
    343:"Charlemagne",
    344:"Roland",
    345:"Kriemhild",
    346:"Moriarty (Ruler)",
    347:"Don Quixote",
    348:"Zhang Jue",
    349:"Kyokutei Bakin",
    35:"Mephistopheles",
    350:"Minamoto-no-Tametomo",
    352:"Xu Fu",
    353:"Lady Avalon",
    354:"Gareth (Summer)",
    355:"Ibuki-Douji (Summer)",
    356:"Utsumi Erice (Summer)",
    357:"Sc├íthach-Skadi (Ruler)",
    358:"Wu Zetian (Caster)",
    359:"Thr├║d",
    36:"Amadeus",
    360:"Hildr",
    361:"Ortlinde",
    362:"Sen-no-Rikyu",
    363:"Yamanami Keisuke",
    364:"Iyo",
    365:"Huyan Zhuo",
    366:"Huang Feihu",
    367:"Nine-Tattoo Dragon Elisa",
    368:"Britomart",
    369:"Kotomine Kirei",
    37:"Zhuge Liang",
    370:"Nitocris Alter",
    371:"Tezcatlipoca",
    372:"Tenochtitlan",
    373:"Kukulcan",
    374:"Johanna",
    375:"Takasugi Shinsaku",
    376:"Tiamat",
    377:"Draco",
    378:"Locusta",
    379:"Setanta",
    38:"C├║ Chulainn (Caster)",
    380:"Kashin Koji",
    381:"Bhima",
    382:"Duryodhana",
    383:"Durga",
    384:"Medusa (Saber)",
    385:"Aesc the Rain Witch",
    386:"Altria (Summer Castoria)",
    387:"Suzuka Gozen (Summer)",
    388:"Chloe (Summer)",
    389:"Cnoc na Riabh Yaraan-doo",
    39:"Kojirou",
    390:"M├⌐lusine (Summer)",
    391:"UDK-Barghest",
    392:"Cait C├║ Cerpriestess",
    393:"Wandjina",
    394:"Ptolema├«os",
    395:"Sugitani Zenjubou",
    396:"Theseus",
    397:"Takeda Harunobu",
    398:"Nagakura Shinpachi",
    399:"Saika Magoichi",
    4:"Saber Lily",
    40:"Cursed Arm",
    400:"Uesugi Kenshin",
    401:"Nemo Santa",
    402:"Yamato Takeru",
    403:"Ushi Gozen",
    404:"Yui Shousetsu",
    405:"Miyamoto Iori",
    406:"Andromeda",
    407:"Marie Antoinette Alter",
    408:"Hassan of the Shining Star",
    409:"The Count of Monte Cristo",
    41:"Stheno",
    410:"Count Cagliostro",
    # 411:"E-Flare Marie", # ignore
    # 412:"E-Aqua Marie", # ignore
    413:"Aozaki Aoko",
    4132:"Super Aoko", # Aoko transforms into Super Aoko with a new kit
    414:"Shizuki Soujuurou",
    415:"Kuonji Alice",
    416:"Hibiki & Chikagi",
    42:"Jing Ke",
    43:"Sanson",
    44:"Phantom",
    45:"Mata Hari",
    46:"Carmilla",
    47:"Heracles",
    48:"Lancelot",
    49:"Lu Bu",
    5:"Nero",
    50:"Spartacus",
    51:"Sakata Kintoki",
    52:"Vlad III",
    53:"Asterios",
    54:"Caligula",
    55:"Darius III",
    56:"Kiyohime",
    57:"Eric",
    58:"Tamamo Cat",
    59:"Jeanne",
    6:"Siegfried",
    60:"Orion",
    61:"Elisabeth",
    62:"Tamamo-no-Mae",
    63:"David",
    64:"Hektor",
    65:"Drake",
    66:"Mary",
    67:"Medea Lily",
    68:"Okita Souji",
    69:"Oda Nobunaga",
    7:"Caesar",
    70:"Sc├íthach",
    71:"Diarmuid",
    72:"Fergus",
    73:"Santa Alter",
    74:"Nursery Rhyme",
    75:"Jack",
    76:"Mordred",
    77:"Nikola Tesla",
    78:"Altria (Lancer Alter)",
    79:"Paracelsus",
    8:"Altera",
    80:"Babbage",
    81:"Jekyll",
    82:"Fran",
    # 83:"King Solomon", # ignore
    84:"Arjuna",
    85:"Karna",
    86:"Heroine X",
    87:"Fionn",
    88:"Brynhild",
    89:"Beowulf",
    9:"Gilles",
    90:"Nero Bride",
    91:"Ryougi Shiki",
    92:"Ryougi Shiki (Assassin)",
    93:"Amakusa Shirou",
    94:"Astolfo",
    95:"Gilgamesh (Child)",
    96:"Edmond Dant├¿s",
    97:"Florence Nightingale",
    98:"C├║ Chulainn Alter",
    99:"Medb"
})

skill_data = {'Function Types': {'addState': 1185, 'gainNp': 317, 'hastenNpturn': 473, 'addStateShort': 2304, 'lossHpSafe': 28, 'gainStar': 151, 'subState': 94, 'gainHp': 112, 'shortenSkill': 13, 'delayNpturn': 38, 'lossNp': 39, 'lossStar': 6, 'fixCommandcard': 1, 'gainNpBuffIndividualSum': 4, 'gainHpFromTargets': 3, 'cardReset': 2, 'gainNpFromTargets': 2, 'absorbNpturn': 2, 'moveState': 3, 'transformServant': 3, 'extendBuffturn': 2, 'gainMultiplyNp': 1, 'shortenBuffcount': 1, 'displayBuffstring': 1, 'gainNpIndividualSum': 1},
              'Function Target Types': {'ptAll': 637, 'ptOne': 394, 'self': 3255, 'enemy': 213, 'ptOther': 71, 'commandTypeSelfTreasureDevice': 7, 'enemyAll': 202, 'ptOneOther': 3, 'ptRandom': 2, 'ptFull': 2}, 
              'Buffs': {'DEF Up': 99, 'Invincible': 89, 'Target Focused': 80, 'NP Gain Up': 119, 'Damage Cut': 32, 'Buster Up': 167, 'Critical Strength Up': 247, 'Ignore Invincible': 34, 'Critical Hit Rate Up': 417, 'Ignore DEF': 5, 'Evade': 112, 'Debuff Resist Up': 33, 'Gain C. Stars Each Turn': 82, 'NP Strength Up': 103, 'Quick Up': 110, 'Arts Up': 142, 'C. Star Gather Up': 116, 'ATK Up': 261, 'Guts': 107, 'Sure Hit': 20, 'NP Gain Each Turn': 45, 'Overcharge Lv. Up': 17, 'Critical Star Drop Up': 79, 'Critical Hit Rate Down': 35, 'C. Star Drop Rate Down': 32, 'ATK Down': 23, 'Delayed Effect (Annihilation Wish)': 1, 'Delayed Effect (The End of the Fourth Night)': 1, 'Debuff Resist Down': 17, 'NP Type Change': 2, 'NP Type Change: Arts': 2, 'NP Type Change: Buster': 2, 'Healing Up': 2, 'Charm': 23, 'DEF Down': 65, 'Debuff Immune': 52, 'STR Up vs. Demonic': 10, 'STR Up vs. Heaven/Earth Servant': 1, 'ATK Debuff Resist Up': 8, 'Nullify Buff': 3, 'Buff Chance Up': 9, 'C. Star Gain Per Turn (Sunlight)': 1, 'Critical Hit Rate Up (Sunlight)': 1, 'Critical STR Up (Sunlight)': 1, 'Strength Up [Chaotic]': 5, 'STR Up vs. Evil': 3, 'Death Chance Up': 7, 'NP Seal': 19, 'Field Set [Sunlight]': 3, 'Debuff Chance Up': 7, 'Poison': 7, 'Corroding Poison': 2, 'Bonus Effect with Arts': 3, 'Max HP Plus': 16, 'Mental Resist Up': 14, 'Restore HP Each Turn': 32, 'Curse': 13, 'HP Recovery Up': 10, 'Stun After 1 Turn': 2, 'STR Up vs. Divine': 9, 'Burn': 5, 'Bonus Effect when Attacking': 8, 'STR Up vs. Divine, Undead, Demon': 1, 'Activate when Damaged': 8, 'Mana Burst Set': 1, 'Quick Card Resist Down': 3, 'Petrify': 3, 'C. Star Gather Up: Buster': 13, 'Critical Rate Up: Buster': 13, 'Field Set [Forest]': 2, 'Hit Count Up': 2, 'Strength Up': 2, 'Death Resist Down': 6, "Death's Abyss": 1, "Activate when Guts is Triggered (Remove Death's Abyss & NP Gauge Up & Buster Up)": 1, 'C. Star Gather Down': 8, 'Apply Trait (Evil)': 3, 'Strength Up [Human Attribute]': 2, 'Strength Up (Lawful)': 4, 'Poison Resist Up': 1, 'STR Up vs. Super Giant': 3, 'NP Gain Up When Damaged': 5, 'NP Strength Down': 12, 'NP Strength Up Set': 1, 'Pre-ATK Damage Bonus Effect (Critical STR Up)': 1, 'Bonus Effect (Debuff)': 4, 'Stun': 13, 'Bonus Effect with Extra Attack': 2, 'Arts Card Resist Down': 10, 'STR Up vs. [Greek Mythology Male]': 1, 'HP Recover Down': 2, 'Change DEF Affinity': 1, 'Burn (Self/Non-stackable)': 5, 'Burn Immune': 6, 'Build Up': 1, 'Skill Seal': 14, 'Damage Plus': 2, 'Strength Up (Curse)': 4, 'C. Star Gather Up: Arts': 10, 'Critical Hit Rate Up: Arts': 10, 'DEF Up [Demonic]': 1, 'Terror': 6, 'Immune to Death': 6, 'Buff Removal Resist Up': 22, 'Blessing of Kur': 1, 'Altera Timer': 1, 'Pseudonym "Iseidako"': 4, 'Class Affinity Change': 3, 'Buster Card Resist Down': 6, 'Command Card Type Change': 2, 'Strength Up (Wild Beasts)': 5, 'Minus Maximum HP': 2, 'Activate on Defeat (Tranquil Fig)': 1, 'STR Up vs. Dragon': 7, 'Strength Up (Heaven attribute)': 3, 'Activate when Guts is Triggered (ATK Up)': 1, 'STR Up vs. Humanoid': 2, 'Schwarzwald Falke': 1, 'Lock Command Cards': 1, 'Strength Up (Threat to Humanity)': 2, 'Strength Up (Earth Attribute)': 1, 'STR Up (Good)': 2, 'Infinite Growth': 2, 'NP Strength Up [Growth]': 1, 'Charm Resist Down (Mental)': 4, 'STR Up vs. Undead': 6, 'Marking': 1, 'Evade Trap': 1, 'Strength Up (Debuff)': 1, 'Bonus Effect with Buster (DEF Down)': 1, 'Bonus Effect with Quick (Critical Strength Up)': 1, 'Field Set [Burning]': 2, 'Buff Chance Down (Treated as Buff)': 1, 'Activate when Attacking (ATK Up & DEF Down)': 2, "Activate on Defeat (Oni Musashi's Last Will and Testament)": 2, 'Weakness Detected': 1, 'Activate when Damaged (ATK Up)': 1, 'STR Up vs. Roman': 3, 'Strength Up [Lawful and Good]': 1, 'Salacious Dance': 1, 'Dance of the Seven Veils': 2, 'Hit Count Up (Arts)': 1, 'Strength Up (Arts)': 1, 'DEF Down (Critical)': 1, 'Calling Card': 2, 'Activate during Critical Attack (Critical Strength Up)': 1, 'Royal Bunny Jump': 1, '': 7, 'Field Set [Near Water]': 4, 'DEF Down (Treated as Buff)': 2, 'Nullify Charm': 2, 'NP Type Change: Quick': 1, 'STR Up (Wild Beasts and Demonic)': 1, 'Pre-Buster ATK Damage Bonus Effect (Critical STR Up)': 1, 'Bonus Effect on Attack (Remove DEF Buff + Death)': 1, 'Target Focused [Male]': 2, 'Living Flame': 1, 'Bonus Effect with Quick Attack (NP Gain)': 1, 'Bonus Effect with Arts Attack (C. Star Gain)': 1, 'Bonus Effect with Arts ATK (Critical Hit Rate Up)': 1, 'Pre-ATK Damage Bonus Effect (ATK Up + ATK Down)': 2, 'Apply Trait (Rome)': 1, 'Bonus Effect with Critical ATK (Apply Rome Trait)': 1, 'Critical Resistance Up': 8, 'C. Star Generation Resistance Up': 8, 'Strength Up (Servant)': 2, "Mermaid's Nourishment": 1, 'Enchant': 2, 'C. Star Gather Rate Up: Quick': 1, 'Critical Hit Rate Up: Quick': 1, 'NP Gain Up: Near Water': 1, 'NP Gain Up: Sunlight': 1, 'Sleep': 2, 'DEF Down (Sleep)': 1, 'Mental Debuff Chance Up': 3, 'Staying Up Late': 1, 'Confusion': 4, 'Activate on Defeat (Adabana of War)': 1, 'Bonus Effect with Quick (Remove Curse)': 1, 'Activate when Guts is Triggered (NP Gain)': 1, 'Bonus Effect with Buster Attack': 4, 'Flame': 1, 'Strength Up (Genji)': 1, 'Death Resist Up': 1, 'Activate when Guts Is Triggered (Grudge of Vengeance)': 1, 'Triggers Each Turn (NP Absorb)': 1, 'Triggers Each Turn (Charge Absorb)': 1, 'Triggers Each Turn (HP Recovery & Remove Debuff)': 2, 'Additional Effect with Normal Buster Attack': 2, 'STR Up (Machine)': 1, 'Triggers Each Turn (ATK Down & Critical Hit Rate Down)': 1, 'Triggers Each Turn (ATK Down & C. Star Rate Down)': 1, 'Strong Eater': 1, 'Triggers Each Turn (Increase NP)': 1, 'STR Up vs. Human': 2, 'Delayed Effect (Death)': 1, 'Morning Lark': 2, 'Boost NP Strength Up': 1, 'Ending of Dreams': 1, 'Bonus Effect when Attacking (Apply Flames of Love)': 1, 'Strength Up (Flames of Love)': 1, 'Pre-ATK Damage Bonus Effect': 1, 'Activate during Critical Attack (DEF Down)': 1, 'Bonus Effect with Buster (C. Star Gain)': 1, 'Bonus Effect with Buster (Critical Hit Rate Up)': 1, 'Bonus Effect with ATK (Poison & Curse & Burn)': 1, 'Disastrous Curse': 1, 'Spreading Fire': 3, 'STR Up vs. Caster': 1, 'Activate on Defeat (Demise Privilege)': 1, 'Activate when Damaged (Buff)': 2, 'DEF Up vs. Divine': 1, 'Critical Strength Up [Evil]': 1, 'Bonus Effect with Critical ATK': 2, 'Activate when Guts IS Triggered (NP Strength Up & Remove Debuff)': 1, 'Triggers Each Turn (NP Strength Up)': 1, 'Charge Down': 2, 'Additional Effect with Normal Attack (Burn)': 1, 'Pre-Quick ATK Damage Bonus Effect': 7, 'Pre-Buster ATK Damage Bonus Effect': 1, 'Prince Wucheng Who Guards the Kingdom': 1, 'Mount Liang': 1, 'Guts <High Chance>': 1, 'Activate when Guts is Triggered': 4, 'Apply Trait (Good)': 1, 'Increase Buff Success Rate when receiving a Buff': 2, 'Decrease Buff Success Rate when receiving a Buff': 1, 'Nullify Invincibility': 1, 'Field Effect Cancellation [Sunlight]': 1, 'Recovery Disabled': 1, 'Holding Holy Grail': 1, '[Poison] Recovery': 1, 'Bonus Effect with Normal Attacks': 3, 'Sacrifice for the World Tree': 1, 'Additional Effect with Normal Quick Attack': 1, 'Bound': 4, 'Bonus Effect with Quick Attacks': 2, 'Triggers Each Turn': 4, 'Bonus Effect with Critical ATK Pre-Damage': 1, 'Preparing for a Revision': 1, 'My Fair Soldier': 1, 'Arts Seal': 1, 'Bonus Effect with Quick Attacks (Quick Resist Down)': 1, 'Weakling Protection': 1, 'Noble Phantasm Change': 1, 'Apply Trait [Super Giant]': 1, 'Throw/Retrieve': 2, 'Bloodstained Prince': 2, 'Strength Up [Earth Servant]': 1, 'Poison Immune': 1, 'Magic Bullet': 9, 'Protagonist Correction': 1, 'Extra Attack Up': 1, 'Lethal Damage Evade': 1, 'Delayed Effect (Quick Transformation)': 1, 'Delayed Effect (Arts Transformation)': 1, 'Delayed Effect (Buster Transformation)': 1, 'Substitution': 1, 'Pre-Quick Damage Bonus Effect': 1, 'Pre-Buster Damage Bonus Effect': 1, 'Strength Up [King]': 1, 'Bonus Effect with Quick Attack (DEF Down)': 1, 'Activate when Guts is Triggered (Buster Up)': 1, 'ATK Buff Chance Down': 2, 'STR Up (Burn)': 1, 'DEF Up vs. Dragon': 2, 'STR Up vs. Male': 1, 'Happy Halloween': 2, 'Pre-ATK Damage Bonus Effect (ATK Up)': 1, 'Delayed Effect (Fire Support)': 2, 'C. Star Drop Rate Up vs. Saber': 2, 'Critical Hit Rate Up vs. Saber': 2, 'STR Up vs. Saber': 2, 'Chance to Evade': 2, 'Strength Up [Giant]': 1, 'NP Gain Down': 2, 'DEF Up vs. Humanoid': 1}}
