#!/usr/bin/env python3
"""
Neo4j client for knowledge graph management.

Handles connection, entity/relationship creation, and queries.
"""

import logging
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from kg_builder.config.settings import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Client for interacting with Neo4j graph database."""

    def __init__(
        self, uri: str | None = None, username: str | None = None, password: str | None = None
    ):
        """Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (defaults to settings)
            username: Neo4j username (defaults to settings)
            password: Neo4j password (defaults to settings)
        """
        settings = get_settings()
        self.uri = uri or settings.neo4j_uri
        self.username = username or settings.neo4j_user
        self.password = password or settings.neo4j_password

        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Connected to Neo4j at {self.uri}")
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def create_constraints(self):
        """Create database constraints and indexes for performance."""
        constraints = [
            # Unique constraints
            "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
            # Indexes for faster queries
            "CREATE INDEX concept_type IF NOT EXISTS FOR (c:Concept) ON (c.type)",
            "CREATE INDEX paper_arxiv IF NOT EXISTS FOR (p:Paper) ON (p.arxiv_id)",
        ]

        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    logger.debug(f"Created: {constraint.split('IF NOT EXISTS')[0].strip()}")
                except Exception as e:
                    logger.warning(f"Constraint/index might already exist: {e}")

        logger.info("Database constraints and indexes created")

    def clear_database(self):
        """Clear all nodes and relationships. USE WITH CAUTION!"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        logger.warning("Database cleared!")

    def create_concept(
        self, name: str, concept_type: str, properties: dict[str, Any] | None = None
    ) -> dict:
        """Create or merge a Concept node.

        Args:
            name: Concept name
            concept_type: Type (method, material, phenomenon, theory, measurement, application)
            properties: Additional properties

        Returns:
            Created/merged node properties
        """
        props = properties or {}
        props["name"] = name
        props["type"] = concept_type

        query = """
        MERGE (c:Concept {name: $name})
        ON CREATE SET c.type = $type, c.created_at = datetime(), c += $props
        ON MATCH SET c += $props
        RETURN c
        """

        with self.driver.session() as session:
            result = session.run(query, name=name, type=concept_type, props=props)
            record = result.single()
            return dict(record["c"]) if record else {}

    def create_paper(self, paper_id: str, properties: dict[str, Any] | None = None) -> dict:
        """Create or merge a Paper node.

        Args:
            paper_id: Paper identifier (filename or arxiv_id)
            properties: Paper properties (title, arxiv_id, authors, etc.)

        Returns:
            Created/merged node properties
        """
        props = properties or {}
        props["id"] = paper_id

        query = """
        MERGE (p:Paper {id: $paper_id})
        ON CREATE SET p.created_at = datetime(), p += $props
        ON MATCH SET p += $props
        RETURN p
        """

        with self.driver.session() as session:
            result = session.run(query, paper_id=paper_id, props=props)
            record = result.single()
            return dict(record["p"]) if record else {}

    def create_author(self, name: str, properties: dict[str, Any] | None = None) -> dict:
        """Create or merge an Author node.

        Args:
            name: Author name
            properties: Additional properties

        Returns:
            Created/merged node properties
        """
        props = properties or {}
        props["name"] = name

        query = """
        MERGE (a:Author {name: $name})
        ON CREATE SET a.created_at = datetime(), a += $props
        ON MATCH SET a += $props
        RETURN a
        """

        with self.driver.session() as session:
            result = session.run(query, name=name, props=props)
            record = result.single()
            return dict(record["a"]) if record else {}

    def create_relationship(
        self,
        source_name: str,
        target_name: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> dict:
        """Create relationship between two Concept nodes.

        Args:
            source_name: Source concept name
            target_name: Target concept name
            rel_type: Relationship type (IS_A, USES, ENABLES, etc.)
            properties: Relationship properties (confidence, context, etc.)

        Returns:
            Created relationship properties
        """
        props = properties or {}

        # Normalize relationship type to uppercase with underscores
        rel_type = rel_type.upper().replace(" ", "_").replace("-", "_")

        query = f"""
        MATCH (s:Concept {{name: $source}})
        MATCH (t:Concept {{name: $target}})
        MERGE (s)-[r:{rel_type}]->(t)
        ON CREATE SET r += $props, r.created_at = datetime()
        ON MATCH SET r += $props
        RETURN r
        """

        with self.driver.session() as session:
            result = session.run(query, source=source_name, target=target_name, props=props)
            record = result.single()
            return dict(record["r"]) if record else {}

    def link_paper_to_concept(
        self, paper_id: str, concept_name: str, properties: dict[str, Any] | None = None
    ):
        """Create MENTIONS relationship from Paper to Concept.

        Args:
            paper_id: Paper identifier
            concept_name: Concept name
            properties: Relationship properties (frequency, sections, etc.)
        """
        props = properties or {}

        query = """
        MATCH (p:Paper {id: $paper_id})
        MATCH (c:Concept {name: $concept_name})
        MERGE (p)-[r:MENTIONS]->(c)
        ON CREATE SET r += $props, r.created_at = datetime()
        ON MATCH SET r += $props
        RETURN r
        """

        with self.driver.session() as session:
            session.run(query, paper_id=paper_id, concept_name=concept_name, props=props)

    def link_paper_to_author(self, paper_id: str, author_name: str):
        """Create AUTHORED_BY relationship from Paper to Author.

        Args:
            paper_id: Paper identifier
            author_name: Author name
        """
        query = """
        MATCH (p:Paper {id: $paper_id})
        MATCH (a:Author {name: $author_name})
        MERGE (p)-[r:AUTHORED_BY]->(a)
        ON CREATE SET r.created_at = datetime()
        RETURN r
        """

        with self.driver.session() as session:
            session.run(query, paper_id=paper_id, author_name=author_name)

    def get_concept(self, name: str) -> dict | None:
        """Get a concept by name.

        Args:
            name: Concept name

        Returns:
            Concept properties or None
        """
        query = "MATCH (c:Concept {name: $name}) RETURN c"

        with self.driver.session() as session:
            result = session.run(query, name=name)
            record = result.single()
            return dict(record["c"]) if record else None

    def get_paper(self, paper_id: str) -> dict | None:
        """Get a paper by ID.

        Args:
            paper_id: Paper identifier

        Returns:
            Paper properties or None
        """
        query = "MATCH (p:Paper {id: $paper_id}) RETURN p"

        with self.driver.session() as session:
            result = session.run(query, paper_id=paper_id)
            record = result.single()
            return dict(record["p"]) if record else None

    def get_concept_relationships(self, concept_name: str) -> list[dict]:
        """Get all relationships for a concept.

        Args:
            concept_name: Concept name

        Returns:
            List of relationships with source, target, and type
        """
        query = """
        MATCH (c:Concept {name: $name})-[r]-(other:Concept)
        RETURN c.name as source, type(r) as relationship, other.name as target, properties(r) as props
        """

        with self.driver.session() as session:
            result = session.run(query, name=concept_name)
            return [
                {
                    "source": record["source"],
                    "relationship": record["relationship"],
                    "target": record["target"],
                    "properties": dict(record["props"]),
                }
                for record in result
            ]

    def get_paper_concepts(self, paper_id: str) -> list[dict]:
        """Get all concepts mentioned in a paper.

        Args:
            paper_id: Paper identifier

        Returns:
            List of concepts with mention properties
        """
        query = """
        MATCH (p:Paper {id: $paper_id})-[r:MENTIONS]->(c:Concept)
        RETURN c.name as concept, c.type as type, properties(r) as mention_props
        ORDER BY c.name
        """

        with self.driver.session() as session:
            result = session.run(query, paper_id=paper_id)
            return [
                {
                    "concept": record["concept"],
                    "type": record["type"],
                    "mention_props": dict(record["mention_props"]),
                }
                for record in result
            ]

    def get_statistics(self) -> dict[str, int]:
        """Get database statistics.

        Returns:
            Dictionary with counts of nodes and relationships
        """
        queries = {
            "concepts": "MATCH (c:Concept) RETURN count(c) as count",
            "papers": "MATCH (p:Paper) RETURN count(p) as count",
            "authors": "MATCH (a:Author) RETURN count(a) as count",
            "relationships": "MATCH ()-[r:IS_A|PART_OF|USES|ENABLES|MEASURES|APPLIES_TO|BASED_ON|RELATED_TO]->() RETURN count(r) as count",
            "mentions": "MATCH ()-[r:MENTIONS]->() RETURN count(r) as count",
        }

        stats = {}
        with self.driver.session() as session:
            for key, query in queries.items():
                result = session.run(query)
                record = result.single()
                stats[key] = record["count"] if record else 0

        return stats

    def search_concepts(self, search_term: str, limit: int = 20) -> list[dict]:
        """Search for concepts by name (case-insensitive partial match).

        Args:
            search_term: Search string
            limit: Maximum results

        Returns:
            List of matching concepts
        """
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($search)
        RETURN c.name as name, c.type as type, properties(c) as props
        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(query, search=search_term, limit=limit)
            return [
                {
                    "name": record["name"],
                    "type": record["type"],
                    "properties": dict(record["props"]),
                }
                for record in result
            ]

    def run_cypher(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict]:
        """Run a custom Cypher query.

        Args:
            query: Cypher query
            parameters: Query parameters

        Returns:
            Query results as list of dictionaries
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
