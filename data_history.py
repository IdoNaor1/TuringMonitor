"""
Historical Data Manager for Sparkline Graphs
Stores recent data points using circular buffers
"""

import threading
from collections import deque
import time


class DataHistory:
    """Manages historical data points for sparkline rendering"""

    def __init__(self, max_points=30):
        """
        Initialize historical data manager

        Args:
            max_points: Maximum data points to store per metric
        """
        self.histories = {}  # metric_name -> deque of values
        self.max_points = max_points
        self.lock = threading.Lock()

    def add_data_point(self, metric_name, value):
        """
        Add new data point for metric (thread-safe)

        Args:
            metric_name: Name of metric (e.g., 'gpu_percent')
            value: Numeric value to store
        """
        with self.lock:
            if metric_name not in self.histories:
                # Create new deque with max length for automatic eviction
                self.histories[metric_name] = deque(maxlen=self.max_points)

            self.histories[metric_name].append(float(value))

    def get_history(self, metric_name, num_points=None):
        """
        Get recent history for metric (thread-safe)

        Args:
            metric_name: Name of metric
            num_points: Number of recent points to return (None = all)

        Returns:
            list: List of values (empty if metric not found)
        """
        with self.lock:
            if metric_name not in self.histories:
                return []

            values = list(self.histories[metric_name])

            if num_points:
                return values[-num_points:]
            return values

    def clear(self):
        """Clear all historical data"""
        with self.lock:
            self.histories.clear()

    def get_tracked_metrics(self):
        """Get list of all tracked metric names"""
        with self.lock:
            return list(self.histories.keys())


# For testing
if __name__ == "__main__":
    import time

    print("Testing DataHistory...")

    history = DataHistory(max_points=5)

    # Add some test data
    for i in range(10):
        history.add_data_point('test_metric', i * 10)
        time.sleep(0.1)

    # Get history (should only have last 5 points due to maxlen=5)
    data = history.get_history('test_metric')
    print(f"Full history (should be last 5): {data}")

    # Get limited points
    data = history.get_history('test_metric', num_points=3)
    print(f"Last 3 points: {data}")

    # Test multiple metrics
    history.add_data_point('cpu', 45.5)
    history.add_data_point('ram', 67.2)

    print(f"Tracked metrics: {history.get_tracked_metrics()}")

    # Test thread safety by adding from multiple threads
    def add_data():
        for i in range(5):
            history.add_data_point('thread_test', i)

    import threading
    threads = [threading.Thread(target=add_data) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Thread test data: {history.get_history('thread_test')}")
    print("DataHistory test complete!")
