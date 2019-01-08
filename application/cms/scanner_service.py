import enum

import requests

from application.cms.exceptions import (
    UnknownFileScanStatus,
    UploadCheckPending,
    UploadCheckFailed,
    UploadCheckVirusFound,
)
from application.cms.service import Service


class ScannerService(Service):
    class Status(enum.Enum):
        OK = "ok"
        PENDING = "pending"
        FAILED = "failed"
        FOUND = "found"

    def init_app(self, app):
        super().init_app(app)
        self.base_url = self.app.config["ATTACHMENT_SCANNER_URL"]
        self.token = self.app.config["ATTACHMENT_SCANNER_API_TOKEN"]
        self.enabled = self.app.config["ATTACHMENT_SCANNER_ENABLED"]

    def scan_file(self, filename, fileobj) -> bool:
        """
        return: True if scanned and safe; False if not scanned
        raises: child of UploadException if scanned and a problem occurred
        """
        if self.enabled:
            response = requests.post(
                f"{self.base_url}/requests", headers={"Authorization": f"Bearer {self.token}"}, files={"file": fileobj}
            )

            status = response.json()["status"].lower()

            if status == ScannerService.Status.OK.value:
                return True
            elif status == ScannerService.Status.PENDING.value:
                self.logger.warning(f"Upload scan pending for `{filename}`: check back for result later")
                raise UploadCheckPending("Upload check did not complete (pending)")
            elif status == ScannerService.Status.FAILED.value:
                self.logger.error(f"Upload scan failed for `{filename}`: {response.json()}")
                raise UploadCheckFailed("Upload check could not be completed (an error occurred)")
            elif status == ScannerService.Status.FOUND.value:
                self.logger.error(f"Upload scan detected a virus in `{filename}`: {response.json()}")
                raise UploadCheckVirusFound("Virus scan has found something suspicious")
            else:
                self.logger.warning(f"Unrecognised status from scanning service for `{filename}`: {response.json()}")
                raise UnknownFileScanStatus(
                    f"Unrecognised status from scanning service for `{filename}`: {response.json()}"
                )

        else:
            self.logger.warning(f"File upload scanning disabled: writing `{filename}` without virus check")

        return False


scanner_service = ScannerService()
