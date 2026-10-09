from dataclasses import dataclass
from typing import Literal
import json
from pydantic import BaseModel
from rdflib import Literal as RDFLiteral
import numpy as np


# from https://stackoverflow.com/a/1733105
class PrettyFloat(float):
    def __repr__(self):
        return "%.15g" % self


def pretty_floats(obj):
    if isinstance(obj, float):
        return PrettyFloat(obj)
    elif isinstance(obj, dict):
        return dict((k, pretty_floats(v)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        return list(map(pretty_floats, obj))
    return obj


class DataTensorResp(BaseModel):
    data: list[float]
    type: Literal["float32", "float64", "int32", "int64"]
    shape: tuple[int, ...]


@dataclass
class DataTensor:
    data: list[float]
    type: Literal["float32", "float64", "int32", "int64"]
    shape: tuple[int, ...]

    @staticmethod
    def from_numpy(array: np.ndarray) -> "DataTensor":
        return DataTensor(
            data=array.flatten().tolist(),
            type=str(array.dtype),
            shape=array.shape,
        )

    def to_numpy(self) -> np.ndarray:
        return np.array(self.data, dtype=np.float32).reshape(self.shape)

    @staticmethod
    def from_literal(lit: RDFLiteral) -> "DataTensor":
        json_str = str(lit)
        data = json.loads(json_str)
        # lowercase all keys to be safe
        data = {k.lower(): v for k, v in data.items()}

        return DataTensor(
            data=data["data"],
            type=data["type"],
            shape=tuple(data["shape"]),
        )

    def to_resp(self) -> DataTensorResp:
        return DataTensorResp(
            data=self.data,
            type=self.type,
            shape=self.shape,
        )

    def to_literal(self) -> RDFLiteral:
        json_str = json.dumps(
            pretty_floats(
                {
                    "data": self.data,
                    "type": self.type,
                    "shape": self.shape,
                }
            )
        )
        return RDFLiteral(
            json_str, datatype="https://w3id.org/rdf-tensor/datatypes#NumericDataTensor"
        )
