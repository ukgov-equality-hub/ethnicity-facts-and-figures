from flask import render_template_string
from werkzeug.test import EnvironBuilder, run_wsgi_app


class TestTemplateGlobals:
    def test_static_mode(self, single_use_app):
        @single_use_app.route("/test-globals")
        def test_globals():
            return render_template_string("""{{ static_mode }}""")

        client = single_use_app.test_client()

        single_use_app.config["STATIC_MODE"] = False
        assert client.get("/test-globals").get_data(as_text=True) == "False"

        single_use_app.config["STATIC_MODE"] = True
        assert client.get("/test-globals").get_data(as_text=True) == "True"

        assert client.get("/test-globals?static_mode=no").get_data(as_text=True) == "False"
        assert client.get("/test-globals?static_mode=yes").get_data(as_text=True) == "True"


class TestHeaders:
    def test_http_headers(self, single_use_app):
        builder = EnvironBuilder(path="/", method="GET")
        env = builder.get_environ()

        (app_iter, status, headers) = run_wsgi_app(single_use_app, env)
        assert headers.get("X-Frame-Options") == "deny"
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert headers.get("X-Permitted-Cross-Domain-Policies") == "none"
        assert headers.get("Content-Security-Policy")
