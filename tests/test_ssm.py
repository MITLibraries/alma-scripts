from llama.ssm import SSM


def test_ssm_get_parameter_value(mocked_ssm):
    ssm = SSM()
    parameter_value = ssm.get_parameter_value("/test/example/ALMA_API_ACQ_READ_KEY")
    assert parameter_value == "abc123"
