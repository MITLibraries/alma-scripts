import tempfile

from llama.sftp import SFTP


def test_sftp_authenticate(sftp_server, mocked_ssm, sftp_server_private_key):
    sftp = SFTP()
    assert sftp.client.get_host_keys().keys() == []
    sftp.authenticate(
        host=sftp_server.host,
        port=sftp_server.port,
        username="test-dropbox-user",
        private_key=sftp_server_private_key,
    )
    assert sftp.client.get_host_keys().keys()[0].startswith("[127.0.0.1]:") is True


def test_sftp_send_file(sftp_server, mocked_ssm, sftp_server_private_key):
    sftp = SFTP()
    sftp.authenticate(
        host=sftp_server.host,
        port=sftp_server.port,
        username="test-dropbox-user",
        private_key=sftp_server_private_key,
    )
    destination_folder = tempfile.mkdtemp()
    response = sftp.send_file("tests/fixtures/vendor.json", destination_folder)
    assert (response.st_size) == 8678
