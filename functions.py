from urllib.parse import urlparse

def url_has_allowed_host_and_scheme(url, host):
    """
    Check if the given URL has an allowed host and scheme.

    :param url: The URL to check.
    :param host: The allowed host.
    :return: True if the URL has an allowed host and scheme, False otherwise.
    """
    parsed_url = urlparse(url)
    # Check if the URL has the same scheme and host as the allowed host
    return parsed_url.scheme in ('http', 'https') and parsed_url.netloc == host

