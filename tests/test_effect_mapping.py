"""
Test module for effect mapping functionality.

Tests the data-driven effect parsing using discovery artifact samples
without requiring external dependencies like MongoDB.
"""

import json
import os
import pytest
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import effect_mapping


class TestEffectMapping:
    """Test effect mapping normalization and handlers."""
    
    @pytest.fixture
    def addStateShort_samples(self):
        """Load addStateShort test fixtures."""
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'addStateShort_samples.json')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture  
    def servantFriendshipUp_samples(self):
        """Load servantFriendshipUp test fixtures."""
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'servantFriendshipUp_samples.json')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def addState_samples(self):
        """Load addState test fixtures.""" 
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'addState_samples.json')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_effect_mapping_normalizes(self, addStateShort_samples, servantFriendshipUp_samples, addState_samples):
        """Verify that mapping returns a dict with expected keys and types."""
        
        # Test addStateShort
        for sample in addStateShort_samples:
            result = effect_mapping.get_effect_for_func(sample, 'np')
            
            # Check required keys are present
            assert 'source' in result
            assert 'funcType' in result
            assert 'targetType' in result
            assert 'parameters' in result
            assert 'svals' in result
            assert 'buffs' in result
            assert 'raw' in result
            
            # Check types
            assert isinstance(result['source'], str)
            assert isinstance(result['funcType'], str)
            assert isinstance(result['targetType'], str)
            assert isinstance(result['parameters'], dict)
            assert isinstance(result['svals'], dict)
            assert isinstance(result['buffs'], list)
            assert isinstance(result['raw'], dict)
            
            # Check specific values for addStateShort
            assert result['source'] == 'np'
            assert result['funcType'] == 'addStateShort'
            
            # Check svals structure
            assert 'base' in result['svals']
            assert 'oc' in result['svals']
            assert isinstance(result['svals']['base'], list)
            assert isinstance(result['svals']['oc'], dict)
            
        # Test servantFriendshipUp
        for sample in servantFriendshipUp_samples:
            result = effect_mapping.get_effect_for_func(sample, 'skill')
            
            assert result['source'] == 'skill'
            assert result['funcType'] == 'servantFriendshipUp'
            
            # Check event-specific parameters
            if result['parameters']:
                assert 'eventId' in result['parameters'] or 'rateCount' in result['parameters']
        
        # Test addState
        for sample in addState_samples:
            result = effect_mapping.get_effect_for_func(sample, 'np')
            
            assert result['source'] == 'np'
            assert result['funcType'] == 'addState'
            
            # addState should have buffs
            assert len(result['buffs']) > 0
    
    def test_svals_normalization(self, addStateShort_samples):
        """Test that svals are properly normalized into base + OC structure."""
        mapper = effect_mapping.EffectMapping()
        
        for sample in addStateShort_samples:
            svals_normalized = mapper._normalize_svals(sample)
            
            # Check structure
            assert 'base' in svals_normalized
            assert 'oc' in svals_normalized
            
            # Check base svals
            if 'svals' in sample:
                assert svals_normalized['base'] == sample['svals']
            
            # Check OC variations if present
            for oc_level in range(2, 6):
                oc_key = f'svals{oc_level}'
                if oc_key in sample:
                    assert oc_level in svals_normalized['oc']
                    assert svals_normalized['oc'][oc_level] == sample[oc_key]
    
    def test_parameter_extraction(self, addStateShort_samples):
        """Test parameter extraction from svals."""
        mapper = effect_mapping.EffectMapping()
        
        for sample in addStateShort_samples:
            svals_normalized = mapper._normalize_svals(sample)
            parameters = mapper._extract_parameters_from_svals(svals_normalized)
            
            # Should extract common parameters
            assert isinstance(parameters, dict)
            
            # Check that we extract meaningful parameters from last sval
            if svals_normalized['base']:
                last_sval = svals_normalized['base'][-1]
                if isinstance(last_sval, dict):
                    if 'Value' in last_sval:
                        assert 'value' in parameters
                        assert parameters['value'] == last_sval['Value']
                    if 'Turn' in last_sval:
                        assert 'turn' in parameters
                        assert parameters['turn'] == last_sval['Turn']
    
    def test_buff_normalization(self, addStateShort_samples):
        """Test buff structure normalization."""
        mapper = effect_mapping.EffectMapping()
        
        for sample in addStateShort_samples:
            if 'buffs' in sample and sample['buffs']:
                for buff in sample['buffs']:
                    normalized_buff = mapper._normalize_buff(buff)
                    
                    # Check required keys
                    assert 'id' in normalized_buff
                    assert 'name' in normalized_buff
                    assert 'type' in normalized_buff
                    assert 'detail' in normalized_buff
                    assert 'icon' in normalized_buff
                    assert 'maxRate' in normalized_buff
                    assert 'vals' in normalized_buff
                    assert 'tvals' in normalized_buff
                    assert 'script' in normalized_buff
                    
                    # Check types
                    assert isinstance(normalized_buff['id'], int)
                    assert isinstance(normalized_buff['name'], str)
                    assert isinstance(normalized_buff['type'], str)
                    assert isinstance(normalized_buff['vals'], list)
                    assert isinstance(normalized_buff['tvals'], list)
                    assert isinstance(normalized_buff['script'], dict)
    
    def test_generic_handler_fallback(self):
        """Test that generic handler works for unmapped funcTypes."""
        # Create a fictional funcType that's not implemented
        fake_func = {
            'funcType': 'fakeFuncType',
            'funcTargetType': 'self',
            'svals': [{'Value': 100, 'Turn': 1}],
            'buffs': []
        }
        
        result = effect_mapping.get_effect_for_func(fake_func, 'np')
        
        # Should still return normalized structure
        assert result['funcType'] == 'fakeFuncType'
        assert result['source'] == 'np'
        assert 'parameters' in result
        assert 'svals' in result
        assert 'buffs' in result
        assert 'raw' in result


