# /app/components/schedule_manager.py
"""
Ad Scheduling (Dayparting) Component
Functional UI for setting when ads should show.
"""

import streamlit as st
from typing import Dict, List

def render_ad_schedule_manager(config: Dict):
    """
    Render ad scheduling interface.
    
    Features:
    - Enable/disable scheduling
    - Set hours per day of week
    - Quick presets (Business hours, All day, Custom)
    - Visual calendar view
    """
    
    st.subheader("🕐 Ad Schedule (Dayparting)")
    st.write("Control when your ads show during the week")
    
    # Initialize ad schedule if not exists
    if 'ad_schedule' not in config:
        config['ad_schedule'] = {
            'enabled': False,
            'monday': list(range(24)),
            'tuesday': list(range(24)),
            'wednesday': list(range(24)),
            'thursday': list(range(24)),
            'friday': list(range(24)),
            'saturday': list(range(24)),
            'sunday': list(range(24))
        }
    
    schedule = config['ad_schedule']
    
    # Enable/disable toggle
    schedule['enabled'] = st.checkbox(
        "Enable ad scheduling",
        value=schedule.get('enabled', False),
        help="When disabled, ads show 24/7",
        key="enable_ad_schedule"
    )
    
    if not schedule['enabled']:
        st.info("✅ Ads will show 24 hours a day, 7 days a week")
        return
    
    # Quick presets
    st.write("**Quick Presets:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🕐 All Day", use_container_width=True, key="preset_all_day"):
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                schedule[day] = list(range(24))
            st.rerun()
    
    with col2:
        if st.button("💼 Business Hours", use_container_width=True, key="preset_business"):
            business_hours = list(range(9, 18))  # 9am-5pm
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                schedule[day] = business_hours
            schedule['saturday'] = []
            schedule['sunday'] = []
            st.rerun()
    
    with col3:
        if st.button("📅 Weekdays", use_container_width=True, key="preset_weekdays"):
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
                schedule[day] = list(range(24))
            schedule['saturday'] = []
            schedule['sunday'] = []
            st.rerun()
    
    with col4:
        if st.button("🌙 Extended Hours", use_container_width=True, key="preset_extended"):
            extended_hours = list(range(6, 23))  # 6am-10pm
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                schedule[day] = extended_hours
            st.rerun()
    
    st.markdown("---")
    
    # Day-by-day configuration
    st.write("**Customize by Day:**")
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day, label in zip(days, day_labels):
        with st.expander(f"📅 {label}", expanded=False):
            current_hours = schedule.get(day, list(range(24)))
            
            # All day toggle
            all_day = len(current_hours) == 24
            if st.checkbox(f"All day", value=all_day, key=f"all_day_{day}"):
                schedule[day] = list(range(24))
            else:
                # Hour range selector
                col1, col2 = st.columns(2)
                
                with col1:
                    start_hour = st.selectbox(
                        "Start Hour",
                        options=list(range(24)),
                        index=min(current_hours) if current_hours else 0,
                        format_func=lambda x: f"{x:02d}:00",
                        key=f"start_{day}"
                    )
                
                with col2:
                    end_hour = st.selectbox(
                        "End Hour",
                        options=list(range(24)),
                        index=max(current_hours) if current_hours else 23,
                        format_func=lambda x: f"{x:02d}:00",
                        key=f"end_{day}"
                    )
                
                # Generate hour range
                if end_hour >= start_hour:
                    schedule[day] = list(range(start_hour, end_hour + 1))
                else:
                    # Wraps around midnight
                    schedule[day] = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
                
                st.caption(f"Active: {len(schedule[day])} hours")
    
    # Visual calendar heatmap
    st.markdown("---")
    st.write("**Schedule Visualization:**")
    
    # Create heatmap data
    heatmap_data = []
    for day in days:
        hours = schedule.get(day, [])
        row = [1 if hour in hours else 0 for hour in range(24)]
        heatmap_data.append(row)
    
    # Create HTML heatmap
    html = '<div style="overflow-x: auto;"><table style="border-collapse: collapse; font-size: 11px;">'
    
    # Header row
    html += '<tr><th style="padding: 4px; border: 1px solid #ddd;">Day</th>'
    for hour in range(24):
        html += f'<th style="padding: 4px; border: 1px solid #ddd; font-size: 9px;">{hour:02d}</th>'
    html += '</tr>'
    
    # Data rows
    for day_idx, (day, label) in enumerate(zip(days, day_labels)):
        html += f'<tr><td style="padding: 4px; border: 1px solid #ddd; font-weight: bold;">{label[:3]}</td>'
        for hour in range(24):
            active = hour in schedule.get(day, [])
            color = '#34A853' if active else '#EA4335'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; background-color: {color};"></td>'
        html += '</tr>'
    
    html += '</table></div>'
    html += '<div style="margin-top: 10px;"><span style="color: #34A853;">■</span> Active <span style="margin-left: 20px; color: #EA4335;">■</span> Inactive</div>'
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Summary
    total_hours = sum(len(schedule.get(day, [])) for day in days)
    total_possible = 24 * 7
    coverage_pct = (total_hours / total_possible) * 100
    
    st.metric("Schedule Coverage", f"{coverage_pct:.1f}%", f"{total_hours} of {total_possible} hours")


