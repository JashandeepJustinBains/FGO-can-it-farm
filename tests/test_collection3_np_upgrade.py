import os
import pytest

from Driver import Driver
from units.Servant import select_character


def test_collection3_upgraded_np_behavior():
    """Integration test for collection 3 NP upgrade behavior.

    Tests that Mana Burst (Wrath)-style on-hit triggers work correctly
    by providing NP grants per hit rather than only once.
    """

    # Fetch servant JSON (DB or fixture)
    servant_json = select_character(3)
    assert servant_json is not None, "Servant 3 not found in DB or fixture"

    # Build servant init dicts: first servant is collectionNo 3 with upgrades
    servants = [
        {
            'collectionNo': 3,
            'np': 5,
            'initialCharge': 100,
            'append_5': True,
            'damageUp': 150,
        },
        {'collectionNo': 314},
        {'collectionNo': 314},
        {'collectionNo': 316},
    ]

    mc_id = 210
    quest_id = 94100501
    # Tokenize the command sequence (split spaces). '#' tokens mark end of wave.
    command_str = "a c f1 i1 4 # d1 g1 x31 4 # b g h1 i1 j 4 #"
    tokens = [t for t in command_str.split() if t]

    # Build Driver and run tokens step-by-step so we can assert after each wave
    driver = Driver(servants, quest_id, mc_id)
    driver.reset_state()

    gm = driver.game_manager
    s3 = next((s for s in gm.servants if s.id == 3), None)
    assert s3 is not None, "Servant 3 not present in initialized team"

    wave_count = 0
    for token in tokens:
        driver.execute_token(token)
        if token == '#':
            wave_count += 1
            # After wave 1
            if wave_count == 1:
                gauge = s3.get_npgauge()
                assert abs(gauge - 30) <= 3, f"After wave1 expected ~30, got {gauge}"
            # After wave 2
            if wave_count == 2:
                gauge = s3.get_npgauge()
                assert abs(gauge - 20) <= 3, f"After wave2 expected ~20, got {gauge}"

