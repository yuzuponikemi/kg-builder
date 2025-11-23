"""
KG Builder - Knowledge Graph Builder for Research Papers

A comprehensive system for extracting, constructing, visualizing, and analyzing
knowledge graphs from research papers using Neo4j and LLMs.
"""

__version__ = "0.1.0"
__author__ = "KG Builder Team"

from kg_builder.sdk.client import KGClient

__all__ = ["KGClient"]
