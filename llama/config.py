import logging
import os

from llama.ssm import SSM

ENV = os.getenv("WORKSPACE")
SSM_PATH = os.getenv("SSM_PATH")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
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
    SENTRY_DSN = ssm.get_parameter_value(f"{SSM_PATH}SENTRY_DSN")
elif ENV == "test":
    ALMA_API_KEY = "abc123"
    ALMA_API_URL = "http://example.com/"
    DATA_WAREHOUSE_USER = "test_dw_user"
    DATA_WAREHOUSE_PASSWORD = "test_dw_password"  # nosec
    DATA_WAREHOUSE_HOST = "database.example.com"
    DATA_WAREHOUSE_PORT = "5500"
    DATA_WAREHOUSE_SID = "abcdef"
    SENTRY_DSN = None
else:
    ALMA_API_KEY = os.getenv("ALMA_API_KEY")
    ALMA_API_URL = os.getenv("ALMA_API_URL")
    DATA_WAREHOUSE_USER = os.getenv("ALMA_DATA_WAREHOUSE_USER")
    DATA_WAREHOUSE_PASSWORD = os.getenv("ALMA_DATA_WAREHOUSE_PASSWORD")
    DATA_WAREHOUSE_HOST = os.getenv("ALMA_DATA_WAREHOUSE_HOST")
    DATA_WAREHOUSE_PORT = os.getenv("ALMA_DATA_WAREHOUSE_PORT")
    DATA_WAREHOUSE_SID = os.getenv("ALMA_DATA_WAREHOUSE_SID")
    SENTRY_DSN = os.getenv("SENTRY_DSN")


def check_sentry():
    if SENTRY_DSN:
        logger.info("Sending a Zero Division Error to Sentry")
        1 / 0
    else:
        logger.info("No Sentry DSN found")


def get_alma_api_key(parameter_name=None):
    if ENV == "stage" or ENV == "prod":
        return ssm.get_parameter_value(SSM_PATH + parameter_name)
    else:
        return ALMA_API_KEY
