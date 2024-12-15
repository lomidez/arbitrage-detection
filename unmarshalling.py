"""
:Authors: Lisa Lomidze, Kevin Lundeen
This module contains useful unmarshalling functions for manipulating subscription on the Forex Provider.
"""
import ipaddress
from array import array
from datetime import datetime, timedelta

MAX_QUOTES_PER_MESSAGE = 50
MICROS_PER_SECOND = 1_000_000


def deserialize_price(b: bytes) -> float:
    """
    Convert a byte array back to a float, which represents a price in the Forex price feed.

    :param b: 4-byte sequence representing a float
    :return: floating-point number representing the price
    """
    a = array('f')
    a.frombytes(b)
    return a[0]


def serialize_address(host: str, port: int) -> bytes:
    """
    Convert an IP address and port number into a 6-byte sequence to be sent in a subscription request.

    :param host: IP address as a string (e.g., '127.0.0.1')
    :param port: Port number as an integer
    :return: 6-byte sequence representing the IP and port
    """
    if host == 'localhost':
        host = '127.0.0.1'
    ip = ipaddress.ip_address(host).packed
    p = array('H', [port])
    p.byteswap()
    return ip + p.tobytes()

def deserialize_utcdatetime(b: bytes) -> datetime:
    """
    Convert a byte stream (8 bytes) into a UTC datetime. The byte stream represents
    the number of microseconds since 00:00:00 UTC on January 1, 1970.

    :param b: 8-byte stream representing the timestamp
    :return: datetime object in UTC
    """
    a = array('Q')
    a.frombytes(b)
    a.byteswap()
    micros_since_epoch = a[0]
    epoch = datetime(1970, 1, 1)
    return epoch + timedelta(microseconds=micros_since_epoch)


def unmarshal_message(b: bytes):
    """
    Convert a byte stream into a list of quote dictionaries. Each dictionary contains
    'cross' (currency pair), 'price', and optionally 'time'.

    :param b: byte stream representing multiple quotes
    :return: list of dictionaries with 'cross', 'price', and optionally 'time'
    """
    quotes = []
    default_time = datetime.utcnow()

    for i in range(0, len(b), 32):
        record = b[i:i + 32]
        cross = record[0:3].decode('ascii') + '/' + record[3:6].decode('ascii')
        price = deserialize_price(record[6:10])
        timestamp = deserialize_utcdatetime(record[10:18])

        quote = {'cross': cross, 'price': price, 'time': timestamp}
        quotes.append(quote)

    return quotes
