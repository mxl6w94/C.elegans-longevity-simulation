from pathlib import Path

import pytest

from fluxworm.io.model_loader import load_model, wild_type_sanity_check

MODEL_PATH = Path(__file__).resolve().parents[2] / "fluxworm_iCEL_models" / "iCEL1314.xml"


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="real iCEL1314.xml not present in this checkout")
def test_load_model_and_wt_growth_is_positive():
    model = load_model(MODEL_PATH, biomass_reaction="BIO0010")
    assert len(model.genes) == 1314
    growth = wild_type_sanity_check(model)
    assert growth > 0
