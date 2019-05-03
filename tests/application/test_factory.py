from flask import render_template_string


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
