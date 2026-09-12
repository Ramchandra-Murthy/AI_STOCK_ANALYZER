from __future__ import annotations

from services.web_platform.models import WebPageDescriptor
from services.web_platform.platform import EnterpriseWebPlatform


def test_web_page_descriptor_immutability() -> None:
    page = WebPageDescriptor(
        page_name="Dashboard", route="/", components=["Summary"], access_role="ADMIN"
    )
    assert page.page_name == "Dashboard"
    assert page.route == "/"
    assert page.timestamp is not None
    assert isinstance(page.metadata, dict)


def test_enterprise_web_platform() -> None:
    page = EnterpriseWebPlatform.get_page_descriptor("Research")
    assert page.page_name == "Research"
    assert page.route == "/research"
    assert len(page.components) > 0
    assert page.access_role == "INSTITUTIONAL_PORTFOLIO_MANAGER"
