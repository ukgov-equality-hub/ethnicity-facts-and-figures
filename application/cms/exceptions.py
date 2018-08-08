class AlreadyApproved(Exception):
    pass


class CannotPublishRejected(Exception):
    pass


class CategorisationNotFoundException(Exception):
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


class UploadAlreadyExists(Exception):
    pass


class UploadCheckError(Exception):
    pass


class UploadCheckFailed(Exception):
    pass


class UploadCheckPending(Exception):
    pass


class UploadNotFoundException(Exception):
    pass
