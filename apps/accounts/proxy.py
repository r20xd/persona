"""Resolve Axes IP at the single trusted reverse-proxy boundary."""

from ipaddress import ip_address, ip_network

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def trusted_networks(value):
    try:
        networks = tuple(ip_network(part.strip(), strict=True) for part in value.split(","))
    except ValueError:
        raise ImproperlyConfigured("DJANGO_TRUSTED_PROXY_CIDRS must contain exact CIDRs.") from None
    if not networks or any(network.prefixlen == 0 for network in networks):
        raise ImproperlyConfigured("DJANGO_TRUSTED_PROXY_CIDRS cannot trust every peer.")
    return networks


def client_ip(request):
    try:
        peer = ip_address(request.META.get("REMOTE_ADDR", ""))
    except ValueError:
        return None
    if any(peer in network for network in settings.TRUSTED_PROXY_NETWORKS):
        try:
            return str(ip_address(request.META.get("HTTP_X_REAL_IP", "")))
        except ValueError:
            pass
    return str(peer)
