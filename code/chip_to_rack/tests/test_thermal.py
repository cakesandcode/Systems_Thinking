"""Tests for the thermal resistance chain model."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from models.thermal import (
    COLD_PLATE_CONFIGS,
    GPU_CONFIGS,
    ThermalConfig,
    compute_thermal_chain,
)


@pytest.fixture
def default_config():
    return ThermalConfig()


@pytest.fixture
def default_results(default_config):
    return compute_thermal_chain(default_config)


class TestResistanceChain:
    def test_r_total_is_sum(self, default_results):
        r = default_results
        expected = r.r1 + r.r2_r3 + r.r4 + r.r5
        assert abs(r.r_total - expected) < 1e-9

    def test_delta_t_total(self, default_results):
        r = default_results
        expected = r.q_tdp * r.r_total
        assert abs(r.delta_t_total - expected) < 1e-9

    def test_t_j_equals_t_in_plus_delta(self, default_results):
        r = default_results
        assert abs(r.t_j - (r.t_in + r.delta_t_total)) < 1e-9

    def test_per_layer_deltas_sum_to_total(self, default_results):
        r = default_results
        layer_sum = r.dt_die + r.dt_cold_plate + r.dt_manifold + r.dt_cdu
        assert abs(layer_sum - r.delta_t_total) < 1e-9


class TestFractions:
    def test_chip_plus_rack_equals_one(self, default_results):
        r = default_results
        assert abs(r.chip_fraction + r.rack_fraction - 1.0) < 1e-9

    def test_sicp_chip_fraction_about_78_pct(self):
        config = ThermalConfig(cold_plate="HP_SiCP")
        r = compute_thermal_chain(config)
        assert 0.75 < r.chip_fraction < 0.82  # ~78%

    def test_jetcool_higher_chip_fraction(self):
        config = ThermalConfig(cold_plate="JetCool")
        r = compute_thermal_chain(config)
        # JetCool has higher R, so chip fraction should be higher
        assert r.chip_fraction > 0.80


class TestJunctionLimit:
    def test_sicp_b200_within_limit(self):
        config = ThermalConfig(gpu="B200_FULL", cold_plate="HP_SiCP", t_in=40.0)
        r = compute_thermal_chain(config)
        assert r.within_limit

    def test_jetcool_b200_check(self):
        config = ThermalConfig(gpu="B200_FULL", cold_plate="JetCool", t_in=40.0)
        r = compute_thermal_chain(config)
        # JetCool with B200 full-spec at 40°C inlet — may or may not be within limit
        # T_j = 40 + 1200 * (0.008 + 0.021 + 0.005 + 0.0003) = 40 + 41.16 = 81.16
        assert r.t_j == pytest.approx(81.16, abs=0.1)

    def test_high_inlet_exceeds_limit(self):
        config = ThermalConfig(gpu="B200_FULL", cold_plate="JetCool", t_in=55.0)
        r = compute_thermal_chain(config)
        # T_j = 55 + 41.16 = 96.16 — exceeds 90°C
        assert not r.within_limit


class TestCrossover:
    def test_sicp_saves_temp_vs_baseline(self):
        config = ThermalConfig(cold_plate="HP_SiCP")
        r = compute_thermal_chain(config)
        # ΔT_saved = Q * (0.021 - 0.010)
        expected = config.q_tdp * (0.021 - 0.010)
        assert abs(r.delta_t_saved_vs_baseline - expected) < 1e-9

    def test_jetcool_zero_savings(self):
        config = ThermalConfig(cold_plate="JetCool")
        r = compute_thermal_chain(config)
        assert abs(r.delta_t_saved_vs_baseline) < 1e-9

    def test_chip_wins_at_nominal(self):
        config = ThermalConfig(
            gpu="B200_FULL", cold_plate="HP_SiCP",
            cdu_drift_c=3.0, flow_starvation_pct=30.0,
        )
        r = compute_thermal_chain(config)
        assert r.chip_wins_ratio > 1.0  # Chip should dominate


class TestFlowStarvation:
    def test_zero_starvation_zero_penalty(self):
        config = ThermalConfig(flow_starvation_pct=0.0)
        r = compute_thermal_chain(config)
        assert r.dt_flow_starvation == 0.0

    def test_reference_point(self):
        # 4°C at 2000W, 30% starvation
        config = ThermalConfig(gpu="B200_FULL", flow_starvation_pct=30.0)
        r = compute_thermal_chain(config)
        # B200_FULL = 1200W, so: 4 * (1200/2000) * (30/30) = 2.4°C
        assert abs(r.dt_flow_starvation - 2.4) < 0.01

    def test_scales_with_tdp(self):
        r_b100 = compute_thermal_chain(ThermalConfig(gpu="B100", flow_starvation_pct=30.0))
        r_b200 = compute_thermal_chain(ThermalConfig(gpu="B200_FULL", flow_starvation_pct=30.0))
        assert r_b200.dt_flow_starvation > r_b100.dt_flow_starvation


class TestGPUConfigs:
    def test_all_gpus_have_tdp(self):
        for key, cfg in GPU_CONFIGS.items():
            assert cfg["tdp_w"] > 0

    def test_b100_is_700w(self):
        assert GPU_CONFIGS["B100"]["tdp_w"] == 700

    def test_b200_full_is_1200w(self):
        assert GPU_CONFIGS["B200_FULL"]["tdp_w"] == 1200


class TestColdPlateConfigs:
    def test_nexalus_disabled(self):
        assert not COLD_PLATE_CONFIGS["Nexalus"]["enabled"]

    def test_sicp_and_jetcool_enabled(self):
        assert COLD_PLATE_CONFIGS["HP_SiCP"]["enabled"]
        assert COLD_PLATE_CONFIGS["JetCool"]["enabled"]

    def test_sicp_lower_r_than_jetcool(self):
        assert COLD_PLATE_CONFIGS["HP_SiCP"]["r_cold_plate"] < COLD_PLATE_CONFIGS["JetCool"]["r_cold_plate"]