def render_device_bid_adjustments(config: Dict):
    """
    Render device bid adjustment interface.
    
    Features:
    - Set bid adjustments for mobile, desktop, tablet
    - Show impact on average CPC
    - Best practices guidance
    """
    
    st.subheader("📱 Device Bid Adjustments")
    st.write("Adjust bids based on device type")
    
    if 'device_bid_adjustments' not in config:
        config['device_bid_adjustments'] = {
            'desktop': 1.0,
            'mobile': 1.0,
            'tablet': 1.0
        }
    
    adjustments = config['device_bid_adjustments']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("🖥️ **Desktop**")
        desktop_adj = st.slider(
            "Desktop Adjustment",
            min_value=-90,
            max_value=900,
            value=int((adjustments.get('desktop', 1.0) - 1.0) * 100),
            step=5,
            format="%d%%",
            key="desktop_adjustment",
            help="Increase or decrease bids for desktop users"
        )
        adjustments['desktop'] = 1.0 + (desktop_adj / 100)
        
        if desktop_adj != 0:
            st.caption(f"Multiplier: {adjustments['desktop']:.2f}x")
    
    with col2:
        st.write("📱 **Mobile**")
        mobile_adj = st.slider(
            "Mobile Adjustment",
            min_value=-90,
            max_value=900,
            value=int((adjustments.get('mobile', 1.0) - 1.0) * 100),
            step=5,
            format="%d%%",
            key="mobile_adjustment",
            help="Mobile typically converts lower but has higher volume"
        )
        adjustments['mobile'] = 1.0 + (mobile_adj / 100)
        
        if mobile_adj != 0:
            st.caption(f"Multiplier: {adjustments['mobile']:.2f}x")
    
    with col3:
        st.write("💻 **Tablet**")
        tablet_adj = st.slider(
            "Tablet Adjustment",
            min_value=-90,
            max_value=900,
            value=int((adjustments.get('tablet', 1.0) - 1.0) * 100),
            step=5,
            format="%d%%",
            key="tablet_adjustment",
            help="Tablet often performs between desktop and mobile"
        )
        adjustments['tablet'] = 1.0 + (tablet_adj / 100)
        
        if tablet_adj != 0:
            st.caption(f"Multiplier: {adjustments['tablet']:.2f}x")
    
    # Example impact
    st.markdown("---")
    st.write("**Example Impact:**")
    
    base_bid = 2.00
    col1, col2, col3 = st.columns(3)
    
    with col1:
        final_desktop = base_bid * adjustments['desktop']
        st.metric("Desktop Bid", f"${final_desktop:.2f}", f"${final_desktop - base_bid:+.2f}")
    
    with col2:
        final_mobile = base_bid * adjustments['mobile']
        st.metric("Mobile Bid", f"${final_mobile:.2f}", f"${final_mobile - base_bid:+.2f}")
    
    with col3:
        final_tablet = base_bid * adjustments['tablet']
        st.metric("Tablet Bid", f"${final_tablet:.2f}", f"${final_tablet - base_bid:+.2f}")
    
    # Best practices
    with st.expander("💡 Best Practices", expanded=False):
        st.markdown("""
        **Common Device Adjustments:**
        
        **Mobile:**
        - E-commerce: -20% to -30% (lower conversion rates)
        - Lead gen with calls: +20% to +50% (mobile users call more)
        - Apps: +50% to +100% (mobile primary channel)
        
        **Desktop:**
        - B2B: +10% to +30% (business users on desktop)
        - High-value purchases: +20% to +50% (users research on desktop)
        
        **Tablet:**
        - Usually -10% to +10% (between mobile and desktop)
        - Evening hours: +20% (tablet usage peaks evening)
        """)
