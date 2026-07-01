from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parents[1]
APP_FILE = BASE_DIR / "src" / "main" / "python" / "web" / "app.py"
TEMPLATES_DIR = BASE_DIR / "src" / "main" / "python" / "web" / "templates"


def read_file(path):
    return path.read_text(encoding="utf-8")


def test_app_does_not_expose_all_network_interfaces():
    content = read_file(APP_FILE)

    assert 'host="0.0.0.0"' not in content
    assert "host='0.0.0.0'" not in content
    assert 'host="127.0.0.1"' in content or "host='127.0.0.1'" in content


def test_app_does_not_use_datetime_utcnow():
    content = read_file(APP_FILE)

    assert "datetime.utcnow()" not in content
    assert "datetime.now(timezone.utc)" in content


def test_app_does_not_use_broad_exceptions():
    content = read_file(APP_FILE)

    assert "except:" not in content
    assert "except Exception" not in content


def test_routes_have_explicit_methods():
    content = read_file(APP_FILE)
    routes = re.findall(r"@app\.route\((.*?)\)", content)

    assert routes

    for route in routes:
        assert "methods=" in route


def test_order_create_template_literal_is_not_duplicated_in_render_template():
    content = read_file(APP_FILE)

    assert 'ORDER_CREATE_TEMPLATE = "orders/create.html"' in content
    assert 'render_template("orders/create.html"' not in content


def test_external_google_fonts_are_not_used_in_templates():
    html_files = list(TEMPLATES_DIR.rglob("*.html"))

    assert html_files

    for html_file in html_files:
        content = read_file(html_file)

        assert "fonts.googleapis.com" not in content
        assert "fonts.gstatic.com" not in content


def test_bill_detail_table_has_headers():
    bill_detail = TEMPLATES_DIR / "bills" / "detail.html"
    content = read_file(bill_detail)

    assert "<thead" in content
    assert "<tbody" in content
    assert "<th" in content


def test_login_does_not_show_default_credentials():
    login_file = TEMPLATES_DIR / "auth" / "login.html"
    content = read_file(login_file)

    assert "admin123" not in content
    assert "staff123" not in content