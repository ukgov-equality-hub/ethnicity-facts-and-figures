from unittest import mock
import pytest
import stopit

from application.sitebuilder.build_service import build_site, request_build
from tests.utils import GeneralTestException


def test_build_exceptions_not_suppressed(app):
    with mock.patch("application.sitebuilder.build_service.do_it") as do_it_patch:
        do_it_patch.side_effect = GeneralTestException("build error")

        request_build()

        with pytest.raises(GeneralTestException) as e, stopit.SignalTimeout(1):
            build_site(app)

        assert str(e.value) == "build error"
