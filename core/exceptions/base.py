from __future__ import annotations

class AIERPError(Exception):
    """Base exception for all errors raised by the AIERP platform."""
    pass

class ValidationError(AIERPError):
    """Raised when data fails domain validation rules."""
    pass

class SerializationError(AIERPError):
    """Raised when encoding or decoding objects fails."""
    pass
