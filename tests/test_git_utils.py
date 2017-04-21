from application.cms.utils import check_content_repo_exists, create_content_repo, create_all_content_repos


def test_repo_exists(app):
    # x = check_content_repo_exists('draft')
    # if not x:
    create_all_content_repos()
    assert 2 == 1
