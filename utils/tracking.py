import streamlit.components.v1 as components
import streamlit as st

def inject_clarity():
    try:
        project_id = st.secrets.get("clarity", {}).get("project_id")
        if not project_id:
            # Silently skip if no project ID configured
            return

        components.html(f"""
            <script type="text/javascript">
              (function(c,l,a,r,i,t,y){{{{ 
                c[a]=c[a]||function(){{{{(c[a].q=c[a].q||[]).push(arguments)}}}};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/{{{{i}}}}";
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
              }}}})(window, document, "clarity", "script", "{project_id}");
            </script>
        """, height=0)
    except Exception:
        # Silently skip if there's any error with Clarity setup
        pass
