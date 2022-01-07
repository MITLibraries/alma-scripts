import os
from io import StringIO

import paramiko

from llama import CONFIG


class SFTP:
    """An SFTP class with functionality for connecting to a host and sending files."""

    def __init__(self):
        self.client = paramiko.SSHClient()

    def authenticate(
        self,
        host=CONFIG.SAP_DROPBOX_HOST,
        port=CONFIG.SAP_DROPBOX_PORT,
        username=CONFIG.SAP_DROPBOX_USER,
        private_key=CONFIG.SAP_DROPBOX_KEY,
    ):
        """Authenticate the client to an SFTP host via SSH and a username and
        private key.
        """
        client = self.client
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))
        client.connect(
            hostname=host,
            port=port,
            username=username,
            look_for_keys=False,
            pkey=pkey,
        )
        self.client = client

    def send_file(self, file, destination_folder=""):
        """Send a file to the specified destination on the FTP server."""
        sftp_session = self.client.open_sftp()
        file_name = os.path.basename(file)
        full_destination_path = os.path.join(destination_folder, file_name)
        return sftp_session.put(file, full_destination_path)
