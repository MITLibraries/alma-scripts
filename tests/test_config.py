import pytest

from llama.config import Config


def test_prod_stage_config_success(mocked_ssm, monkeypatch):
    monkeypatch.setenv("WORKSPACE", "stage")
    config = Config()
    assert config.ENV == "stage"
    assert config.SSM_PATH == "/test/example/"
    assert config.ALMA_API_URL == "http://example.com/"
    assert config.DATA_WAREHOUSE_USER == "fake_dw_user"
    assert config.DATA_WAREHOUSE_PASSWORD == "fake_dw_password"
    assert config.DATA_WAREHOUSE_HOST == "dw.fake.edu"
    assert config.DATA_WAREHOUSE_PORT == "0000"
    assert config.DATA_WAREHOUSE_SID == "ABCDE"
    assert config.LOG_LEVEL == "warning"
    assert config.SAP_REPORT_RECIPIENT_EMAILS == (
        "report_1@example.com,report_2@example.com"
    )
    assert config.SAP_SUMMARY_RECIPIENT_EMAILS == "summary@example.com"
    assert config.SAP_REPLY_TO_EMAIL == "replyto@example.com"
    assert config.SES_SEND_FROM_EMAIL == "from@example.com"
    assert config.SENTRY_DSN == "sentry_123456"


def test_prod_stage_config_parameter_not_found_raises_error(mocked_ssm, monkeypatch):
    monkeypatch.setenv("WORKSPACE", "stage")
    mocked_ssm.delete_parameter(Name="/test/example/ALMA_API_URL")
    with pytest.raises(Exception) as e:
        Config()
    assert str(e.value) == "Parameter does not exist: /test/example/ALMA_API_URL"


def test_prod_stage_config_missing_values_raises_error(mocked_ssm, monkeypatch):
    monkeypatch.setenv("WORKSPACE", "stage")
    mocked_ssm.put_parameter(
        Name="/test/example/ALMA_API_URL",
        Value="   ",
        Overwrite=True,
    )
    with pytest.raises(Exception) as e:
        Config()
    assert str(e.value) == (
        "LLAMA config is missing the following required config variables for stage "
        "environment: ['ALMA_API_URL']"
    )


def test_load_other_env_config_success():
    config = Config()
    assert config.ENV == "test"
    assert config.SSM_PATH == "/test/example/"
    assert config.ALMA_API_URL == "http://example.com/"
    assert config.DATA_WAREHOUSE_USER == "test_dw_user"
    assert config.DATA_WAREHOUSE_PASSWORD == "test_dw_password"
    assert config.DATA_WAREHOUSE_HOST == "database.example.com"
    assert config.DATA_WAREHOUSE_PORT == "5500"
    assert config.DATA_WAREHOUSE_SID == "abcdef"
    assert config.LOG_LEVEL == "INFO"
    assert config.SAP_REPORT_RECIPIENT_EMAILS == (
        "report_1@example.com,report_2@example.com"
    )
    assert config.SAP_SUMMARY_RECIPIENT_EMAILS == "summary@example.com"
    assert config.SAP_REPLY_TO_EMAIL == "replyto@example.com"
    assert config.SES_SEND_FROM_EMAIL == "from@example.com"
    assert config.SENTRY_DSN is None


def test_get_env_success():
    env = Config.get_env()
    assert env == "test"


def test_get_env_without_workspace_raises_error(monkeypatch):
    monkeypatch.delenv("WORKSPACE", raising=False)
    with pytest.raises(Exception) as e:
        Config.get_env()
    assert str(e.value) == (
        "Env variable 'WORKSPACE' is required in all environments, please set it and "
        "try again."
    )


def test_get_ssm_path_success():
    ssm_path = Config.get_ssm_path("whatever")
    assert ssm_path == "/test/example/"


def test_get_ssm_path_raises_error_in_prod_stage(monkeypatch):
    monkeypatch.delenv("SSM_PATH", raising=False)
    with pytest.raises(Exception) as e:
        Config.get_ssm_path("stage")
    assert str(e.value) == (
        "Env variable 'SSM_PATH' is required in the stage environment, please set it "
        "and try again."
    )


def test_get_ssm_path_returns_none_if_not_set_in_non_prod_stage_env(monkeypatch):
    monkeypatch.delenv("SSM_PATH", raising=False)
    ssm_path = Config.get_ssm_path("whatever")
    assert ssm_path is None


def test_check_sentry_raises_error():
    config = Config()
    config.SENTRY_DSN = "whatever"
    with pytest.raises(ZeroDivisionError):
        config.check_sentry()


def test_check_sentry_does_nothing_if_not_set():
    config = Config()
    assert config.check_sentry() is None


def test_get_alma_api_key_prod_stage(mocked_ssm, monkeypatch):
    monkeypatch.setenv("WORKSPACE", "stage")
    config = Config()
    key = config.get_alma_api_key("ALMA_API_ACQ_READ_KEY")
    assert key == "abc123"


def test_get_alma_api_key_prod_stage_raises_error_if_not_present(
    mocked_ssm, monkeypatch
):
    monkeypatch.setenv("WORKSPACE", "stage")
    config = Config()
    with pytest.raises(Exception) as e:
        config.get_alma_api_key("nothing_here")
    assert str(e.value) == "Parameter does not exist: /test/example/nothing_here"


def test_get_alma_api_key_dev_test():
    config = Config()
    key = config.get_alma_api_key("ALMA_API_ACQ_READ_KEY")
    assert key == "abc123"


def test_get_alma_api_key_dev_test_raises_error_if_not_present():
    config = Config()
    with pytest.raises(KeyError):
        config.get_alma_api_key("nothing_here")


def test_missing_values_returns_missing_values(monkeypatch):
    config = Config()
    missing = config.missing_values()
    assert missing == ["SENTRY_DSN"]


def test_missing_values_returns_empty_list_if_all_present():
    config = Config()
    config.SENTRY_DSN = "something"
    assert config.missing_values() == []


def test_ssm_safety_check_raises_error(monkeypatch):
    monkeypatch.setenv("WORKSPACE", "whatever")
    monkeypatch.setenv("SSM_PATH", "/test/example/prod")
    with pytest.raises(Exception) as e:
        Config()
    assert str(e.value) == (
        "Production SSM_PATH may ONLY be used in the production environment. "
        "Check your env variables and try again."
    )
