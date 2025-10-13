"""
Performance Monitoring Utility
Tracks operation timing and provides performance insights

SAFE: Only adds timing measurements, doesn't affect functionality
"""

import time
from contextlib import contextmanager
from typing import Dict, List
import streamlit as st


class PerformanceMonitor:
    """Monitor and track performance of operations"""
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
    
    @contextmanager
    def timer(self, operation_name: str, warn_threshold: float = 1.0):
        """
        Time an operation and optionally warn if slow.
        
        SAFE: Only measures time, doesn't modify functionality
        
        Args:
            operation_name: Name of operation being timed
            warn_threshold: Seconds before showing warning (default: 1.0)
        
        Usage:
            with timer("Running simulation"):
                results = run_simulation(config)
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            
            # Store timing
            if operation_name not in self.timings:
                self.timings[operation_name] = []
            self.timings[operation_name].append(duration)
            
            # Warn if slow
            if duration > warn_threshold:
                st.warning(f"⏱️ {operation_name} took {duration:.2f}s")
    
    def get_stats(self, operation_name: str) -> Dict:
        """Get statistics for an operation"""
        if operation_name not in self.timings:
            return {}
        
        timings = self.timings[operation_name]
        return {
            'count': len(timings),
            'total': sum(timings),
            'average': sum(timings) / len(timings),
            'min': min(timings),
            'max': max(timings)
        }
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all operations"""
        return {
            op: self.get_stats(op)
            for op in self.timings.keys()
        }
    
    def clear(self):
        """Clear all timing data"""
        self.timings.clear()


# Global instance
_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


@contextmanager
def timer(operation_name: str, warn_threshold: float = 1.0):
    """
    Convenience function for timing operations.
    
    Usage:
        from utils.performance import timer
        
        with timer("Loading data"):
            df = load_large_dataset()
    """
    monitor = get_performance_monitor()
    with monitor.timer(operation_name, warn_threshold):
        yield


def show_performance_stats():
    """Display performance statistics in Streamlit"""
    monitor = get_performance_monitor()
    stats = monitor.get_all_stats()
    
    if not stats:
        st.info("No performance data collected yet")
        return
    
    st.subheader("Performance Statistics")
    
    import pandas as pd
    
    # Convert to DataFrame
    rows = []
    for op, data in stats.items():
        rows.append({
            'Operation': op,
            'Count': data['count'],
            'Total (s)': f"{data['total']:.2f}",
            'Average (s)': f"{data['average']:.2f}",
            'Min (s)': f"{data['min']:.2f}",
            'Max (s)': f"{data['max']:.2f}"
        })
    
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("Clear Performance Data"):
        monitor.clear()
        st.rerun()
