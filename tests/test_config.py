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
    assert config.SAP_DROPBOX_HOST == "stage.host"
    assert config.SAP_DROPBOX_PORT == "0000"
    assert config.SAP_DROPBOX_USER == "stage-dropbox-user"
    assert (
        config.SAP_DROPBOX_KEY
        == """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAwFR40KI1SzBR0njomkDDEeS0c4r6+7HoUlzqE24hcnP0eJW1
xa2i1dBMkhm56bhWIIq6w6F9Fg8bd5Tsr72OYsiDpoeJ6KV3RVFDv6Ighja+/WdP
4DroQfq0YVo2XoBSPb5uhv46/pNUa5Y+rwVh+SPQlH8sxE7LZODoy8FD2+GskSUs
jk9Y3Cca5/cv7wafh/i3/De5tE5DG1pLlNwbdAG3xCgcgS2806XCMgA5mXt9HXqn
vyuoyyG2gW6sdHb1pwf8rlgoRLbPqwbLpOi245f5XqLmmwBu4Nxc3scseDXfuHDp
Nky1cOzIBePVxktM2DlAAPQ+7Em23TJr0pmrQQIDAQABAoIBAQCnsX9dufDpzAmr
kAyPYmQzV8wW6lkH2AkOt0DJDD9RgdToxvAkmc7eyq3YvWGibT17RjqtlEJyV13F
mC3+1TIu41IWgxs1pAAoikCd+AiPvXAtlkTI59PWo3dfYr8BCrWqbD4GqehaS69R
10B0bicMibO1pmUsDN++53NTJQG71rZp8o3b39Pse3ON/fQLpflPdaBOGkcyXVu5
UB4UDpO8PHtGU3IsxdpM1AVLpari/cYTksgTVczYtYDcTT4Ud2kuB4Q9OmwDTT2K
uecn7S4FR1FS58ILHhC67gWO/A6DnXTUqwiD8/pDY8QJcRQviWoEBQyhMycZSH+O
enzJtCPZAoGBAPPgVlFRMM99r2zSqT0btIG986Pyh3q8dz8ZvfdwUSIbRgqPAG47
ZukRqIVl2d7S9yVtRnFnDteNokG4d5Mk1a3syn87iFKE6wBpr4htWSlOlntVakou
iQq1ngFcA6ABAwtv2eEa1BPaWMuW7q3yWdOYrC36vX1A03llyp4xFNzfAoGBAMnk
IuT1ZRJZpAqd9SveEqW+aYpUrFetYz3JhVuNT49vJoBiq1RrWvgfuEC7gayEDDfb
Gep11XnXPkXspN6415kdarOgiE9CQlADNG9fk0D61O5ONZZTrqGWEBythfoV2xSk
xb6YDPuxs0S6MylQAc9ZRVUpVGLnytHsKjAMVlvfAoGASxFZ4Iv6V1QbxIaPu5Sk
mm8q6ONFmp0ao5y74cd74eC9TZC5FDVKtyFNW0p/ptwPYUDitxN++RDKyioK/IsR
DwldR46+po/temINuxPVpyZeobYoEo+CdX50FX0KTJ0jH8kdKvJEJ5xFSt25uGdq
CPzsuvZ8j2p97ddMaCc5gccCgYAdUI7wh+FBJNr43661y+0RO/C/MURFBtweIKDI
hmBDB3Sjt7AA9gWjeZebbp6JmjLb+Wht7uYsZuCX7qCR5m0Hwom3w1uHhqtySsTW
Vx5elQ1N/PUy+rukotF8GIYXpgzFlpdP8WwRL+BD3nWHTiK1JNU4ZGPoaJe+m3gU
ufXgKQKBgFdbqJfnSrXyrJcDH9nzMwnR6wyFc0RnILie1lrcQZiru9s/Tlv71GJ/
nMEybyOailEeSlBKYy04uVJGPVO4bnzIiGmJdgZlxxjEwHpx/6bkBnh4YVbRAHgc
al8MbhHvfVaRRdRW8eRVuoeHfPge8fRr7UtloYbOEpZh9nTxMUHj
-----END RSA PRIVATE KEY-----
"""
    )
    assert config.SAP_FINAL_RECIPIENT_EMAILS == (
        "final_1@example.com,final_2@example.com"
    )
    assert config.SAP_REVIEW_RECIPIENT_EMAILS == "review@example.com"
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


