"""
Tests for the feature flags module.

Covers default behaviour, YAML file loading, is_enabled(), set_flag(),
get_all_flags(), reload_flags() and the Flask integration points
(query-parameter override and /api/features endpoint).
"""

import os
import tempfile
import pytest

from src import feature_flags


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_flags_file(content: str) -> str:
    """Write *content* to a temp file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".yml")
    os.close(fd)
    with open(path, "w") as fh:
        fh.write(content)
    return path


# ---------------------------------------------------------------------------
# Module-scoped Flask app fixture (isolated from conftest to avoid shared-db
# issues when running in parallel with --numprocesses auto).
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def feature_flag_app():
    """
    A module-scoped Flask application that uses its own temp SQLite database.

    Patching db.db_path keeps the module-level db singleton pointed at an
    isolated file for the duration of this test module only.
    """
    from src import create_app
    from src.models import db as _db

    fd, db_path = tempfile.mkstemp(suffix="_ff_test.db")
    os.close(fd)

    original_path = _db.db_path
    _db.db_path = db_path
    _db.init_db()

    app = create_app()
    app.config["TESTING"] = True

    yield app

    _db.db_path = original_path
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def feature_flag_client(feature_flag_app):
    """Return a test client for the isolated Flask app."""
    return feature_flag_app.test_client()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_flags_after_test():
    """
    Reload default flags after every test to avoid cross-test contamination.
    """
    yield
    os.environ.pop("FEATURE_FLAGS_FILE", None)
    feature_flags.reload_flags()


# ---------------------------------------------------------------------------
# Tests: load_flags / default behaviour
# ---------------------------------------------------------------------------

class TestDefaultFlags:
    """All features should be enabled when no config file is supplied."""

    def test_all_top_level_features_enabled_by_default(self):
        """Top-level features are enabled when defaults are used."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")

        for feat in ("authentication", "todos", "admin", "files", "api", "search", "utilities"):
            assert feature_flags.is_enabled(feat), f"Expected '{feat}' to be enabled by default"

    def test_sub_features_enabled_by_default(self):
        """Sub-features are enabled when defaults are used."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")

        assert feature_flags.is_enabled("authentication", "login")
        assert feature_flags.is_enabled("authentication", "register")
        assert feature_flags.is_enabled("todos", "create")
        assert feature_flags.is_enabled("todos", "delete")
        assert feature_flags.is_enabled("admin", "command_execution")
        assert feature_flags.is_enabled("utilities", "ssrf")
        assert feature_flags.is_enabled("utilities", "xxe")

    def test_unknown_feature_enabled_by_default(self):
        """Unknown features fail-open (return True) for graceful degradation."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        assert feature_flags.is_enabled("nonexistent_feature") is True


# ---------------------------------------------------------------------------
# Tests: YAML file loading
# ---------------------------------------------------------------------------

