from contextlib import suppress
from tempfile import TemporaryFile

import pytest
from testfixtures import LogCapture

from application.cms.exceptions import (
    UploadCheckPending,
    UploadCheckFailed,
    UploadCheckVirusFound,
    UnknownFileScanStatus,
)
from tests.utils import UnmockedRequestException


def test_file_is_posted_to_remote_api(scanner_service, requests_mocker):
    # Check that we're definitely making _a_ request by hitting the global unmocked request exception
    with pytest.raises(UnmockedRequestException):
        with TemporaryFile() as tmpfile:
            scanner_service.scan_file(filename="test", fileobj=tmpfile)

    requests_mocker.post("http://scanner-service/requests", json={"status": "ok"})

    # Check that we no longer get an exception after mocking the intended target endpoint
    with TemporaryFile() as tmpfile:
        scanner_service.scan_file(filename="test", fileobj=tmpfile)


@pytest.mark.parametrize("enabled", [True, False])
def test_scanner_service_respects_config_enabled(enabled, scanner_service, requests_mocker):
    scanner_service.enabled = enabled

    if enabled:
        requests_mocker.post("http://scanner-service/requests", json={"status": "ok"})

    with TemporaryFile() as tmpfile:
        assert scanner_service.scan_file(filename="test", fileobj=tmpfile) is enabled


@pytest.mark.parametrize(
    "status, expected_exception",
    (
        ("ok", None),
        ("pending", UploadCheckPending),
        ("failed", UploadCheckFailed),
        ("found", UploadCheckVirusFound),
        ("unknown", UnknownFileScanStatus),
    ),
)
def test_exception_raised_for_scan_results(status, expected_exception, scanner_service, requests_mocker):
    requests_mocker.post("http://scanner-service/requests", json={"status": status})

    context_manager = pytest.raises(expected_exception) if expected_exception else suppress()
    with context_manager:
        with TemporaryFile() as tmpfile:
            scanner_service.scan_file(filename="test", fileobj=tmpfile)


@pytest.mark.parametrize(
    "enabled, status, expected_log_message",
    (
        (False, "ok", "File upload scanning disabled: writing `test` without virus check"),
        (True, "ok", None),
        (True, "pending", "Upload scan pending for `test`: check back for result later"),
        (True, "failed", "Upload scan failed for `test`: {'status': 'failed'}"),
        (True, "found", "Upload scan detected a virus in `test`: {'status': 'found'}"),
        (True, "unknown", "Unrecognised status from scanning service for `test`: {'status': 'unknown'}"),
    ),
)
def test_scanner_service_logging(enabled, status, expected_log_message, scanner_service, requests_mocker):
    scanner_service.enabled = enabled

    requests_mocker.post("http://scanner-service/requests", json={"status": status})

    with LogCapture("application.cms.scanner_service") as log_catcher:
        with TemporaryFile() as tmpfile:
            try:
                scanner_service.scan_file(filename="test", fileobj=tmpfile)
            except Exception:
                pass

        if expected_log_message:
            assert len(log_catcher.records) == 1
            assert log_catcher.records[0].message == expected_log_message
