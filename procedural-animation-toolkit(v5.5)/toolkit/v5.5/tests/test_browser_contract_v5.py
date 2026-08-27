import json
import re
import unittest
from pathlib import Path

PACK = Path(__file__).resolve().parents[3]
REPO = Path(__file__).resolve().parents[4]
SITE = REPO / "showcase/v5.5/site"
HTML = (SITE / "index.html").read_text()
PAGE_MANIFEST = json.loads((SITE / "asset-manifest.json").read_text())
RELEASE_MANIFEST = json.loads((PACK / "validated_result/v5.5/animation-manifest.v5.5.json").read_text())


class V5_5ShowcaseContractTests(unittest.TestCase):
    def test_all_local_media_references_exist(self):
        refs = set(re.findall(r'(?:src|poster)="([^"]+)"', HTML))
        self.assertTrue(refs)
        self.assertEqual([], sorted(ref for ref in refs if not (SITE / ref).is_file()))
        self.assertFalse(any(ref.startswith(("http://", "https://")) for ref in refs))

    def test_showcase_uses_v5_5_release_manifest(self):
        page_names = {clip["name"] for clip in PAGE_MANIFEST["clips"]}
        release_names = {clip["name"] for clip in RELEASE_MANIFEST["clips"]}
        self.assertEqual(release_names, page_names)
        self.assertEqual(37, len(page_names))
        self.assertTrue(all("_V5_5" in name for name in page_names))

    def test_accessible_playback_contract(self):
        for token in (
            'id="hero-toggle"',
            "syncHeroControl",
            "prefers-reduced-motion",
            "aria-pressed",
            "behaviorVideo.setAttribute('aria-label'",
        ):
            self.assertIn(token, HTML)

    def test_required_review_films_are_packaged(self):
        for name in ("idle-breath", "walk-relaxed-inplace", "eat-loop", "bite-attack"):
            path = SITE / f"media/films/{name}.mp4"
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 100_000)

    def test_asset_manifest_is_offline_and_points_to_hero(self):
        self.assertTrue(PAGE_MANIFEST["offline"])
        self.assertEqual("media/films/walk-relaxed-inplace.mp4", PAGE_MANIFEST["hero"])
        self.assertEqual(960, PAGE_MANIFEST["hero_probe"]["width"])
        self.assertEqual(540, PAGE_MANIFEST["hero_probe"]["height"])


if __name__ == "__main__":
    unittest.main()