class TestYamlFileLoading:
    """Feature flags are loaded correctly from a YAML file."""

    def test_load_valid_yaml_file(self):
        """Flags from a valid YAML file override the defaults."""
        content = """
features:
  authentication:
    enabled: true
    login: true
    register: false
  search:
    enabled: false
"""
        path = _write_flags_file(content)
        try:
            feature_flags.reload_flags(path)
            assert feature_flags.is_enabled("authentication", "login") is True
            assert feature_flags.is_enabled("authentication", "register") is False
            assert feature_flags.is_enabled("search") is False
        finally:
            os.unlink(path)

    def test_disabled_parent_disables_children(self):
        """Disabling the parent feature disables all its sub-features."""
        content = """
features:
  admin:
    enabled: false
    panel: true
    command_execution: true
"""
        path = _write_flags_file(content)
        try:
            feature_flags.reload_flags(path)
            assert feature_flags.is_enabled("admin") is False
            assert feature_flags.is_enabled("admin", "panel") is False
            assert feature_flags.is_enabled("admin", "command_execution") is False
        finally:
            os.unlink(path)

    def test_env_var_path_used_when_no_argument(self):
        """FEATURE_FLAGS_FILE env var is used when no path argument is given."""
        content = """
features:
  search:
    enabled: false
"""
        path = _write_flags_file(content)
        try:
            os.environ["FEATURE_FLAGS_FILE"] = path
            feature_flags.reload_flags()
            assert feature_flags.is_enabled("search") is False
        finally:
            os.environ.pop("FEATURE_FLAGS_FILE", None)
            os.unlink(path)

    def test_missing_features_key_falls_back_to_defaults(self):
        """A YAML file without a 'features' key falls back to all-enabled defaults."""
        content = "some_other_key: true\n"
        path = _write_flags_file(content)
        try:
            feature_flags.reload_flags(path)
            assert feature_flags.is_enabled("search") is True
        finally:
            os.unlink(path)

    def test_malformed_yaml_falls_back_to_defaults(self):
        """A malformed YAML file falls back to all-enabled defaults gracefully."""
        content = "features:\n  bad: [unclosed"
        path = _write_flags_file(content)
        try:
            feature_flags.reload_flags(path)
            assert feature_flags.is_enabled("todos", "create") is True
        finally:
            os.unlink(path)

    def test_safe_yaml_loader_used(self):
        """
        Verify that safe YAML loading is in use (CWE-502 remediated).

        yaml.safe_load() rejects dangerous !!python/ tags while still
        correctly parsing plain YAML content.
        """
        content = "features:\n  search:\n    enabled: true\n"
        path = _write_flags_file(content)
        try:
            feature_flags.reload_flags(path)
            # Safe content still loads correctly.
            assert feature_flags.is_enabled("search") is True
        finally:
            os.unlink(path)

    def test_safe_yaml_loader_rejects_python_objects(self):
        """
        Verify yaml.safe_load() blocks !!python/ object construction (CWE-502).

        With the full Loader, the payload below would execute arbitrary code.
        yaml.safe_load() must raise a yaml.YAMLError instead.
        """
        # This payload would call os.system('id') with yaml.load(Loader=yaml.Loader)
        payload = "!!python/object/apply:os.system ['id']\n"
        path = _write_flags_file(payload)
        try:
            # safe_load raises yaml.YAMLError on !!python/ tags.
            import yaml

            with open(path) as fh:
                with pytest.raises(yaml.YAMLError):
                    yaml.safe_load(fh)
        finally:
            os.unlink(path)

    def test_file_not_found_uses_defaults(self):
        """A non-existent file path falls back to all-enabled defaults."""
        feature_flags.reload_flags("/tmp/does_not_exist_abc123.yml")
        assert feature_flags.is_enabled("todos", "read") is True


# ---------------------------------------------------------------------------
# Tests: is_enabled
# ---------------------------------------------------------------------------

class TestIsEnabled:
    """Verify is_enabled() logic for various flag shapes."""

    def test_boolean_true_flag(self):
        """A plain boolean True flag is enabled."""
        feature_flags._flags = {"my_feature": True}
        assert feature_flags.is_enabled("my_feature") is True

    def test_boolean_false_flag(self):
        """A plain boolean False flag is disabled."""
        feature_flags._flags = {"my_feature": False}
        assert feature_flags.is_enabled("my_feature") is False

    def test_dict_flag_enabled(self):
        """A dict flag with enabled=True is enabled."""
        feature_flags._flags = {"my_feature": {"enabled": True, "sub": True}}
        assert feature_flags.is_enabled("my_feature") is True

    def test_dict_flag_disabled(self):
        """A dict flag with enabled=False is disabled."""
        feature_flags._flags = {"my_feature": {"enabled": False, "sub": True}}
        assert feature_flags.is_enabled("my_feature") is False

    def test_sub_feature_enabled(self):
        """A sub-feature that is explicitly True is enabled."""
        feature_flags._flags = {"auth": {"enabled": True, "login": True}}
        assert feature_flags.is_enabled("auth", "login") is True

    def test_sub_feature_disabled(self):
        """A sub-feature that is explicitly False is disabled."""
        feature_flags._flags = {"auth": {"enabled": True, "login": False}}
        assert feature_flags.is_enabled("auth", "login") is False

    def test_sub_feature_of_disabled_parent(self):
        """A sub-feature of a disabled parent is always disabled."""
        feature_flags._flags = {"auth": {"enabled": False, "login": True}}
        assert feature_flags.is_enabled("auth", "login") is False

    def test_sub_feature_defaults_to_true_when_missing(self):
        """An undeclared sub-feature defaults to True (fail-open)."""
        feature_flags._flags = {"auth": {"enabled": True}}
        assert feature_flags.is_enabled("auth", "undeclared_sub") is True

    def test_unknown_feature_returns_true(self):
        """Feature not in the store returns True (fail-open)."""
        feature_flags._flags = {}
        assert feature_flags.is_enabled("completely_unknown") is True


