import sqreen


def record_login(sender, **kwargs):
    sqreen.auth_track(True, username=kwargs["user"].email)
