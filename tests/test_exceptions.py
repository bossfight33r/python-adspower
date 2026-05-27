from adspower import AdsPowerApiError, AdsPowerConnectionError, AdsPowerError, AdsPowerStuckError

def test_hierarchy():
    assert issubclass(AdsPowerApiError, AdsPowerError)
    assert issubclass(AdsPowerConnectionError, AdsPowerError)
    assert issubclass(AdsPowerStuckError, AdsPowerApiError)

def test_api_error_code():
    err = AdsPowerApiError("rate limited", code=429)
    assert err.code == 429 and str(err) == "rate limited"