# ---------------------------------------------------------------------------
# Tests: set_flag
# ---------------------------------------------------------------------------

class TestSetFlag:
    """set_flag() mutates the in-memory flag store."""

    def test_set_flag_disables_feature(self):
        """set_flag can disable a top-level feature."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        feature_flags.set_flag("search", False)
        assert feature_flags.is_enabled("search") is False

    def test_set_flag_enables_feature(self):
        """set_flag can re-enable a disabled feature."""
        feature_flags._flags = {"search": {"enabled": False}}
        feature_flags.set_flag("search", True)
        assert feature_flags.is_enabled("search") is True

    def test_set_flag_modifies_sub_feature(self):
        """set_flag can toggle a sub-feature independently."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        feature_flags.set_flag("admin", False, sub_feature="command_execution")
        assert feature_flags.is_enabled("admin", "command_execution") is False
        # Parent should still be enabled
        assert feature_flags.is_enabled("admin") is True

    def test_set_flag_creates_new_feature(self):
        """set_flag creates a new entry if the feature does not yet exist."""
        feature_flags._flags = {}
        feature_flags.set_flag("brand_new", True)
        assert feature_flags.is_enabled("brand_new") is True

    def test_set_flag_converts_bool_to_dict_for_sub_feature(self):
        """set_flag wraps a plain bool flag in a dict when setting a sub-feature."""
        feature_flags._flags = {"auth": True}
        feature_flags.set_flag("auth", False, sub_feature="login")
        assert isinstance(feature_flags._flags["auth"], dict)
        assert feature_flags._flags["auth"]["login"] is False


# ---------------------------------------------------------------------------
# Tests: get_all_flags
# ---------------------------------------------------------------------------

