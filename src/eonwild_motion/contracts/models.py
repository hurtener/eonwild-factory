from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ContractDocument:
    kind: str
    path: str
    sha256: str
    data: dict[str, Any]


@dataclass(frozen=True)
class ResolvedProfile:
    repository: Path
    profile_path: Path
    profile: dict[str, Any]
    profile_sha256: str
    documents: dict[str, ContractDocument]
    layers: tuple[ContractDocument, ...]
    input_path: Path
    input_sha256: str
    approved_output_path: Path
    approved_output_sha256: str
    source_release_root: Path
    source_manifest_path: Path
    source_manifest_sha256: str
    contact_evidence_path: Path
    contact_evidence_sha256: str
    lock: dict[str, Any]
    lock_sha256: str
    selector: str
    channel: dict[str, Any] | None = None

    @property
    def rig(self) -> dict[str, Any]:
        return self.documents["rig"].data

    @property
    def family(self) -> dict[str, Any]:
        return self.documents["family"].data

    @property
    def species(self) -> dict[str, Any]:
        return self.documents["species"].data

    @property
    def motion(self) -> dict[str, Any]:
        return self.documents["motion"].data

    @property
    def render_set(self) -> dict[str, Any]:
        return self.documents["renderSet"].data

    def profile_binding(self) -> dict[str, Any]:
        channel = self.channel or {}
        return {
            "id": self.profile["id"],
            "sha256": self.profile_sha256,
            "lockSha256": self.lock_sha256,
            "channel": channel.get("name"),
            "channelStateSha256": channel.get("stateSha256"),
            "generation": channel.get("generation"),
            "iteration": channel.get("iteration"),
            "revision": channel.get("revision"),
            "historyId": channel.get("historyId"),
        }

    def runtime_document(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "profileSha256": self.profile_sha256,
            "documents": {
                key: value.data for key, value in self.documents.items()
            },
            "layers": [layer.data for layer in self.layers],
            "inputPath": str(self.input_path),
            "inputSha256": self.input_sha256,
            "approvedOutputPath": str(self.approved_output_path),
            "approvedOutputSha256": self.approved_output_sha256,
            "sourceReleaseRoot": str(self.source_release_root),
            "sourceManifestPath": str(self.source_manifest_path),
            "sourceManifestSha256": self.source_manifest_sha256,
            "contactEvidencePath": str(self.contact_evidence_path),
            "contactEvidenceSha256": self.contact_evidence_sha256,
            "lock": self.lock,
            "lockSha256": self.lock_sha256,
            "profileSelector": self.selector,
            "channel": self.channel,
        }
