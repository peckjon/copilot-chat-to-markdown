"""Tests for i18n translation system."""

import pytest
import os
import json
import tempfile
from unittest.mock import patch


class TestNormalizeLanguageCode:
    """Test language code normalization with BCP 47."""

    def test_exact_match_case_insensitive(self):
        """Should match exact language codes case-insensitively."""
        available = ['en-US', 'pt-BR']
        defaults = {'en': 'en-US', 'pt': 'pt-BR'}
        
        from chat_to_markdown import normalize_language_code
        
        assert normalize_language_code('en-US', available, defaults) == 'en-US'
        assert normalize_language_code('en-us', available, defaults) == 'en-US'
        assert normalize_language_code('EN-US', available, defaults) == 'en-US'

    def test_base_language_uses_default_region(self):
        """Should map base language to default region."""
        available = ['en-US', 'pt-BR', 'pt-PT']
        defaults = {'en': 'en-US', 'pt': 'pt-BR'}
        
        from chat_to_markdown import normalize_language_code
        
        assert normalize_language_code('en', available, defaults) == 'en-US'
        assert normalize_language_code('pt', available, defaults) == 'pt-BR'

    def test_fallback_to_any_region(self):
        """Should fallback to any available region for base language."""
        available = ['en-US', 'pt-PT']
        defaults = {'en': 'en-US', 'pt': 'pt-BR'}
        
        from chat_to_markdown import normalize_language_code
        
        # pt-BR not available, should find pt-PT
        assert normalize_language_code('pt-XX', available, defaults) == 'pt-PT'

    def test_final_fallback_to_en_us(self):
        """Should fallback to en-US when language not found."""
        available = ['en-US', 'pt-BR']
        defaults = {'en': 'en-US', 'pt': 'pt-BR'}
        
        from chat_to_markdown import normalize_language_code
        
        assert normalize_language_code('fr', available, defaults) == 'en-US'
        assert normalize_language_code('zh-CN', available, defaults) == 'en-US'

    def test_empty_language_returns_en_us(self):
        """Should return en-US for empty language code."""
        available = ['en-US']
        defaults = {}
        
        from chat_to_markdown import normalize_language_code
        
        assert normalize_language_code('', available, defaults) == 'en-US'
        assert normalize_language_code(None, available, defaults) == 'en-US'


class TestLoadTranslations:
    """Test translation file loading."""

    def test_load_existing_language(self, tmp_path):
        """Should load translations for existing language."""
        # Create temp translations file
        translations = {
            'en-US': {'test_key': 'Test Value'},
            'pt-BR': {'test_key': 'Valor de Teste'},
            '_defaults': {'en': 'en-US', 'pt': 'pt-BR'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            result = load_translations('pt-BR')
            assert result is True
            assert t('test_key') == 'Valor de Teste'

    def test_load_with_base_language_fallback(self, tmp_path):
        """Should use default region for base language."""
        translations = {
            'en-US': {'greeting': 'Hello'},
            'pt-BR': {'greeting': 'Olá'},
            '_defaults': {'en': 'en-US', 'pt': 'pt-BR'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            load_translations('pt')  # Should use pt-BR
            assert t('greeting') == 'Olá'

    def test_missing_translation_file_returns_false(self, tmp_path, capsys):
        """Should return False when translations.json not found."""
        from chat_to_markdown import load_translations
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            result = load_translations('en-US')
            assert result is False
            
            captured = capsys.readouterr()
            assert 'translations.json not found' in captured.err


class TestTranslationFunction:
    """Test the t() translation function."""

    def test_returns_translation_for_existing_key(self, tmp_path):
        """Should return translated text for existing key."""
        translations = {
            'en-US': {'key1': 'Value 1'},
            '_defaults': {'en': 'en-US'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            load_translations('en-US')
            assert t('key1') == 'Value 1'

    def test_returns_key_for_missing_translation(self, tmp_path):
        """Should return key itself when translation not found."""
        translations = {
            'en-US': {'existing_key': 'Value'},
            '_defaults': {'en': 'en-US'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            load_translations('en-US')
            assert t('missing_key') == 'missing_key'

    def test_format_with_parameters(self, tmp_path):
        """Should format translation with parameters."""
        translations = {
            'en-US': {
                'greeting': 'Hello {name}',
                'count': 'Found {count} items'
            },
            '_defaults': {'en': 'en-US'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            load_translations('en-US')
            assert t('greeting', name='World') == 'Hello World'
            assert t('count', count=5) == 'Found 5 items'

    def test_format_handles_missing_parameters_gracefully(self, tmp_path):
        """Should handle missing format parameters gracefully."""
        translations = {
            'en-US': {'template': 'Value: {value}'},
            '_defaults': {'en': 'en-US'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, t
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            load_translations('en-US')
            # Should return unformatted string if param missing
            result = t('template')
            assert 'Value:' in result


class TestGetCurrentLanguage:
    """Test getting current active language."""

    def test_returns_active_language(self, tmp_path):
        """Should return the currently active language code."""
        translations = {
            'pt-BR': {'key': 'valor'},
            '_defaults': {'pt': 'pt-BR'}
        }
        
        translations_file = tmp_path / 'translations.json'
        translations_file.write_text(json.dumps(translations))
        
        from chat_to_markdown import load_translations, get_current_language
        
        with patch('chat_to_markdown.__file__', str(tmp_path / 'fake.py')):
            load_translations('pt-BR')
            assert get_current_language() == 'pt-BR'
