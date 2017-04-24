
class PageExistsException(Exception):
    pass


class AlreadyApproved(Exception):
    pass


class RejectionImpossible(Exception):
    pass


# Git related exceptions:

class IncorrectBranchCheckedOut(Exception):
    pass


class GitRepoNotFound(Exception):
    pass


class RepoAlreadyExists(Exception):
    pass
