from boto3 import client


class SSM:
    """An SSM class that provides a generic boto3 SSM client with specific SSM
    functionality necessary for llama scripts"""

    def __init__(self):
        self.client = client("ssm", region_name="us-east-1")

    def get_parameter_history(self, parameter_key):
        """Get parameter history based on the specified key."""
        response = self.client.get_parameter_history(
            Name=parameter_key, WithDecryption=True
        )
        parameter_history = response["Parameters"]
        return parameter_history

    def get_parameter_value(self, parameter_key):
        """Get parameter value based on the specified key."""
        parameter_object = self.client.get_parameter(
            Name=parameter_key, WithDecryption=True
        )
        parameter_value = parameter_object["Parameter"]["Value"]
        return parameter_value

    def update_parameter_value(self, parameter_key, new_value, parameter_type):
        """Update parameter with specified value."""
        response = self.client.put_parameter(
            Name=parameter_key, Value=new_value, Type=parameter_type, Overwrite=True
        )
        return response
