from scripts.e2e_model_smoke import e2e_model_smoke


def test_configured_model_over_real_local_http() -> None:
    e2e_model_smoke()
