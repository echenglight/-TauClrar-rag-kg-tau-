"""将 literature_graph.json 导入 Neo4j（优化版）。

用法：
    python build_graph.py --data data/literature_graph.json --wipe
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from neo4j import GraphDatabase


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def upsert_nodes(tx, nodes: list[dict]) -> None:
    query = """
    UNWIND $nodes AS n
    MERGE (x:Entity {id: n.id})
    SET x.name = n.name,
        x.type = n.type,
        x.size = n.size,
        x += n.properties
    FOREACH (_ IN CASE WHEN n.type = 'Gene' THEN [1] ELSE [] END | SET x:Gene)
    FOREACH (_ IN CASE WHEN n.type = 'Compound' THEN [1] ELSE [] END | SET x:Compound)
    FOREACH (_ IN CASE WHEN n.type = 'Pathway' THEN [1] ELSE [] END | SET x:Pathway)
    FOREACH (_ IN CASE WHEN n.type = 'Disease' THEN [1] ELSE [] END | SET x:Disease)
    FOREACH (_ IN CASE WHEN n.type = 'Protein' THEN [1] ELSE [] END | SET x:Protein)
    RETURN count(x) AS c
    """
    tx.run(query, nodes=nodes)


def upsert_edges(tx, edges: list[dict]) -> None:
    query = """
    UNWIND $edges AS e
    MATCH (s:Entity {id: e.source})
    MATCH (t:Entity {id: e.target})
    MERGE (s)-[r:RELATED_TO {id: e.id}]->(t)
    SET r.rel_type = e.type,
        r.weight = e.weight,
        r.evidence = e.evidence,
        r.source_ids = e.source_ids,
        r.evidence_status = e.evidence_status,
        r.context = e.context,
        r.label = e.label
    RETURN count(r) AS c
    """
    tx.run(query, edges=edges)


def create_indexes(tx) -> None:
    tx.run("CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")
    tx.run("CREATE INDEX entity_name_idx IF NOT EXISTS FOR (n:Entity) ON (n.name)")


def clear_graph(tx) -> None:
    tx.run("MATCH (n) DETACH DELETE n")


def main() -> None:
    parser = argparse.ArgumentParser(description="文献图谱导入 Neo4j")
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", default="change_me")
    parser.add_argument("--data", default="data/literature_graph.json")
    parser.add_argument("--wipe", action="store_true", help="导入前清空图数据库")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    data_file = (base / args.data).resolve()

    payload = load_json(data_file)
    nodes = payload.get("nodes", [])
    edges = payload.get("edges", [])

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))

    with driver.session() as session:
        if args.wipe:
            session.execute_write(clear_graph)
        session.execute_write(create_indexes)
        session.execute_write(upsert_nodes, nodes)
        session.execute_write(upsert_edges, edges)

    driver.close()

    print("导入完成")
    print(f"节点数：{len(nodes)}")
    print(f"关系数：{len(edges)}")


if __name__ == "__main__":
    main()
