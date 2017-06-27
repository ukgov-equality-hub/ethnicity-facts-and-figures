
class PageExistsException(Exception):
    pass


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
