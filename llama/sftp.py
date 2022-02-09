from io import StringIO

import paramiko


class SFTP:
    """An SFTP class with functionality for connecting to a host and sending files."""

    def __init__(self):
        self.client = paramiko.SSHClient()

    def authenticate(
        self, host: str, port: str, username: str, private_key: str
    ) -> None:
        """Authenticate the client to an SFTP host via SSH and a username and
        private key.
        """
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = paramiko.RSAKey.from_private_key(StringIO(private_key))
        self.client.connect(
            hostname=host,
            port=port,
            username=username,
            look_for_keys=False,
            pkey=pkey,
            disabled_algorithms={"keys": ["rsa-sha2-256", "rsa-sha2-512"]},
        )

    def send_file(
        self, file_contents: str, file_path: str
    ) -> paramiko.sftp_attr.SFTPAttributes:
        """Send the string contents of a file to specified path on the SFTP server.

        The file_path parameter should include the path and file name e.g.
        "path/to/file.txt", if no path is included the file will be sent to the home
        folder for the SFTP user. Note that any directories included in the path MUST
        already exist on the server.

        Returns: SFTPAttributes object containing attributes of sent file on the server
        """
        sftp_session = self.client.open_sftp()
        return sftp_session.putfo(StringIO(file_contents), file_path)
