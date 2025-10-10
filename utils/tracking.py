import streamlit.components.v1 as components
import streamlit as st

def inject_clarity():
    project_id = st.secrets.get("clarity", {}).get("project_id", "YOUR_PROJECT_ID")
    if project_id == "to2u5jl3hy":
        st.warning("Microsoft Clarity Project ID is missing.")
        return

    components.html(f"""
        <script type="text/javascript">
          (function(c,l,a,r,i,t,y){{{{ 
            c[a]=c[a]||function(){{{{(c[a].q=c[a].q||[]).push(arguments)}}}};
            t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/{{{{i}}}}";
            y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
          }}}})(window, document, "clarity", "script", "to2u5jl3hy");
        </script>
    """, height=0)
