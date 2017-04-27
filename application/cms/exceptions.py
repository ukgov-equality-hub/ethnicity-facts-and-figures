
class PageExistsException(Exception):
    pass


class AlreadyApproved(Exception):
    pass


class RejectionImpossible(Exception):
    pass


class IncorrectBranchCheckedOut(Exception):
    pass


class GitRepoNotFound(Exception):
    pass


class RepoAlreadyExists(Exception):
    pass


class CommitMessageCannotBeEmpty(Exception):
    pass


class FileUnEditable(Exception):
    pass


class PageUnEditable(Exception):
    pass


class CannotPublishRejected(Exception):
    pass


class PageNotFoundException(Exception):
    pass
