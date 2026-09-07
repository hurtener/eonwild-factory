"""The rapid still wrapper must retain exact source seconds and avoid film flags."""
from pathlib import Path
import importlib.util


path = Path(__file__).resolve().parents[1] / "tools/review_candidate_stills.py"
spec = importlib.util.spec_from_file_location("review_candidate_stills_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_blender_command_requests_only_exact_native_stills():
    command = module.blender_command(blender="blender", root=Path("/repo"),
        package=Path("/candidate"), output=Path("/review/side"), view="side",
        mode="root_motion", times=[0., 23 / 96, 23 / 48], width=480, samples=2)
    assert command[-4:] == ["--still-times", "0.0", repr(23 / 96), repr(23 / 48)]
    assert "--fbx" not in command
    assert "--fps" not in command
    assert command[command.index("--view") + 1] == "side"
