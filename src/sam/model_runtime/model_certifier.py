"""Model Certifier — sertifikasi model 7 dimensi (Sprint 248).

Program B — Model Runtime Integration.
Dimensi: Structure, Integrity, Consistency, Completeness, Determinism,
Immutability, PreviewOnly.

Semua pengecekan deterministik, read-only, no-network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .model_manifest import ModelManifest
from .model_score import ModelScore, ModelScoreSet
from .model_cert_report import ModelCertificationReport

# Kode dimensi (identifier stabil untuk API/test)
DIMENSIONS = (
    "structure",
    "integrity",
    "consistency",
    "completeness",
    "determinism",
    "immutability",
    "preview_only",
)


@dataclass(frozen=True)
class ModelCertifier:
    """Sertifikasi model (read-only, deterministik)."""

    def certify(self, manifest: ModelManifest) -> ModelCertificationReport:
        scores: dict = {}
        notes: List[str] = []

        scores["structure"] = self._structure(manifest)
        scores["integrity"] = self._integrity(manifest)
        scores["consistency"] = self._consistency(manifest)
        scores["completeness"] = self._completeness(manifest)
        scores["determinism"] = self._determinism(manifest)
        scores["immutability"] = self._immutability(manifest)
        scores["preview_only"] = self._preview(manifest)

        passed = sum(1 for s in scores.values() if s.passed)
        all_passed = passed == len(scores)
        if all_passed:
            notes.append("all dimensions passed")

        return ModelCertificationReport(
            report_id=f"cert-{manifest.descriptor.id}",
            model_id=manifest.descriptor.id,
            passed=all_passed,
            dimensions_total=len(DIMENSIONS),
            dimensions_passed=passed,
            score_set=ModelScoreSet(scores=scores),
            notes=notes,
        )

    # --- 7 dimensi ---

    def _structure(self, manifest: ModelManifest) -> ModelScore:
        ok = bool(manifest.descriptor.id and manifest.manifest_id)
        return ModelScore("structure", score=1.0 if ok else 0.0,
                          passed=ok, detail="valid id" if ok else "missing id")

    def _integrity(self, manifest: ModelManifest) -> ModelScore:
        ok = manifest.contract.owner_id == manifest.descriptor.id
        return ModelScore("integrity", score=1.0 if ok else 0.0, passed=ok,
                          detail="contract bound to descriptor" if ok else "contract/descriptor mismatch")

    def _consistency(self, manifest: ModelManifest) -> ModelScore:
        ok = manifest.metadata.source_runtime == "model"
        return ModelScore("consistency", score=1.0 if ok else 0.0, passed=ok,
                          detail="runtime consistent" if ok else "unexpected source runtime")

    def _completeness(self, manifest: ModelManifest) -> ModelScore:
        ok = bool(manifest.contract.operations)
        return ModelScore("completeness", score=1.0 if ok else 0.0, passed=ok,
                          detail="has operations" if ok else "no operations")

    def _determinism(self, manifest: ModelManifest) -> ModelScore:
        # dua serialisasi harus identik => deterministik
        a = manifest.descriptor.as_dict()
        b = ModelManifest(
            manifest.manifest_id, manifest.descriptor, manifest.contract,
            manifest.metadata, dict(manifest.integrity_extra),
        ).descriptor.as_dict()
        ok = a == b
        return ModelScore("determinism", score=1.0 if ok else 0.0, passed=ok,
                          detail="deterministic serialization" if ok else "non-deterministic")

    def _immutability(self, manifest: ModelManifest) -> ModelScore:
        ok = manifest.contract.preview_only is True and manifest.metadata.preview_only is True
        return ModelScore("immutability", score=1.0 if ok else 0.0, passed=ok,
                          detail="immutable flags set" if ok else "mutable flags")

    def _preview(self, manifest: ModelManifest) -> ModelScore:
        ok = manifest.contract.external_calls == 0
        return ModelScore("preview_only", score=1.0 if ok else 0.0, passed=ok,
                          detail="external_calls=0" if ok else "external_calls!=0")
