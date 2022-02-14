from llama.ssm import SSM


def test_initialize_ssm_without_endpoint_url():
    ssm = SSM()
    assert ssm.client.meta.endpoint_url == "https://ssm.us-east-1.amazonaws.com"


def test_initialize_ssm_with_endpoint_url(monkeypatch):
    monkeypatch.setenv("SSM_ENDPOINT_URL", "http://example.com")
    ssm = SSM()
    assert ssm.client.meta.endpoint_url == "http://example.com"


def test_ssm_get_parameter_value(mocked_ssm):
    ssm = SSM()
    parameter_value = ssm.get_parameter_value("/test/example/ALMA_API_ACQ_READ_KEY")
    assert parameter_value == "abc123"


def test_ssm_get_parameter_history(mocked_ssm):
    ssm = SSM()
    ssm.update_parameter_value(
        "/test/example/ALMA_API_ACQ_READ_KEY", "def456", "SecureString"
    )
    parameter_history = ssm.get_parameter_history("/test/example/ALMA_API_ACQ_READ_KEY")
    assert parameter_history[0]["Name"] == "/test/example/ALMA_API_ACQ_READ_KEY"
    assert parameter_history[0]["Type"] == "SecureString"
    assert parameter_history[0]["Value"] == "abc123"
    assert parameter_history[0]["Version"] == 1
    assert parameter_history[1]["Name"] == "/test/example/ALMA_API_ACQ_READ_KEY"
    assert parameter_history[1]["Type"] == "SecureString"
    assert parameter_history[1]["Value"] == "def456"
    assert parameter_history[1]["Version"] == 2


def test_ssm_update_parameter_value(mocked_ssm):
    ssm = SSM()
    assert ssm.get_parameter_value("/test/example/ALMA_API_ACQ_READ_KEY") == "abc123"
    ssm.update_parameter_value(
        "/test/example/ALMA_API_ACQ_READ_KEY", "def456", "SecureString"
    )
    assert ssm.get_parameter_value("/test/example/ALMA_API_ACQ_READ_KEY") == "def456"
