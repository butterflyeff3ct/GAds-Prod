"""
Dashboard Metrics Caching
Caches expensive dashboard calculations with proper invalidation

SAFE: Uses DataFrame hash as cache key - auto-invalidates when data changes
"""

import streamlit as st
import pandas as pd
import hashlib
from typing import Dict, Tuple


def get_dataframe_hash(df: pd.DataFrame) -> str:
    """
    Create a hash of DataFrame contents for cache key.
    
    SAFE: If data changes, hash changes, cache invalidates automatically
    
    Args:
        df: Input DataFrame
        
    Returns:
        MD5 hash string
    """
    try:
        # Hash the DataFrame content
        return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()
    except Exception:
        # Fallback: use shape and first/last values
        hash_str = f"{df.shape}_{df.iloc[0].sum() if len(df) > 0 else 0}_{df.iloc[-1].sum() if len(df) > 0 else 0}"
        return hashlib.md5(hash_str.encode()).hexdigest()


@st.cache_data(ttl=300)  # Cache for 5 minutes
def calculate_dashboard_metrics(df_hash: str, df: pd.DataFrame) -> Dict:
    """
    Calculate all dashboard metrics with caching.
    
    SAFE: Cache key includes DataFrame hash, so always reflects current data
    
    Args:
        df_hash: Hash of DataFrame (for cache invalidation)
        df: Results DataFrame
        
    Returns:
        Dictionary of calculated metrics
    """
    # Convert to numeric, handling any string data
    numeric_cols = ['cost', 'conversions', 'clicks', 'impressions', 'revenue']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calculate core metrics
    total_clicks = int(df['clicks'].sum())
    total_impressions = int(df['impressions'].sum())
    total_cost = float(df['cost'].sum())
    total_conversions = int(df['conversions'].sum())
    total_revenue = float(df['revenue'].sum())
    
    # Calculate derived metrics (handle division by zero)
    avg_cpc = (total_cost / total_clicks) if total_clicks > 0 else 0
    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cvr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
    roas = (total_revenue / total_cost) if total_cost > 0 else 0
    avg_position = df['position'].mean() if 'position' in df.columns and len(df) > 0 else 0
    cpm = (total_cost / total_impressions * 1000) if total_impressions > 0 else 0
    
    return {
        'total_clicks': total_clicks,
        'total_impressions': total_impressions,
        'total_cost': total_cost,
        'total_conversions': total_conversions,
        'total_revenue': total_revenue,
        'avg_cpc': avg_cpc,
        'ctr': ctr,
        'cvr': cvr,
        'roas': roas,
        'avg_position': avg_position,
        'cpm': cpm
    }


@st.cache_data(ttl=300)  # Cache for 5 minutes
def aggregate_time_series(df_hash: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by datetime for time series charts.
    
    SAFE: Cache invalidates when input data changes
    
    Args:
        df_hash: Hash of DataFrame
        df: Results DataFrame
        
    Returns:
        Aggregated DataFrame
    """
    if 'datetime' not in df.columns:
        return pd.DataFrame()
    
    # Aggregate by datetime
    time_series = df.groupby('datetime').agg({
        'clicks': 'sum',
        'impressions': 'sum',
        'cost': 'sum',
        'conversions': 'sum'
    }).reset_index().sort_values('datetime')
    
    return time_series


@st.cache_data(ttl=300)  # Cache for 5 minutes
def aggregate_keyword_performance(df_hash: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate keyword performance metrics.
    
    SAFE: Cache invalidates when input data changes
    
    Args:
        df_hash: Hash of DataFrame
        df: Results DataFrame
        
    Returns:
        Keyword performance DataFrame
    """
    if 'matched_keyword' not in df.columns:
        return pd.DataFrame()
    
    # Aggregate by keyword
    keyword_agg = df.groupby('matched_keyword').agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'cost': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    # Calculate derived metrics (vectorized, safe)
    keyword_agg['ctr'] = (keyword_agg['clicks'] / keyword_agg['impressions'].replace(0, 1) * 100).fillna(0)
    keyword_agg['cvr'] = (keyword_agg['conversions'] / keyword_agg['clicks'].replace(0, 1) * 100).fillna(0)
    keyword_agg['cpc'] = (keyword_agg['cost'] / keyword_agg['clicks'].replace(0, 1)).fillna(0)
    
    # Sort by cost (top spenders first)
    keyword_agg = keyword_agg.sort_values('cost', ascending=False).head(20)
    
    return keyword_agg


@st.cache_data(ttl=300)  # Cache for 5 minutes
def aggregate_daily_spend(df_hash: str, df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """
    Aggregate daily spend for budget tracking.
    
    SAFE: Cache invalidates when input data changes
    
    Args:
        df_hash: Hash of DataFrame
        df: Results DataFrame
        
    Returns:
        Tuple of (daily spend DataFrame, daily budget)
    """
    if 'day' not in df.columns:
        return pd.DataFrame(), 0.0
    
    # Aggregate by day
    daily_spend = df.groupby('day').agg({'cost': 'sum'}).reset_index()
    
    # Get daily budget from session state
    campaign_config = st.session_state.get('campaign_config', {})
    daily_budget = float(campaign_config.get('daily_budget', 100.0))
    
    return daily_spend, daily_budget


def clear_dashboard_cache():
    """
    Clear all dashboard caches manually.
    
    Use this if you want to force refresh (e.g., after data update)
    """
    calculate_dashboard_metrics.clear()
    aggregate_time_series.clear()
    aggregate_keyword_performance.clear()
    aggregate_daily_spend.clear()
