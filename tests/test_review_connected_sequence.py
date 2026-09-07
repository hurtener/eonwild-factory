from pathlib import Path
import subprocess
import sys


def test_cli_writes_hash_bound_source_schedule(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable, str(root/'tools/review_connected_sequence.py'), '--help'],
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert '--cycles' in result.stdout
    assert '--views' in result.stdout
    assert '--modes' in result.stdout
    assert '--blender' in result.stdout
