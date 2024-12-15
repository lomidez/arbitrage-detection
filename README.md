# Detecting Arbitrage Opportunities in Forex Markets

Implementation of a real-time arbitrage detection system for foreign exchange (forex) markets using Python. It employs a publish/subscribe architecture, graph-based algorithms, and real-time data processing to identify profitable arbitrage opportunities.

---

## Features

### Real-Time Arbitrage Detection
- Detects arbitrage opportunities by processing live forex quotes in real-time.
- Uses the **Bellman-Ford Algorithm** to find negative-weight cycles in a currency graph, indicating arbitrage opportunities.

### Publish/Subscribe Architecture
- Implements a subscriber process that listens for forex price updates published over **UDP/IP datagrams**.
- Dynamically updates the currency graph based on the latest quotes and removes expired data.

### Robust Data Handling
- Handles out-of-order messages and discards outdated quotes.
- Ensures accurate results by maintaining time-sensitive price data and bidirectional edges for currency pairs.

---

## Technologies Used

- **Languages/Frameworks**: Python
- **Networking**: Socket Programming (UDP/IP)
- **Algorithms**: Bellman-Ford for cycle detection
- **Utilities**: Custom serialization/deserialization of forex quotes

---

## Usage

### 1. Start the Forex Provider
Run the provided test publisher to simulate forex price feed:
```bash
python provider.py
```

### 2. Run the Arbitrage Detection Subscriber
Run the subscriber to listen for price updates and detect arbitrage opportunities:
```bash
python subscriber.py <PROVIDER_HOST> <PROVIDER_PORT>
```
Replace `<PROVIDER_HOST>` and `<PROVIDER_PORT>` with the address of the running forex provider.

---

## Example Workflow

1. **Subscribe to Forex Provider**:
   The subscriber sends its address to the forex provider and starts receiving price updates.

2. **Process Incoming Quotes**:
   - Updates the currency graph with new exchange rates.
   - Removes expired quotes to maintain data relevance.

3. **Detect Arbitrage**:
   - Runs the Bellman-Ford algorithm on the graph to find negative cycles.
   - Reports any detected arbitrage opportunities, including the sequence of trades and potential profit.

---

## File Structure

- **subscriber.py**: Main subscriber implementation, including network communication and arbitrage detection.
- **unmarshalling.py**: Utilities for unmarshalling forex data.
- **bellman_ford.py**: Implementation of the Bellman-Ford algorithm for cycle detection.
- **provider.py**: Test publisher that simulates a forex price feed.

---

## Contributors

- **Lisa Lomidze**
- **Kevin Lundeen**

