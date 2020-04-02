from __future__ import annotations

from abc import ABC, abstractproperty
from typing import Any, Dict

from .alias import Field


class IndependentGraphQLField(ABC):
    @abstractproperty
    def field(self) -> Field:
        raise NotImplementedError()

    def resolver(self, obj, info, **user_kwarg) -> Dict[str, Any]:
        raise NotImplementedError()
