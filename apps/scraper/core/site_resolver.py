from urllib.parse import urlparse

from models import BaseSiteResolver


class DomainKeywordSiteResolver(BaseSiteResolver):
    """
    Resolves a URL to a site key by matching known keys against the URL host.

    Example: known_keys=["ynet"] + url=https://www.ynet.co.il/... -> "ynet".
    Keeps O/CP: adding a new site is configuration, not code.
    """

    def __init__(self, known_keys: tuple[str, ...] | list[str]):
        self._known_keys = tuple(known_keys)

    def resolve(self, url: str) -> str | None:
        host = (urlparse(url).hostname or "").lower()
        for key in self._known_keys:
            if key.lower() in host:
                return key
        return None
