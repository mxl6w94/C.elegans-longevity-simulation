"""System tests: the app works end to end for each worm a user can choose."""

from __future__ import annotations

import html
import re

import pytest

# (boxes the user ticks, name shown on the results page, genotype key in the API)
GENOTYPES = [
    (["wild type"], "Wild type (normal worm)", "wild type"),
    (["daf-2"], "daf-2", "daf-2"),
    (["rsks-1"], "rsks-1", "rsks-1"),
    (["daf-2", "rsks-1"], "daf-2 + rsks-1", "daf-2 rsks-1"),
    (["daf-2", "rsks-1", "daf-16"], "daf-16 + daf-2 + rsks-1", "daf-16; daf-2 rsks-1"),
]

ERRORS = [
    ([], "Select at least one gene, or choose Wild type."),
    (["wild type", "daf-2"], "Wild type means no genes are changed, so it can't be combined with other genes."),
    (["daf-16"], "That combination isn't in the dataset."),
    (["daf-16", "rsks-1"], "That combination isn't in the dataset."),
]


def post_genes(client, base_url, genes):
    return client.post(f"{base_url}/", data={"genes": genes}, timeout=10)


# --- the page -------------------------------------------------------------

def test_home_page_loads(client, base_url):
    r = client.get(f"{base_url}/", timeout=10)
    assert r.status_code == 200
    assert "text/html" in r.headers["Content-Type"]
    assert "Choose a worm" in r.text
    assert "Your results will appear here" in r.text


@pytest.mark.parametrize("genes, name, key", GENOTYPES, ids=[g[2] for g in GENOTYPES])
def test_prediction_for_each_worm(client, base_url, genes, name, key):
    r = post_genes(client, base_url, genes)
    assert r.status_code == 200
    assert f"<h2>{html.escape(name)}</h2>" in r.text
    for tile in ("Measured lifespan", "Model estimate", "Measured vs model", "Growth vs normal worm"):
        assert tile in r.text
    assert "doi.org/10.1016/j.celrep.2013.11.018" in r.text
    assert 'id="timelapse"' in r.text
    assert f'data-genotype="{html.escape(key)}"' in r.text
    assert 'class="alert alert-error" role="alert">' not in r.text


@pytest.mark.parametrize("genes, message", ERRORS, ids=["nothing", "wt-plus-gene", "daf-16-alone", "daf-16-rsks-1"])
def test_invalid_selection_shows_error(client, base_url, genes, message):
    r = post_genes(client, base_url, genes)
    assert r.status_code == 200
    assert message in html.unescape(r.text)
    assert 'id="timelapse"' not in r.text


def test_ticked_boxes_are_remembered(client, base_url):
    r = post_genes(client, base_url, ["daf-2", "rsks-1"])
    checked = set(re.findall(r'value="([^"]+)"\s+checked', r.text))
    assert checked == {"daf-2", "rsks-1"}


# --- the JSON API used by the time-lapse graph ----------------------------

def test_api_curves_shape(client, base_url):
    r = client.get(f"{base_url}/api/curves", timeout=10)
    assert r.status_code == 200
    assert r.headers["Content-Type"].startswith("application/json")
    data = r.json()

    assert data["reference"] == "wild type"
    assert list(data["genotypes"])[0] == "wild type", "wild type must come first (legend order)"
    assert set(data["genotypes"]) == {g[2] for g in GENOTYPES}
    assert data["source"]["doi"] == "10.1016/j.celrep.2013.11.018"

    n = len(data["t"])
    assert n > 10 and data["t"][0] == 0
    for key, g in data["genotypes"].items():
        curves = [g["model"]] + ([g["measured"]] if g["measured"] is not None else [])
        for curve in curves:
            assert len(curve) == n, key
            assert curve[0] == pytest.approx(1.0), key
            assert all(b <= a + 1e-9 for a, b in zip(curve, curve[1:])), f"{key}: survival must never rise"
        assert g["color_var"].startswith("--g-"), key


def mean_lifespan(t, curve):
    """Area under a survival curve = mean lifespan."""
    return sum((a + b) / 2 * (t1 - t0) for a, b, t0, t1 in zip(curve, curve[1:], t, t[1:]))


def test_measured_curves_match_the_lab_values(client, base_url):
    """Each measured curve is the wild-type curve stretched to the published lifespan.

    Values: Chen et al. 2013 (core/data/lifespan_reference.csv).
    """
    data = client.get(f"{base_url}/api/curves", timeout=10).json()
    t, g = data["t"], data["genotypes"]

    wt_mean = mean_lifespan(t, g["wild type"]["measured"])
    assert wt_mean == pytest.approx(1.0, abs=0.01), "time axis: 1.0 = wild-type mean lifespan"
    assert g["wild type"]["measured"] == pytest.approx(g["wild type"]["model"], abs=1e-6)

    for key, pct in {"rsks-1": 20, "daf-2": 169, "daf-2 rsks-1": 454}.items():
        assert g[key]["measured_pct"] == pct
        assert mean_lifespan(t, g[key]["measured"]) / wt_mean == pytest.approx(1 + pct / 100, rel=0.01), key

    # No number is published for the triple mutant, so no measured curve is drawn
    assert g["daf-16; daf-2 rsks-1"]["measured_pct"] is None
    assert g["daf-16; daf-2 rsks-1"]["measured"] is None


def test_model_values_match_pipeline_results(client, base_url):
    """Regression check against the committed core/results.

    If the pipeline is re-run and these numbers change on purpose, update them here
    (core/results/lifespan_model_vs_lab.csv has the current values).
    """
    g = client.get(f"{base_url}/api/curves", timeout=10).json()["genotypes"]
    assert g["wild type"]["model_mean_pct"] == pytest.approx(0.0, abs=1e-6)
    assert g["rsks-1"]["model_mean_pct"] == pytest.approx(0.0, abs=0.5)
    assert g["daf-2"]["model_mean_pct"] == pytest.approx(126.1, abs=1.0)
    assert g["daf-2 rsks-1"]["model_mean_pct"] == pytest.approx(116.8, abs=1.0)
    assert g["daf-16; daf-2 rsks-1"]["model_mean_pct"] == pytest.approx(0.0, abs=0.5)
    assert g["daf-2"]["growth_pct"] == pytest.approx(-55.8, abs=0.5)


# --- static files ---------------------------------------------------------

@pytest.mark.parametrize("path, content_type", [
    ("/static/css/main.css", "text/css"),
    ("/static/scripts/main.js", "javascript"),
    ("/static/scripts/timelapse.js", "javascript"),
    ("/static/vendor/chart.umd.min.js", "javascript"),
])
def test_static_files_are_served(client, base_url, path, content_type):
    r = client.get(f"{base_url}{path}", timeout=10)
    assert r.status_code == 200
    assert content_type in r.headers["Content-Type"]
    assert len(r.content) > 100


def test_unknown_route_is_404(client, base_url):
    assert client.get(f"{base_url}/no-such-page", timeout=10).status_code == 404
