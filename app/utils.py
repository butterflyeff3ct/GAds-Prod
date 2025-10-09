"""Utility helpers for Streamlit application."""

from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping

import streamlit as st


def _iter_query_items(params: Mapping[str, object] | MutableMapping[str, object]) -> Iterator[tuple[str, object]]:
    """Yield key/value pairs from a Streamlit query-params container."""

    try:
        return iter(params.items())  # type: ignore[return-value]
    except Exception:
        pass

    try:
        keys: Iterable[str] = params.keys()  # type: ignore[assignment]
    except Exception:
        return iter(())

    return ((key, params.get(key)) for key in keys)  # type: ignore[misc]


def get_query_params() -> Dict[str, List[str]]:
    """Return current query parameters in a Streamlit-version-agnostic way."""

    try:
        raw_params = st.query_params  # Available on recent Streamlit builds.
    except Exception:
        try:
            legacy_params = st.experimental_get_query_params()
        except Exception:
            return {}

        return {key: list(value) for key, value in legacy_params.items()}

    normalised: Dict[str, List[str]] = {}
    for key, value in _iter_query_items(raw_params):
        if isinstance(value, list):
            normalised[key] = value
        elif value is None:
            normalised[key] = []
        else:
            normalised[key] = [str(value)]

    return normalised


def clear_query_params() -> None:
    """Safely clear all Streamlit query parameters."""

    try:
        params = st.query_params
    except Exception:
        params = None

    if params is not None:
        try:
            for key, _ in list(_iter_query_items(params)):
                try:
                    del st.query_params[key]
                except KeyError:
                    # Parameter may have been removed during iteration – ignore.
                    pass
            return
        except Exception:
            pass

    # Fall back to the experimental helper on older Streamlit builds.
    try:
        st.experimental_set_query_params()
    except Exception:
        # As a last resort, swallow the error; failing to clear query params
        # shouldn't block the rest of the login flow.
        pass
