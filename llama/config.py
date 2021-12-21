import logging
import os

from llama.ssm import SSM

logger = logging.getLogger(__name__)

# Expected configuration values in the form
# "name_of_config_value": "name_of_env_variable_or_ssm_parameter"
EXPECTED_CONFIG_VALUES = {
    "ALMA_API_URL": "ALMA_API_URL",
    "DATA_WAREHOUSE_USER": "ALMA_DATA_WAREHOUSE_USER",
    "DATA_WAREHOUSE_PASSWORD": "ALMA_DATA_WAREHOUSE_PASSWORD",
    "DATA_WAREHOUSE_HOST": "ALMA_DATA_WAREHOUSE_HOST",
    "DATA_WAREHOUSE_PORT": "ALMA_DATA_WAREHOUSE_PORT",
    "DATA_WAREHOUSE_SID": "ALMA_DATA_WAREHOUSE_SID",
    "LOG_LEVEL": "LLAMA_LOG_LEVEL",
    "SAP_REPLY_TO_EMAIL": "SAP_REPLY_TO_EMAIL",
    "SAP_FINAL_RECIPIENT_EMAILS": "SAP_FINAL_RECIPIENT_EMAILS",
    "SAP_REVIEW_RECIPIENT_EMAILS": "SAP_REVIEW_RECIPIENT_EMAILS",
    "SENTRY_DSN": "SENTRY_DSN",
    "SES_SEND_FROM_EMAIL": "SES_SEND_FROM_EMAIL",
}

SSM_ENVS = ("prod", "stage")


class Config:
    def __init__(self):
        self.ENV = self.get_required_env_variable("WORKSPACE")
        print(f"Loading llama config settings for env: {self.ENV}")

        self.SSM_PATH = self.get_required_env_variable("SSM_PATH")
        self.ssm_safety_check()

        self._set_attributes()
        if self.missing_values() and self.ENV in SSM_ENVS:
            raise Exception(
                "LLAMA config is missing the following required config variables "
                f"for {self.ENV} environment: {self.missing_values()}"
            )
        if self.missing_values():
            print(
                "LLAMA config is missing config values, set if needed: "
                f"{self.missing_values()}"
            )

    def _set_attributes(self):
        if self.ENV in SSM_ENVS:
            ssm = SSM()
            for key, value in EXPECTED_CONFIG_VALUES.items():
                try:
                    setattr(self, key, ssm.get_parameter_value(self.SSM_PATH + value))
                except ssm.client.exceptions.ParameterNotFound as e:
                    raise Exception(
                        f"Parameter does not exist: {self.SSM_PATH + value}"
                    ) from e

        else:
            for key, value in EXPECTED_CONFIG_VALUES.items():
                setattr(self, key, os.getenv(value))

    @staticmethod
    def get_required_env_variable(variable_name: str) -> None:
        try:
            return os.environ[variable_name]
        except KeyError as e:
            raise Exception(
                f"Env variable '{variable_name}' is required in all environments, "
                "please set it and try again."
            ) from e

    def check_sentry(self):
        if self.SENTRY_DSN:
            logger.info("Sending a Zero Division Error to Sentry")
            1 / 0
        else:
            logger.info("No Sentry DSN found")

    def get_alma_api_key(self, key_name):
        if self.ENV in SSM_ENVS:
            ssm = SSM()
            try:
                return ssm.get_parameter_value(self.SSM_PATH + key_name)
            except ssm.client.exceptions.ParameterNotFound as e:
                raise Exception(
                    f"Parameter does not exist: {self.SSM_PATH + key_name}"
                ) from e
        else:
            return os.environ[key_name]

    def missing_values(self):
        return list(
            set(["ENV", "SSM_PATH"] + list(EXPECTED_CONFIG_VALUES.keys()))
            - set(
                attribute
                for attribute, value in self.__dict__.items()
                if value and value.strip()
            )
        )

    def ssm_safety_check(self):
        if "prod" in self.SSM_PATH and self.ENV != "prod":
            raise Exception(
                "Production SSM_PATH may ONLY be used in the production "
                "environment. Check your env variables and try again."
            )
