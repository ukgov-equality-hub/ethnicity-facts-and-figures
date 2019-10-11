import os
from tempfile import NamedTemporaryFile

import pytest

from application.cms.exceptions import UploadCheckError


class TestUploadService:
    def setup(self):
        self.temp_file = NamedTemporaryFile(mode="wb", delete=False)

    def teardown(self):
        try:
            os.unlink(self.temp_file.name)

        except OSError:
            pass

    @pytest.mark.parametrize(
        "contents, expected_encoding",
        ((b"ascii", "ASCII"), (b"\xc2\xa5 \xc2\xa9 \xc2\xb5 \xc2\xbc", "UTF-8")),  # "¥ © µ ¼" in UTF-8 encoding
    )
    def test_validate_file(self, app, upload_service, contents, expected_encoding):
        with self.temp_file as tempfile:
            tempfile.write(contents)

        assert upload_service.validate_file(tempfile.name) == expected_encoding

    @pytest.mark.parametrize(
        "contents, expected_error_message",
        (
            (b"", "Please check that you are uploading a CSV file."),
            (
                b"\xff\xfe\x00\x00\xa5\x00\x00\x00",  # "¥" in UTF-32 encoding
                "File encoding UTF-32 not valid. Valid encodings: ASCII, UTF-8",
            ),
        ),
    )
    def test_file_with_invalid_encoding(self, app, upload_service, contents, expected_error_message):
        with self.temp_file as tempfile:
            tempfile.write(contents)

        with pytest.raises(UploadCheckError) as e:
            upload_service.validate_file(tempfile.name)

        assert e.match(expected_error_message)
