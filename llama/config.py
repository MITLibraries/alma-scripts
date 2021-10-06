import logging
import os

from llama.ssm import SSM

logger = logging.getLogger(__name__)

ENV = os.getenv("WORKSPACE")
SSM_PATH = os.getenv("SSM_PATH")

logger.info("Configuring llama for current env: %s", ENV)

ssm = SSM()

if ENV == "stage" or ENV == "prod":
    ALMA_API_URL = ssm.get_parameter_value(f"{SSM_PATH}ALMA_API_URL")
    DATA_WAREHOUSE_USER = ssm.get_parameter_value(f"{SSM_PATH}ALMA_DATA_WAREHOUSE_USER")
    DATA_WAREHOUSE_PASSWORD = ssm.get_parameter_value(
        f"{SSM_PATH}ALMA_DATA_WAREHOUSE_PASSWORD"
    )
    DATA_WAREHOUSE_HOST = ssm.get_parameter_value(f"{SSM_PATH}ALMA_DATA_WAREHOUSE_HOST")
    DATA_WAREHOUSE_PORT = ssm.get_parameter_value(f"{SSM_PATH}ALMA_DATA_WAREHOUSE_PORT")
    DATA_WAREHOUSE_SID = ssm.get_parameter_value(f"{SSM_PATH}ALMA_DATA_WAREHOUSE_SID")
elif ENV == "test":
    ALMA_API_KEY = "abc123"
    ALMA_API_URL = "http://example.com/"
    DATA_WAREHOUSE_USER = "test_dw_user"
    DATA_WAREHOUSE_PASSWORD = "test_dw_password"  # nosec
    DATA_WAREHOUSE_HOST = "database.example.com"
    DATA_WAREHOUSE_PORT = "5500"
    DATA_WAREHOUSE_SID = "abcdef"
else:
    ALMA_API_KEY = os.getenv("ALMA_API_KEY")
    ALMA_API_URL = os.getenv("ALMA_API_URL")
    DATA_WAREHOUSE_USER = os.getenv("ALMA_DATA_WAREHOUSE_USER")
    DATA_WAREHOUSE_PASSWORD = os.getenv("ALMA_DATA_WAREHOUSE_PASSWORD")
    DATA_WAREHOUSE_HOST = os.getenv("ALMA_DATA_WAREHOUSE_HOST")
    DATA_WAREHOUSE_PORT = os.getenv("ALMA_DATA_WAREHOUSE_PORT")
    DATA_WAREHOUSE_SID = os.getenv("ALMA_DATA_WAREHOUSE_SID")


def get_alma_api_key(parameter_name=None):
    if ENV == "stage" or ENV == "prod":
        return ssm.get_parameter_value(SSM_PATH + parameter_name)
    else:
        return ALMA_API_KEY
