# /app/components/extensions_manager.py
"""
Ad Extensions Manager Component
Functional UI for adding and managing all types of ad extensions.
"""

import streamlit as st
from typing import List, Dict

def render_extensions_manager(ad_group_index: int, config: Dict):
    """
    Render ad extensions management interface for an ad group.
    
    Supported extensions:
    - Sitelinks
    - Callouts
    - Structured Snippets
    - Call Extensions
    - Location Extensions (future)
    """
    
    ad_groups = config.get('ad_groups', [])
    if ad_group_index >= len(ad_groups):
        return
    
    ad_group = ad_groups[ad_group_index]
    
    # Initialize extensions dict if not exists
    if 'extensions' not in ad_group:
        ad_group['extensions'] = {
            'sitelinks': [],
            'callouts': [],
            'structured_snippets': {}
        }
    
    extensions = ad_group['extensions']
    
    st.subheader("🔗 Ad Extensions")
    st.write("Enhance your ads with additional information")
    
    # Extensions tabs
    tab1, tab2, tab3 = st.tabs(["Sitelinks", "Callouts", "Structured Snippets"])
    
    # ========== SITELINKS ==========
    with tab1:
        st.write("**Sitelinks** - Additional links to specific pages (+20% CTR)")
        
        if 'sitelinks' not in extensions:
            extensions['sitelinks'] = []
        
        sitelinks = extensions['sitelinks']
        
        # Display existing sitelinks
        if sitelinks:
            for i, sitelink in enumerate(sitelinks):
                col1, col2, col3 = st.columns([3, 3, 1])
                
                with col1:
                    sitelink['text'] = st.text_input(
                        "Link Text",
                        value=sitelink.get('text', ''),
                        max_chars=25,
                        placeholder="Shop New Arrivals",
                        key=f"sitelink_text_{ad_group_index}_{i}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    sitelink['url'] = st.text_input(
                        "URL",
                        value=sitelink.get('url', ''),
                        placeholder="https://example.com/new",
                        key=f"sitelink_url_{ad_group_index}_{i}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    if st.button("🗑️", key=f"del_sitelink_{ad_group_index}_{i}"):
                        sitelinks.pop(i)
                        st.rerun()
        
        # Add new sitelink
        if st.button("➕ Add Sitelink", key=f"add_sitelink_{ad_group_index}"):
            sitelinks.append({'text': '', 'url': '', 'description': ''})
            st.rerun()
        
        st.caption("Google shows up to 4-6 sitelinks. Add at least 2 for best results.")
    
    # ========== CALLOUTS ==========
    with tab2:
        st.write("**Callouts** - Highlight key features (+10% CTR)")
        
        if 'callouts' not in extensions:
            extensions['callouts'] = []
        
        callouts = extensions['callouts']
        
        # Display existing callouts
        if callouts:
            for i, callout in enumerate(callouts):
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    new_text = st.text_input(
                        "Callout",
                        value=callout,
                        max_chars=25,
                        placeholder="Free Shipping",
                        key=f"callout_text_{ad_group_index}_{i}",
                        label_visibility="collapsed"
                    )
                    callouts[i] = new_text
                
                with col2:
                    if st.button("🗑️", key=f"del_callout_{ad_group_index}_{i}"):
                        callouts.pop(i)
                        st.rerun()
        
        # Quick add multiple
        st.write("**Quick Add:**")
        callouts_bulk = st.text_area(
            "Add multiple callouts (one per line)",
            placeholder="Free Shipping\n24/7 Support\n30-Day Returns\nPrice Match Guarantee",
            height=100,
            key=f"callouts_bulk_{ad_group_index}"
        )
        
        if st.button("➕ Add Callouts", key=f"add_callouts_{ad_group_index}"):
            new_callouts = [c.strip() for c in callouts_bulk.split('\n') if c.strip() and len(c.strip()) <= 25]
            callouts.extend(new_callouts)
            st.success(f"Added {len(new_callouts)} callouts!")
            st.rerun()
        
        st.caption("Add at least 4 callouts. Google shows 2-6 at a time.")
        
        # Common callout examples
        with st.expander("💡 Common Callout Examples"):
            st.write("**Shipping & Returns:**")
            st.code("Free Shipping\nFree Returns\nSame-Day Delivery\n2-Day Shipping")
            st.write("**Service & Support:**")
            st.code("24/7 Support\nLive Chat\nPhone Support\nEmail Support")
            st.write("**Guarantees:**")
            st.code("Money-Back Guarantee\nPrice Match\n100% Satisfaction\nLifetime Warranty")
    
    # ========== STRUCTURED SNIPPETS ==========
    with tab3:
        st.write("**Structured Snippets** - Showcase product/service categories (+8% CTR)")
        
        if 'structured_snippets' not in extensions:
            extensions['structured_snippets'] = {}
        
        snippets = extensions['structured_snippets']
        
        # Predefined headers
        snippet_headers = [
            "Amenities", "Brands", "Courses", "Degree programs", "Destinations",
            "Featured hotels", "Insurance coverage", "Models", "Neighborhoods",
            "Service catalog", "Shows", "Styles", "Types"
        ]
        
        selected_header = st.selectbox(
            "Header",
            options=snippet_headers,
            key=f"snippet_header_{ad_group_index}"
        )
        
        current_values = snippets.get(selected_header, [])
        
        values_text = st.text_area(
            "Values (one per line)",
            value='\n'.join(current_values) if current_values else '',
            placeholder="Value 1\nValue 2\nValue 3",
            height=100,
            key=f"snippet_values_{ad_group_index}"
        )
        
        new_values = [v.strip() for v in values_text.split('\n') if v.strip()]
        if new_values:
            snippets[selected_header] = new_values
        elif selected_header in snippets:
            del snippets[selected_header]
        
        st.caption(f"Current snippets: {len(snippets)} headers with {sum(len(v) for v in snippets.values())} total values")
        
        # Show all current snippets
        if snippets:
            st.write("**Active Snippets:**")
            for header, values in snippets.items():
                st.write(f"• {header}: {', '.join(values)}")
    
    # Summary
    st.markdown("---")
    total_extensions = len(extensions.get('sitelinks', [])) + len(extensions.get('callouts', [])) + len(extensions.get('structured_snippets', {}))
    
    if total_extensions > 0:
        st.success(f"✅ {total_extensions} total extensions configured")
        
        # Estimated CTR impact
        estimated_uplift = 0
        if extensions.get('sitelinks'):
            estimated_uplift += min(len(extensions['sitelinks']), 4) * 5  # Up to 20%
        if extensions.get('callouts'):
            estimated_uplift += min(len(extensions['callouts']), 4) * 2.5  # Up to 10%
        if extensions.get('structured_snippets'):
            estimated_uplift += len(extensions['structured_snippets']) * 4  # 4% per snippet
        
        estimated_uplift = min(estimated_uplift, 50)  # Cap at 50%
        st.info(f"📈 Estimated CTR uplift: +{estimated_uplift:.0f}%")
    else:
        st.warning("⚠️ No extensions configured. Add extensions to improve CTR by 10-30%")
