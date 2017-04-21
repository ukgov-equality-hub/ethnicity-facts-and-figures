
class PageExistsException(Exception):
    pass


class AlreadyApproved(Exception):
    pass


class RejectionImpossible(Exception):
    pass


# Git related exceptions:


class InvalidBranchSpecified(Exception):
    pass


class IncorrectBranchCheckedOut(Exception):
    pass


class GitRepoNotFound(Exception):
    pass

class RepoAlreadyExists(Exception):
    pass
