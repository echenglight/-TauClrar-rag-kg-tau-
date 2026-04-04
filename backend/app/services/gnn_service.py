from __future__ import annotations

from collections import defaultdict, deque

from app.schemas.analysis import GNNPrediction, GNNResult, MoleculeProfile
from app.schemas.graph import GraphEdge, GraphNode


class LightGNNService:
    """轻量级 GNN 风格打分：基于化合物节点的多跳传播。"""

    TARGET_TYPES = {"Protein", "Gene", "Pathway", "Disease"}

    def infer(
        self,
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        molecules: list[MoleculeProfile],
        keyword: str,
        top_k: int = 5,
    ) -> GNNResult:
        node_map = {node.id: node for node in nodes}
        adjacency = self._build_adjacency(edges)

        seed_ids = self._find_seed_nodes(nodes, molecules, keyword)
        if not seed_ids:
            return GNNResult(model_name="LightGNN-v1", top_k=top_k, predictions=[])

        distances = self._multi_source_bfs(adjacency, seed_ids, max_depth=3)
        degrees = {node_id: len(neighbors) for node_id, neighbors in adjacency.items()}
        max_degree = max(degrees.values()) if degrees else 1

        predictions: list[GNNPrediction] = []
        for node_id, depth in distances.items():
            node = node_map.get(node_id)
            if node is None or node.type not in self.TARGET_TYPES:
                continue

            proximity_score = max(0.0, 1.0 - (depth / 4.0))
            centrality_score = degrees.get(node_id, 0) / max_degree
            seed_support = self._seed_neighbor_support(node_id, adjacency, seed_ids)
            score = round(
                0.55 * proximity_score + 0.25 * centrality_score + 0.20 * seed_support,
                4,
            )

            predictions.append(
                GNNPrediction(
                    node_id=node_id,
                    node_name=node.name,
                    node_type=node.type,
                    score=score,
                    explanation=f"{depth} 跳邻域传播 + 度中心性 + 化合物邻接支持",
                )
            )

        predictions.sort(key=lambda item: item.score, reverse=True)
        return GNNResult(
            model_name="LightGNN-v1", top_k=top_k, predictions=predictions[:top_k]
        )

    @staticmethod
    def _build_adjacency(edges: list[GraphEdge]) -> dict[str, set[str]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in edges:
            adjacency[edge.source].add(edge.target)
            adjacency[edge.target].add(edge.source)
        return adjacency

    @staticmethod
    def _multi_source_bfs(
        adjacency: dict[str, set[str]],
        seed_ids: set[str],
        max_depth: int,
    ) -> dict[str, int]:
        visited: dict[str, int] = {}
        queue = deque([(seed, 0) for seed in seed_ids])

        while queue:
            current, depth = queue.popleft()
            if current in visited and depth >= visited[current]:
                continue
            visited[current] = depth

            if depth >= max_depth:
                continue
            for neighbor in adjacency.get(current, set()):
                queue.append((neighbor, depth + 1))

        return visited

    @staticmethod
    def _seed_neighbor_support(
        node_id: str, adjacency: dict[str, set[str]], seed_ids: set[str]
    ) -> float:
        neighbors = adjacency.get(node_id, set())
        if not neighbors:
            return 0.0
        hits = sum(1 for n in neighbors if n in seed_ids)
        return hits / len(neighbors)

    @staticmethod
    def _find_seed_nodes(
        nodes: list[GraphNode], molecules: list[MoleculeProfile], keyword: str
    ) -> set[str]:
        keyword = keyword.strip().lower()
        names = {molecule.name.lower() for molecule in molecules}
        names.update(
            {molecule.smiles.lower() for molecule in molecules if molecule.smiles}
        )
        if keyword:
            names.add(keyword)

        seeds: set[str] = set()
        for node in nodes:
            node_name = node.name.lower()
            node_type = node.type.lower()
            if node_type == "compound" and any(
                text and text in node_name for text in names
            ):
                seeds.add(node.id)

        if seeds:
            return seeds

        return {node.id for node in nodes if node.type.lower() == "compound"}
