"""
:Authors: Lisa Lomidze
Implementation of the subscriber functionality.
"""

import sys
import socket
import threading
from datetime import datetime, timedelta
import unmarshalling as fbs
import bellman_ford
import math

SUBSCRIBER_ADDRESS = ('localhost', 12534)  # Address where subscriber listens
BUF_SZ = 4096
TIMEOUT_SECONDS = 10
QUOTE_EXPIRATION = 1.5 


class Subscriber(object):
    """Class to perform subscriber functionality."""
    
    def __init__(self, subscriber_address, request_address):
        """
        :param subscriber_address: the address where the subscriber listens for data
        :param request_address: the address where subscription requests are sent
        """
        self.subscriber_address = subscriber_address
        self.request_address = request_address
        self.graph = bellman_ford.BellmanFord()
        self.latest_timestamps = {}
    
    def run(self):
        """Starts the listening thread and sends subscription request."""
        listener_thread = threading.Thread(target=self.start_listening, args=(self.subscriber_address,))
        listener_thread.start()
        self.subscribe_to_forex(self.subscriber_address, self.request_address)
    
    def subscribe_to_forex(self, subscriber_address, request_address):
        """
        Sends a subscription request to the Forex Provider.

        :param subscriber_address: the address of the subscriber
        :param request_address: the address of the Forex Provider
        """
        serialized_subscriber_address = fbs.serialize_address(subscriber_address[0], subscriber_address[1])
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(serialized_subscriber_address, request_address)
            print(f"Subscription request sent from {subscriber_address} to {request_address}")

    def start_listening(self, subscriber_address):
        """
        Listens for incoming messages from the Forex Provider and processes them.

        :param subscriber_address: the address on which the subscriber listens for messages
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(subscriber_address)
            sock.settimeout(TIMEOUT_SECONDS)

            while True:
                try:
                    data = sock.recv(BUF_SZ)
                    self.process_received_data(data)
                except socket.timeout:
                    print(f"No messages received in {TIMEOUT_SECONDS} seconds. Subscription was cancelled. Closing listener thread.")
                    break

    def process_received_data(self, data):
        """
        Processes the received data by updating the graph with new rates,
        removing expired quotes, and checking for arbitrage opportunities.

        :param data: the data received from the Forex Provider
        """
        quotes = fbs.unmarshal_message(data)  # unmarshal the received message
        now = datetime.utcnow()  # get the current time

        # Remove expired quotes from the graph
        self.remove_expired_quotes(now)

        for quote in quotes:
            cross = quote['cross']  # the currency pair
            currency1 = cross[:3]
            currency2 = cross[4:]
            price = quote['price']  # the price for the currency pair
            timestamp = quote['time']  # the timestamp of the quote

            # Check if the quote is outdated
            if cross in self.latest_timestamps and timestamp <= self.latest_timestamps[cross]:
                print(f"{timestamp} {currency1} {currency2} {price}")
                print("ignoring out-of-sequence message")
                continue

            print(f"{timestamp} {currency1} {currency2} {price}")

            # Update the timestamp
            self.latest_timestamps[cross] = timestamp

            # Update the graph with the latest rates
            self.update_graph(currency1, currency2, price)

        # Check for arbitrage opportunities after updating the graph
        self.check_for_arbitrage()

    def update_graph(self, currency1, currency2, price):
        """
        Updates the graph with new rates for the given currency pair.

        :param currency1: the first currency in the pair
        :param currency2: the second currency in the pair
        :param price: the price for the currency pair
        """
        if price > 0:
            # Add edge for currency1 -> currency2 with weight -log(rate)
            self.graph.add_edge(currency1, currency2, -math.log10(price))
            # Add edge for currency2 -> currency1 with weight log(rate)
            self.graph.add_edge(currency2, currency1, math.log10(price))

    def remove_expired_quotes(self, current_time):
        """
        Removes expired quotes from the graph if they are older than 1.5 seconds.

        :param current_time: the current time used to compare timestamps
        """
        expired_markets = [market for market, ts in self.latest_timestamps.items()
                           if (current_time - ts).total_seconds() > QUOTE_EXPIRATION]
        for market in expired_markets:
            currency1 = market[:3]
            currency2 = market[4:]

            # Remove edges for the expired currency pair from the graph
            try:
                self.graph.remove_edge(currency1, currency2)
                self.graph.remove_edge(currency2, currency1)
                print(f"removing stale quote for ('{currency1}', '{currency2}')")
            except KeyError:
                pass  # ignore if the edge doesn't exist

            del self.latest_timestamps[market]

    def check_for_arbitrage(self):
        """
        Checks for arbitrage opportunities by running the Bellman-Ford algorithm.
        Only cycles that start and end with USD are considered.
        """
        if 'USD' not in self.graph.vertices:
            return

        start_currency = 'USD'
        dist, prev, neg_cycle_edge = self.graph.shortest_paths(start_currency)

        if neg_cycle_edge:
            self.report_negative_cycle(prev, neg_cycle_edge)

    def report_negative_cycle(self, prev, neg_cycle_edge):
        """
        Reports an arbitrage opportunity if a negative cycle is found.

        :param prev: the dictionary of previous vertices in the shortest path
        :param neg_cycle_edge: the edge that forms part of the negative cycle
        """
        u, v = neg_cycle_edge
        cycle = [v, u]
        while prev[u] not in cycle:
            u = prev[u]
            cycle.append(u)
        cycle.append(prev[u])
        cycle.reverse()

        if cycle[0] != 'USD' or cycle[-1] != 'USD':
            return
    
        initial_currency = cycle[0]
        amount = 100
        print("ARBITRAGE:")
        print(f"\tstart with {initial_currency} {amount}")

        for i in range(len(cycle) - 1):
            from_currency = cycle[i]
            to_currency = cycle[i + 1]
            rate = 10 ** (-self.graph.edges[from_currency][to_currency])  # Convert back to rate
            amount *= rate
            print(f"\texchange {from_currency} for {to_currency} at {rate} --> {to_currency} {amount}")

        print()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python subscriber.py PROVIDER_HOST PROVIDER_PORT")
        exit(1)
    
    REQUEST_ADDRESS = (sys.argv[1], int(sys.argv[2])) # Address where provider waits for subscription
    subscriber = Subscriber(SUBSCRIBER_ADDRESS, REQUEST_ADDRESS)
    subscriber.run()
