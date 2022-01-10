from llama.sftp import SFTP


def test_sftp_authenticate(mocked_sftp_server, mocked_ssm, test_sftp_private_key):
    sftp = SFTP()
    assert sftp.client.get_host_keys().keys() == []
    sftp.authenticate(
        host=mocked_sftp_server.host,
        port=mocked_sftp_server.port,
        username="test-dropbox-user",
        private_key=test_sftp_private_key,
    )
    assert sftp.client.get_host_keys().keys()[0].startswith("[127.0.0.1]:") is True


def test_sftp_send_file(mocked_sftp_server, mocked_ssm, test_sftp_private_key):
    sftp = SFTP()
    sftp.authenticate(
        host=mocked_sftp_server.host,
        port=mocked_sftp_server.port,
        username="test-dropbox-user",
        private_key=test_sftp_private_key,
    )
    response = sftp.send_file("I am a file", "dropbox/newfile.txt")
    assert (response.st_size) == 11