class TestNPParserIntegration:
    """Test NP parser integration with effect mapping."""
    
    @pytest.fixture
    def sample_np_fixture(self):
        """Load sample NP test fixture."""
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_np.json')
        with open(fixture_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_np_parser_integration(self, sample_np_fixture):
        """Load a sample NP, run the refactored parser, assert normalized effects and legacy."""
        # Import NP class directly to avoid dependency issues
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'np_module', 
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'units', 'np.py')
        )
        np_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(np_module)
        
        # Create NP with sample data
        np_obj = np_module.NP([sample_np_fixture])
        
        # Test getting values
        results = np_obj.get_np_values(np_level=1, overcharge_level=1)
        
        # Should have at least one normalized effect
        assert len(results) > 0
        
        for effect in results:
            # Check normalized effect structure
            assert 'source' in effect
            assert 'funcType' in effect
            assert 'targetType' in effect
            assert 'parameters' in effect
            assert 'svals' in effect
            assert 'buffs' in effect
            assert 'raw' in effect
            
            # Check that source is correctly set to 'np'
            assert effect['source'] == 'np'
            
            # Check that legacy exists for backwards compatibility
            assert '_legacy' in effect
            legacy = effect['_legacy']
            
            # Check legacy structure
            assert 'funcType' in legacy
            assert 'funcTargetType' in legacy
            assert 'functvals' in legacy
            assert 'svals' in legacy
            assert 'buffs' in legacy
            
            # Verify that legacy funcType matches normalized funcType
            assert legacy['funcType'] == effect['funcType']
    
    def test_np_parser_handles_multiple_functions(self, sample_np_fixture):
        """Test that NP parser correctly handles multiple functions in an NP."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'np_module', 
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'units', 'np.py')
        )
        np_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(np_module)
        
        # Create NP with sample data
        np_obj = np_module.NP([sample_np_fixture])
        
        # Get expected number of functions
        expected_count = len(sample_np_fixture['functions'])
        
        # Test getting values
        results = np_obj.get_np_values(np_level=1, overcharge_level=1)
        
        # Should have same number of effects as functions
        assert len(results) == expected_count
        
        # All should have proper structure
        for effect in results:
            assert effect['source'] == 'np'
            assert effect['variant_id'] == sample_np_fixture['id']
            assert '_legacy' in effect