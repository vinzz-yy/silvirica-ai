from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union


@dataclass
class JsonRpcRequest:
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]]
    id: Optional[Union[str, int]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> JsonRpcRequest:
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method", ""),
            params=data.get("params"),
            id=data.get("id"),
        )


@dataclass
class JsonRpcResponse:
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            d["error"] = self.error
        else:
            d["result"] = self.result
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
