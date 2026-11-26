"""Running behind a reverse proxy that forwards /api to this server (e.g. Vercel in front of Railway).

ORIGIN_SECRET unset (local, Caddy on one machine): nothing changes; the socket address is the client.
ORIGIN_SECRET set: the proxy adds `x-origin-secret` to every forwarded request. Requests without it
are refused, except the health check the hosting platform calls directly. Only for requests that
carry the secret is `x-real-ip` trusted as the visitor's address (Vercel overwrites it, so a visitor
cannot choose it); rate limits then count each visitor separately instead of the proxy as one client.
"""
import hmac
import ipaddress
import os

SECRET_HEADER = 'x-origin-secret'
OPEN_PATHS = frozenset({'/api/v1/health'})


def origin_secret():
    return os.getenv('ORIGIN_SECRET', '')


def via_proxy(request):
    secret = origin_secret()
    sent = request.headers.get(SECRET_HEADER, '')
    return bool(secret) and hmac.compare_digest(sent.encode(), secret.encode())


def allowed(request):
    return not origin_secret() or request.url.path in OPEN_PATHS or via_proxy(request)


def client_address(request):
    if via_proxy(request):
        candidate = request.headers.get('x-real-ip', '').strip()
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            pass
    return request.client.host if request.client else 'unknown'
