from __future__ import annotations

import csv
from pathlib import Path

from app.core.config import settings
from app.schemas.analysis import FingerprintSummary, MoleculeProfile


class MoleculeFeatureService:
    """读取示例分子文件并提供关键词检索。"""

    DESCRIPTOR_KEYS = [
        "MolWt",
        "MolLogP",
        "TPSA",
        "NumHDonors",
        "NumHAcceptors",
        "NumRotatableBonds",
        "RingCount",
        "LipinskiHBA",
        "LipinskiHBD",
    ]

    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        self.descriptor_path = (root / settings.molecule_descriptor_file).resolve()
        self.fingerprint_path = (root / settings.molecule_fingerprint_file).resolve()
        self._cached_profiles: list[MoleculeProfile] | None = None
        self.last_notes: list[str] = []

    def search(self, keyword: str, limit: int = 5) -> list[MoleculeProfile]:
        keyword = keyword.strip().lower()
        profiles = self._load_profiles()

        if not keyword:
            return profiles[:limit]

        hits = [
            profile
            for profile in profiles
            if keyword in profile.name.lower()
            or keyword in profile.smiles.lower()
            or keyword in profile.molecular_formula.lower()
        ]
        if hits:
            return hits[:limit]
        return profiles[:limit]

    def _load_profiles(self) -> list[MoleculeProfile]:
        if self._cached_profiles is not None:
            return self._cached_profiles

        notes: list[str] = []
        descriptor_rows = self._read_csv_rows(self.descriptor_path, notes)
        fingerprint_rows = self._read_csv_rows(self.fingerprint_path, notes)

        fp_by_name: dict[str, dict[str, str]] = {
            (row.get("Name") or "").strip(): row for row in fingerprint_rows
        }

        profiles: list[MoleculeProfile] = []
        for row in descriptor_rows:
            name = (row.get("Name") or "").strip()
            if not name:
                continue

            fp_row = fp_by_name.get(name, {})
            profiles.append(
                MoleculeProfile(
                    name=name,
                    smiles=(row.get("SMILES") or fp_row.get("SMILES") or "").strip(),
                    molecular_formula=(
                        row.get("MolecularFormula")
                        or fp_row.get("MolecularFormula")
                        or ""
                    ).strip(),
                    descriptors=self._select_descriptors(row),
                    fingerprint=self._build_fingerprint_summary(fp_row),
                )
            )

        self._cached_profiles = profiles
        self.last_notes = notes
        return profiles

    @staticmethod
    def _read_csv_rows(path: Path, notes: list[str]) -> list[dict[str, str]]:
        if not path.exists():
            notes.append(f"分子文件不存在: {path}")
            return []

        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]

    def _select_descriptors(self, row: dict[str, str]) -> dict[str, float | str]:
        result: dict[str, float | str] = {}
        for key in self.DESCRIPTOR_KEYS:
            value = (row.get(key) or "").strip()
            if not value:
                continue
            try:
                result[key] = round(float(value), 4)
            except ValueError:
                result[key] = value
        return result

    @staticmethod
    def _build_fingerprint_summary(row: dict[str, str]) -> FingerprintSummary:
        if not row:
            return FingerprintSummary()

        morgan_on_indices = [
            int(col.split("_", maxsplit=1)[1])
            for col, value in row.items()
            if col.startswith("Morgan_") and value == "1"
        ]
        maccs_on_indices = [
            int(col.split("_", maxsplit=1)[1])
            for col, value in row.items()
            if col.startswith("MACCS_") and value == "1"
        ]

        return FingerprintSummary(
            morgan_on_bits=len(morgan_on_indices),
            maccs_on_bits=len(maccs_on_indices),
            morgan_on_indices_preview=morgan_on_indices[:24],
            maccs_on_indices_preview=maccs_on_indices[:24],
        )
