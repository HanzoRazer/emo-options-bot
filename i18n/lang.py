"""
Language support for EMO Options Bot
JSON-based translation system with file-based translations.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any

_ROOT = Path(__file__).resolve().parents[1]
_LOCALE_DIR = _ROOT / "i18n" / "translations"

_CACHE: Dict[str, Dict[str, str]] = {}

def _load(lang: str) -> Dict[str, str]:
    """Load translations from JSON files with caching."""
    lang = (lang or "en").lower()
    if lang in _CACHE:
        return _CACHE[lang]
    
    # Ensure translations directory exists
    _LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    
    path = _LOCALE_DIR / f"{lang}.json"
    if not path.exists():
        path = _LOCALE_DIR / "en.json"
    
    try:
        if path.exists():
            _CACHE[lang] = json.loads(path.read_text(encoding="utf-8"))
        else:
            # Fallback to built-in translations if files don't exist
            _CACHE[lang] = _get_builtin_translations(lang)
    except Exception:
        _CACHE[lang] = _get_builtin_translations("en")
    
    return _CACHE[lang]

def _get_builtin_translations(lang: str) -> Dict[str, str]:
    """Fallback built-in translations."""
    builtin = {
        "en": {
            "staging_disabled": "📋 Order staging is disabled (set EMO_STAGE_ORDERS=1 to enable)",
            "draft_written": "📝 Order draft written to: {path}",
            "yaml_missing": "⚠️  PyYAML not available, falling back to JSON format",
            "order_staged": "✅ Order staged successfully",
            "invalid_side": "❌ Invalid order side: {side}. Must be 'buy' or 'sell'",
            "invalid_order_type": "❌ Invalid order type: {order_type}. Must be 'market' or 'limit'",
            "missing_limit_price": "❌ Limit price required for limit orders",
            "invalid_quantity": "❌ Invalid quantity: {qty}. Must be positive number",
            "invalid_symbol": "❌ Invalid symbol: {symbol}. Symbol cannot be empty",
            "staging_error": "❌ Error staging order: {error}",
        },
        "es": {
            "staging_disabled": "📋 La preparación de órdenes está deshabilitada (establezca EMO_STAGE_ORDERS=1 para habilitar)",
            "draft_written": "📝 Borrador de orden escrito en: {path}",
            "yaml_missing": "⚠️  PyYAML no disponible, usando formato JSON",
            "order_staged": "✅ Orden preparada exitosamente",
            "invalid_side": "❌ Lado de orden inválido: {side}. Debe ser 'buy' o 'sell'",
            "invalid_order_type": "❌ Tipo de orden inválido: {order_type}. Debe ser 'market' o 'limit'",
            "missing_limit_price": "❌ Precio límite requerido para órdenes límite",
            "invalid_quantity": "❌ Cantidad inválida: {qty}. Debe ser un número positivo",
            "invalid_symbol": "❌ Símbolo inválido: {symbol}. El símbolo no puede estar vacío",
            "staging_error": "❌ Error al preparar orden: {error}",
        }
    }
    return builtin.get(lang, builtin["en"])

def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """
    Translate a message key to the specified language.
    
    Args:
        key: Translation key
        lang: Language code (en, es, fr, etc.)
        **kwargs: Format parameters for the message
        
    Returns:
        Translated and formatted message
    """
    translations = _load(lang)
    message = translations.get(key, f"[MISSING: {key}]")
    
    # Format with provided kwargs
    try:
        return message.format(**kwargs)
    except (KeyError, ValueError):
        # If formatting fails, return the raw message
        return message

def get_supported_languages() -> list[str]:
    """Get list of supported language codes from files and built-in."""
    languages = set(["en", "es"])  # Always include built-in languages
    
    # Add languages from translation files
    if _LOCALE_DIR.exists():
        for file in _LOCALE_DIR.glob("*.json"):
            languages.add(file.stem)
    
    return sorted(list(languages))

def add_translation(lang: str, translations: Dict[str, str]) -> None:
    """
    Add or update translations for a language.
    
    Args:
        lang: Language code
        translations: Dictionary of key-value translation pairs
    """
    lang = lang.lower().strip()
    
    # Update cache
    if lang not in _CACHE:
        _CACHE[lang] = {}
    _CACHE[lang].update(translations)
    
    # Write to file
    _LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = _LOCALE_DIR / f"{lang}.json"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(_CACHE[lang], f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not write translation file {file_path}: {e}")

def reload_translations() -> None:
    """Clear cache and reload all translations."""
    global _CACHE
    _CACHE = {}

def export_translations() -> Dict[str, Dict[str, str]]:
    """Export all loaded translations."""
    result = {}
    for lang in get_supported_languages():
        result[lang] = _load(lang)
    return result