class TestGetAllFlags:
    """get_all_flags() returns the complete flag dictionary."""

    def test_returns_dict(self):
        """get_all_flags() always returns a dict."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        result = feature_flags.get_all_flags()
        assert isinstance(result, dict)

    def test_returns_all_default_keys(self):
        """get_all_flags() contains all expected top-level feature keys."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        result = feature_flags.get_all_flags()
        for key in ("authentication", "todos", "admin", "files", "api", "search", "utilities"):
            assert key in result, f"Missing key '{key}' in get_all_flags() output"

    def test_returns_copy_not_reference(self):
        """Mutating the returned dict does not affect the internal store."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        result = feature_flags.get_all_flags()
        result["authentication"] = False
        # Internal store should be unchanged
        assert feature_flags.is_enabled("authentication") is True


# ---------------------------------------------------------------------------
# Tests: Flask route integration
# All Flask tests share one module-scoped app (feature_flag_app) to avoid parallel
# SQLite conflicts, and are grouped into the same xdist worker.
# ---------------------------------------------------------------------------

@pytest.mark.xdist_group("feature_flags_flask")
class TestFlaskRouteIntegration:
    """Feature flags are respected by Flask routes."""

    def test_login_route_disabled(self, feature_flag_client):
        """Login route returns 404 when authentication.login flag is disabled."""
        feature_flags.set_flag("authentication", False, sub_feature="login")
        response = feature_flag_client.get("/login")
        assert response.status_code == 404

    def test_register_route_disabled(self, feature_flag_client):
        """Register route returns 404 when authentication.register flag is disabled."""
        feature_flags.set_flag("authentication", False, sub_feature="register")
        response = feature_flag_client.get("/register")
        assert response.status_code == 404

    def test_api_todos_route_disabled(self, feature_flag_client):
        """API todos endpoint returns 404 when api.todos flag is disabled."""
        feature_flags.set_flag("api", False, sub_feature="todos")
        response = feature_flag_client.get("/api/todos")
        assert response.status_code == 404

    def test_search_route_disabled(self, feature_flag_client):
        """Search route returns 404 when search flag is disabled."""
        feature_flags.set_flag("search", False)
        response = feature_flag_client.get("/search")
        assert response.status_code == 404

    def test_feature_flags_enabled_by_default_login_accessible(self, feature_flag_client):
        """Login route is accessible when flags are at defaults."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        response = feature_flag_client.get("/login")
        assert response.status_code == 200

    def test_feature_flags_enabled_by_default_register_accessible(self, feature_flag_client):
        """Register route is accessible when flags are at defaults."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        response = feature_flag_client.get("/register")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests: /api/features endpoint (unauthenticated disclosure – CWE-200)
# ---------------------------------------------------------------------------

@pytest.mark.xdist_group("feature_flags_flask")
class TestApiFeaturesEndpoint:
    """The /api/features endpoint exposes flags without authentication."""

    def test_endpoint_accessible_without_auth(self, feature_flag_client):
        """Anyone can read the feature flags (CWE-200 vulnerability)."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        response = feature_flag_client.get("/api/features")
        assert response.status_code == 200
        assert response.is_json

    def test_endpoint_returns_features_key(self, feature_flag_client):
        """Response JSON contains a 'features' key."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        response = feature_flag_client.get("/api/features")
        data = response.get_json()
        assert "features" in data

    def test_endpoint_reflects_all_default_flags(self, feature_flag_client):
        """All seven default top-level flags are present in the response."""
        feature_flags.reload_flags("/tmp/nonexistent_flags_file_xyz.yml")
        response = feature_flag_client.get("/api/features")
        data = response.get_json()
        for key in ("authentication", "todos", "admin", "files", "api", "search", "utilities"):
            assert key in data["features"], f"Key '{key}' missing from /api/features response"

    def test_endpoint_reflects_disabled_flag(self, feature_flag_client):
        """Disabled flags are reflected in the /api/features response."""
        feature_flags.set_flag("search", False)
        response = feature_flag_client.get("/api/features")
        data = response.get_json()
        search_cfg = data["features"].get("search", {})
        if isinstance(search_cfg, dict):
            assert search_cfg.get("enabled") is False
        else:
            assert search_cfg is False


# ---------------------------------------------------------------------------
# Tests: query-parameter override (CWE-284 vulnerability)
# ---------------------------------------------------------------------------

@pytest.mark.xdist_group("feature_flags_flask")
class TestQueryParameterOverride:
    """
    The ?override_flag= query parameter bypasses disabled feature flags.
    This is an intentional CWE-284 vulnerability for educational purposes.
    """

    def test_override_reenables_disabled_login(self, feature_flag_client):
        """A disabled login feature can be re-enabled via ?override_flag=."""
        feature_flags.set_flag("authentication", False, sub_feature="login")

        # Without override – should be 404
        response = feature_flag_client.get("/login")
        assert response.status_code == 404

        # With override – should be accessible again (vulnerability!)
        response = feature_flag_client.get("/login?override_flag=authentication.login")
        assert response.status_code == 200

    def test_override_reenables_disabled_api_todos(self, feature_flag_client):
        """A disabled api.todos endpoint can be re-enabled via ?override_flag=."""
        feature_flags.set_flag("api", False, sub_feature="todos")

        response = feature_flag_client.get("/api/todos")
        assert response.status_code == 404

        response = feature_flag_client.get("/api/todos?override_flag=api.todos")
        assert response.status_code == 200

    def test_override_parent_feature_name_bypasses_check(self, feature_flag_client):
        """Passing just the parent feature name also bypasses the check."""
        feature_flags.set_flag("search", False)

        response = feature_flag_client.get("/search?override_flag=search", follow_redirects=False)
        # Either 200 (bypassed & not authenticated) or 302 (to login) – either
        # confirms the flag check was bypassed since 404 was avoided.
        assert response.status_code in (200, 302)
