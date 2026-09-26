"""Offline VIN and German type-code lookup, using the shared Orvin datasets.

Results are fresh JSON-compatible dictionaries. Unknown optional values are None;
status fields distinguish missing evidence, unsupported input and ambiguity.
"""
from .lookup import Context, HsnTsnLookup, VinDecoder
from .answer import VehicleAnswer

__all__ = ["Context", "HsnTsnLookup", "VinDecoder", "VehicleAnswer"]
