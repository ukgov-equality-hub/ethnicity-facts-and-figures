
class PageExistsException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class AlreadyApproved(Exception):
    pass


class RejectionImpossible(Exception):
    pass


class IncorrectBranchCheckedOut(Exception):
    pass


class FileUnEditable(Exception):
    pass


class PageUnEditable(Exception):
    pass


class CannotPublishRejected(Exception):
    pass


class PageNotFoundException(Exception):
    pass


class InvalidPageType(Exception):
    pass


class DimensionNotFoundException(Exception):
    pass


class DimensionAlreadyExists(Exception):
    pass


class UploadNotFoundException(Exception):
    pass


class UploadAlreadyExists(Exception):
    pass


class UpdateAlreadyExists(Exception):
    pass
