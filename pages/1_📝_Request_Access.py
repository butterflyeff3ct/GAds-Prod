"""
Request Access Page - Proxy to signup_page
This allows st.switch_page() to work correctly
"""
import streamlit as st
from app.signup_page import main

if __name__ == "__main__":
    main()
