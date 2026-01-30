"""Tests for i18n translation system."""

import pytest
import json
from unittest.mock import patch


class TestLanguageNormalization:
    """Test BCP 47 language code normalization."""

    def test_language_normalization_scenarios(self):
        """Test all normalization scenarios in one comprehensive test."""
        available = ['en-US', 'pt-BR', 'pt-PT']
        defaults = {'en': 'en-US', 'pt': 'pt-BR'}
        
        from chat_to_markdown import normalize_language_code
        
        # Exact match (case-insensitive)
        assert normalize_language_code('en-US', available, defaults) == 'en-US'
        assert normalize_language_code('en-us', available, defaults) == 'en-US'
        
        # Base language to default region
        assert normalize_language_code('en', available, defaults) == 'en-US'
        assert normalize_language_code('pt', available, defaults) == 'pt-BR'
        
        # Fallback to any region when specific unavailable
        assert normalize_language_code('pt-XX', available, defaults) == 'pt-BR'
        
        # Final fallback to en-US
        assert normalize_language_code('fr', available, defaults) == 'en-US'
        assert normalize_language_code('', available, defaults) == 'en-US'
        assert normalize_language_code(None, available, defaults) == 'en-US'


class TestTranslationLoading:
    """Test translation file loading and error handling."""

    def test_successful_load_and_translation(self, tmp_path):
        """Should load translations and translate correctly."""
        translations = {
            'en-US': {'greeting': 'Hello', 'count': 'Found {count} items'},
            'pt-BR': {'greeting': 'Olá', 'count': 'Encontrou {count} itens'},
            '_defaults': {'en': 'en-US', 'pt': 'pt-BR'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t, get_current_language
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            # Load pt-BR
            assert load_translations('pt-BR') is True
            assert t('greeting') == 'Olá'
            assert t('count', count=5) == 'Encontrou 5 itens'
            assert get_current_language() == 'pt-BR'
            
            # Load with base language (pt -> pt-BR)
            load_translations('pt')
            assert get_current_language() == 'pt-BR'

    def test_missing_translation_file(self, tmp_path, capsys):
        """Should handle missing translation file gracefully."""
        from chat_to_markdown import load_translations
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            assert load_translations('en-US') is False
            assert 'translations.json not found' in capsys.readouterr().err


class TestTranslationFunction:
    """Test the t() translation function."""

    def test_translation_function_behavior(self, tmp_path):
        """Test translation with parameters and missing keys."""
        translations = {
            'en-US': {'exists': 'Value', 'with_param': 'Hello {name}'},
            '_defaults': {'en': 'en-US'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            load_translations('en-US')
            
            # Existing key
            assert t('exists') == 'Value'
            
            # Missing key returns key itself
            assert t('missing') == 'missing'
            
            # Parameter substitution
            assert t('with_param', name='World') == 'Hello World'
            
            # Missing parameter handled gracefully
            result = t('with_param')
            assert 'Hello' in result
