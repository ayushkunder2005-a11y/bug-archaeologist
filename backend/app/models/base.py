"""Base class for MongoDB document models."""

import uuid
from datetime import datetime, timezone
from typing import Any


class MongoBaseModel:
    """Base model wrapper for MongoDB documents with attribute access."""

    def __init__(self, **data: Any):
        if "id" not in data or not data["id"]:
            data["id"] = str(data.get("_id")) if data.get("_id") else str(uuid.uuid4())
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self._data[name] = value

    def __getitem__(self, item: str) -> Any:
        return self._data[item]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, item: str) -> bool:
        return item in self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        d = dict(self._data)
        d["_id"] = d.get("id")
        return d

    @classmethod
    def from_mongo(cls, doc: dict[str, Any] | None) -> Any:
        if not doc:
            return None
        doc_copy = dict(doc)
        if "_id" in doc_copy and ("id" not in doc_copy or not doc_copy["id"]):
            doc_copy["id"] = str(doc_copy["_id"])
        return cls(**doc_copy)
