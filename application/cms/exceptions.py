class AlreadyApproved(Exception):
    pass


class CannotChangeSubtopicOncePublished(Exception):
    pass


class CannotPublishRejected(Exception):
    pass


class ClassificationNotFoundException(Exception):
    pass


class ClassificationFinderClassificationNotFoundException(Exception):
    pass


class DimensionClassificationNotFoundException(Exception):
    pass


class DimensionAlreadyExists(Exception):
    pass


class DimensionNotFoundException(Exception):
    pass


class FileUnEditable(Exception):
    pass


class IncorrectBranchCheckedOut(Exception):
    pass


class InvalidPageHierarchy(Exception):
    pass


class InvalidPageType(Exception):
    pass


class PageExistsException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class PageNotFoundException(Exception):
    pass


class PageUnEditable(Exception):
    pass


class RejectionImpossible(Exception):
    pass


class StaleUpdateException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class UpdateAlreadyExists(Exception):
    pass


class UploadError(Exception):
    pass


class UploadAlreadyExists(UploadError):
    pass


class UploadCheckError(UploadError):
    pass


class UploadCheckVirusFound(UploadCheckError):
    pass


class UnknownFileScanStatus(Exception):
    pass


class UploadCheckFailed(UploadError):
    pass


class UploadCheckPending(UploadError):
    pass


class UploadNotFoundException(UploadError):
    pass
