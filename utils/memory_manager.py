"""
Memory Management Utility
Automatic cleanup of old session data to prevent memory bloat

SAFE: Only removes old/unused data, doesn't affect current functionality
"""

import streamlit as st
from datetime import datetime
import sys
import gc


class MemoryManager:
    """Manages session state memory to prevent accumulation"""
    
    # Configuration
    MAX_STORED_SIMULATIONS = 3  # Keep only last 3 simulation results
    MAX_CACHE_AGE_SECONDS = 3600  # Clear caches older than 1 hour
    
    @staticmethod
    def cleanup_old_simulations():
        """
        Remove old simulation results from session state.
        Keeps only the most recent simulations to free memory.
        
        SAFE: Only affects historical data, not current session
        """
        # Initialize simulation history if not exists
        if 'simulation_history' not in st.session_state:
            st.session_state.simulation_history = []
            return
        
        # Keep only recent simulations
        if len(st.session_state.simulation_history) > MemoryManager.MAX_STORED_SIMULATIONS:
            removed_count = len(st.session_state.simulation_history) - MemoryManager.MAX_STORED_SIMULATIONS
            st.session_state.simulation_history = st.session_state.simulation_history[-MemoryManager.MAX_STORED_SIMULATIONS:]
            
            # Force garbage collection to free memory immediately
            gc.collect()
            
            return removed_count
        
        return 0
    
    @staticmethod
    def get_memory_usage_mb() -> float:
        """Get current Python process memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # psutil not available, use sys module
            return sys.getsizeof(st.session_state) / 1024 / 1024
    
    @staticmethod
    def cleanup_streamlit_caches():
        """
        Clear old Streamlit caches.
        
        SAFE: Streamlit will automatically rebuild caches when needed
        """
        try:
            # Clear data cache (not resource cache - that has connections)
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
        except Exception:
            pass  # Silent fail - not critical
    
    @staticmethod
    def optimize_dataframe_memory(df):
        """
        Optimize DataFrame memory usage without changing data.
        
        SAFE: Only changes internal data types, not values
        
        Args:
            df: pandas DataFrame
            
        Returns:
            Optimized DataFrame (or original if optimization fails)
        """
        try:
            import pandas as pd
            
            # Create copy to avoid modifying original
            df_optimized = df.copy()
            
            # Downcast numeric columns
            for col in df_optimized.select_dtypes(include=['float64']).columns:
                df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='float')
            
            for col in df_optimized.select_dtypes(include=['int64']).columns:
                df_optimized[col] = pd.to_numeric(df_optimized[col], downcast='integer')
            
            # Convert object columns to category if low cardinality
            for col in df_optimized.select_dtypes(include=['object']).columns:
                if df_optimized[col].nunique() / len(df_optimized) < 0.5:
                    df_optimized[col] = df_optimized[col].astype('category')
            
            return df_optimized
        except Exception:
            # If optimization fails, return original
            return df
    
    @staticmethod
    def cleanup_on_simulation_start():
        """Run cleanup tasks before starting a new simulation"""
        MemoryManager.cleanup_old_simulations()
        gc.collect()
    
    @staticmethod
    def cleanup_on_simulation_end(results_df):
        """
        Run cleanup tasks after simulation completes.
        
        Args:
            results_df: Simulation results DataFrame
            
        Returns:
            Optimized DataFrame
        """
        # Optimize the results DataFrame
        results_df = MemoryManager.optimize_dataframe_memory(results_df)
        
        # Store in history (limited)
        if 'simulation_history' not in st.session_state:
            st.session_state.simulation_history = []
        
        st.session_state.simulation_history.append({
            'timestamp': datetime.now().isoformat(),
            'rows': len(results_df),
            'memory_mb': results_df.memory_usage(deep=True).sum() / 1024 / 1024
        })
        
        # Cleanup old entries
        MemoryManager.cleanup_old_simulations()
        
        return results_df
    
    @staticmethod
    def get_memory_stats() -> dict:
        """Get current memory statistics"""
        stats = {
            'process_memory_mb': MemoryManager.get_memory_usage_mb(),
            'stored_simulations': len(st.session_state.get('simulation_history', [])),
            'session_state_keys': len(st.session_state.keys())
        }
        
        # Add DataFrame memory if results exist
        if 'simulation_results' in st.session_state and st.session_state.simulation_results is not None:
            df = st.session_state.simulation_results
            stats['results_memory_mb'] = df.memory_usage(deep=True).sum() / 1024 / 1024
            stats['results_rows'] = len(df)
        
        return stats


# Convenience function
def cleanup_memory():
    """Quick cleanup function - call before heavy operations"""
    return MemoryManager.cleanup_on_simulation_start()