def test_load_other_env_config_success(monkeypatch, test_sftp_private_key):
    monkeypatch.setenv("SAP_DROPBOX_KEY", test_sftp_private_key)
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
    assert config.SAP_DROPBOX_HOST == "test.host"
    assert config.SAP_DROPBOX_PORT == "9999"
    assert config.SAP_DROPBOX_USER == "test-dropbox-user"
    assert (
        config.SAP_DROPBOX_KEY
        == """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAwFR40KI1SzBR0njomkDDEeS0c4r6+7HoUlzqE24hcnP0eJW1
xa2i1dBMkhm56bhWIIq6w6F9Fg8bd5Tsr72OYsiDpoeJ6KV3RVFDv6Ighja+/WdP
4DroQfq0YVo2XoBSPb5uhv46/pNUa5Y+rwVh+SPQlH8sxE7LZODoy8FD2+GskSUs
jk9Y3Cca5/cv7wafh/i3/De5tE5DG1pLlNwbdAG3xCgcgS2806XCMgA5mXt9HXqn
vyuoyyG2gW6sdHb1pwf8rlgoRLbPqwbLpOi245f5XqLmmwBu4Nxc3scseDXfuHDp
Nky1cOzIBePVxktM2DlAAPQ+7Em23TJr0pmrQQIDAQABAoIBAQCnsX9dufDpzAmr
kAyPYmQzV8wW6lkH2AkOt0DJDD9RgdToxvAkmc7eyq3YvWGibT17RjqtlEJyV13F
mC3+1TIu41IWgxs1pAAoikCd+AiPvXAtlkTI59PWo3dfYr8BCrWqbD4GqehaS69R
10B0bicMibO1pmUsDN++53NTJQG71rZp8o3b39Pse3ON/fQLpflPdaBOGkcyXVu5
UB4UDpO8PHtGU3IsxdpM1AVLpari/cYTksgTVczYtYDcTT4Ud2kuB4Q9OmwDTT2K
uecn7S4FR1FS58ILHhC67gWO/A6DnXTUqwiD8/pDY8QJcRQviWoEBQyhMycZSH+O
enzJtCPZAoGBAPPgVlFRMM99r2zSqT0btIG986Pyh3q8dz8ZvfdwUSIbRgqPAG47
ZukRqIVl2d7S9yVtRnFnDteNokG4d5Mk1a3syn87iFKE6wBpr4htWSlOlntVakou
iQq1ngFcA6ABAwtv2eEa1BPaWMuW7q3yWdOYrC36vX1A03llyp4xFNzfAoGBAMnk
IuT1ZRJZpAqd9SveEqW+aYpUrFetYz3JhVuNT49vJoBiq1RrWvgfuEC7gayEDDfb
Gep11XnXPkXspN6415kdarOgiE9CQlADNG9fk0D61O5ONZZTrqGWEBythfoV2xSk
xb6YDPuxs0S6MylQAc9ZRVUpVGLnytHsKjAMVlvfAoGASxFZ4Iv6V1QbxIaPu5Sk
mm8q6ONFmp0ao5y74cd74eC9TZC5FDVKtyFNW0p/ptwPYUDitxN++RDKyioK/IsR
DwldR46+po/temINuxPVpyZeobYoEo+CdX50FX0KTJ0jH8kdKvJEJ5xFSt25uGdq
CPzsuvZ8j2p97ddMaCc5gccCgYAdUI7wh+FBJNr43661y+0RO/C/MURFBtweIKDI
hmBDB3Sjt7AA9gWjeZebbp6JmjLb+Wht7uYsZuCX7qCR5m0Hwom3w1uHhqtySsTW
Vx5elQ1N/PUy+rukotF8GIYXpgzFlpdP8WwRL+BD3nWHTiK1JNU4ZGPoaJe+m3gU
ufXgKQKBgFdbqJfnSrXyrJcDH9nzMwnR6wyFc0RnILie1lrcQZiru9s/Tlv71GJ/
nMEybyOailEeSlBKYy04uVJGPVO4bnzIiGmJdgZlxxjEwHpx/6bkBnh4YVbRAHgc
al8MbhHvfVaRRdRW8eRVuoeHfPge8fRr7UtloYbOEpZh9nTxMUHj
-----END RSA PRIVATE KEY-----
"""
    )
    assert config.SAP_FINAL_RECIPIENT_EMAILS == (
        "final_1@example.com,final_2@example.com"
    )
    assert config.SAP_REVIEW_RECIPIENT_EMAILS == "review@example.com"
    assert config.SAP_REPLY_TO_EMAIL == "replyto@example.com"
    assert config.SES_SEND_FROM_EMAIL == "from@example.com"
    assert config.SENTRY_DSN is None


def test_get_required_env_variable_success():
    env = Config.get_required_env_variable("WORKSPACE")
    assert env == "test"


def test_get_required_env_variable_raises_error(monkeypatch):
    monkeypatch.delenv("WORKSPACE", raising=False)
    with pytest.raises(Exception) as e:
        Config.get_required_env_variable("WORKSPACE")
    assert str(e.value) == (
        "Env variable 'WORKSPACE' is required in all environments, please set it and "
        "try again."
    )


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
