import numpy as np
import pytest

import moco_iterates as mi

HEADER = ['inDegrees=no', 'num_controls=2', 'num_derivatives=0', 'num_states=3', 'endheader']
COLS = ['time', '/jointset/root/height/value', '/jointset/root/height/speed', '/forceset/motor_a/activation',
        '/forceset/motor_a', '/forceset/residual_height']


def trajectory(tmp_path, name, data):
    mi.write(tmp_path / name, HEADER, COLS, data)
    return tmp_path / name


def physical(n=5):
    t = np.linspace(0, 4, n)
    return np.column_stack([t, .9 + .3 * t, np.full(n, .3), np.linspace(-.2, .6, n), np.linspace(.1, .9, n), np.linspace(-.5, .5, n)])


def test_read_iterate_restores_scale_and_time(tmp_path):
    p = physical(); dump = p.copy(); dump[:, 0] = 0; dump[:, 1:4] *= .5; dump[:, 4:] *= .25
    _, cols, back = mi.read_iterate(trajectory(tmp_path, 'x_trajectory000050.sto', dump), duration=4)
    assert cols == COLS
    np.testing.assert_allclose(back, p)


def test_read_iterate_refuses_missing_time(tmp_path):
    dump = physical(); dump[:, 0] = 0
    with pytest.raises(ValueError):
        mi.read_iterate(trajectory(tmp_path, 'x_trajectory000050.sto', dump))


def test_dump_scale_measures_factors_against_solution(tmp_path):
    p = physical(); trajectory(tmp_path, 'solution.sto', p)
    dump = p.copy(); dump[:, 0] = 0; dump[:, 1:4] *= .5; dump[:, 4:] *= .25
    trajectory(tmp_path, 'run_trajectory000100.sto', dump); trajectory(tmp_path, 'run_trajectory000050.sto', dump * 7)
    assert mi.dump_scale(tmp_path, 150) is None   # no dump at the final iteration
    s = mi.dump_scale(tmp_path, 100)
    assert s['states'] == pytest.approx(.5) and s['controls'] == pytest.approx(.25)
    assert s['states_max_fit_error'] < 1e-12 and s['controls_max_fit_error'] < 1e-12


def test_best_dump_picks_lowest_violation(tmp_path):
    for k in (50, 100, 150):
        trajectory(tmp_path, f'r_trajectory{k:06d}.sto', physical())
    log = tmp_path / 'run.out'
    log.write_text('iter    objective    inf_pr   inf_du\n  50  4.0e+00 3.0e+01 1e-1\n 100r 4.0e+00 2.0e-03 1e-1\n 150  4.1e+00 5.0e-01 1e-1\n')
    k, path, inf = mi.best_dump(tmp_path, log)
    assert (k, inf) == (100, 2e-3) and path.name.endswith('000100.sto')
