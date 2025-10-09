# /app/campaign_wizard.py
import streamlit as st
from datetime import date, timedelta
import time
from app.state import OBJECTIVES_ENHANCED, GEO_LOCATIONS, AUDIENCE_SEGMENTS
from data_models.schemas import BiddingStrategy
from features.keyword_extractor import KeywordExtractor, ADVANCED_KEYWORDS
from services.gemini_client import get_gemini_client
from core.simulation import run_simulation

# ========== HELPER FUNCTIONS ==========

def calculate_ad_strength(headlines: list, descriptions: list) -> str:
    """Calculate Ad Strength based on Google Ads criteria."""
    score = 0
    
    # Headlines scoring (0-40 points)
    headline_count = len([h for h in headlines if h.strip()])
    if headline_count >= 15:
        score += 40
    elif headline_count >= 10:
        score += 30
    elif headline_count >= 5:
        score += 20
    elif headline_count >= 3:
        score += 10
    
    # Descriptions scoring (0-30 points)
    desc_count = len([d for d in descriptions if d.strip()])
    if desc_count >= 4:
        score += 30
    elif desc_count >= 3:
        score += 20
    elif desc_count >= 2:
        score += 10
    
    # Diversity scoring (0-20 points)
    unique_headlines = len(set([h.lower().strip() for h in headlines if h.strip()]))
    if unique_headlines >= 10:
        score += 20
    elif unique_headlines >= 5:
        score += 15
    elif unique_headlines >= 3:
        score += 10
    
    # Length optimization (0-10 points)
    avg_headline_length = sum(len(h) for h in headlines if h.strip()) / max(1, headline_count)
    avg_desc_length = sum(len(d) for d in descriptions if d.strip()) / max(1, desc_count)
    
    if 20 <= avg_headline_length <= 30 and 70 <= avg_desc_length <= 90:
        score += 10
    elif 15 <= avg_headline_length <= 35 and 60 <= avg_desc_length <= 95:
        score += 5
    
    # Convert score to rating
    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Average"
    else:
        return "Poor"

def get_ad_strength_recommendations(headlines: list, descriptions: list, current_strength: str) -> list:
    """Generate recommendations to improve Ad Strength."""
    recommendations = []
    
    headline_count = len([h for h in headlines if h.strip()])
    desc_count = len([d for d in descriptions if d.strip()])
    
    if headline_count < 15:
        recommendations.append(f"Add more headlines (currently {headline_count}, recommended: 15)")
    
    if desc_count < 4:
        recommendations.append(f"Add more descriptions (currently {desc_count}, recommended: 4)")
    
    # Check for duplicate headlines
    unique_headlines = len(set([h.lower().strip() for h in headlines if h.strip()]))
    if unique_headlines < headline_count * 0.8:
        recommendations.append("Make headlines more unique and diverse")
    
    # Check headline lengths
    short_headlines = [h for h in headlines if h.strip() and len(h) < 20]
    if short_headlines:
        recommendations.append("Expand short headlines to be more descriptive")
    
    # Check description lengths
    short_descriptions = [d for d in descriptions if d.strip() and len(d) < 60]
    if short_descriptions:
        recommendations.append("Add more detail to descriptions")
    
    if current_strength == "Poor":
        recommendations.append("Consider using AI generation to create more diverse ad copy")
    
    return recommendations

def nav_buttons(current_step: int, total_steps: int):
    st.markdown("---")
    cols = st.columns([1, 1, 1, 4])
    if current_step > 1:
        if cols[0].button("⬅️ Back", use_container_width=True):
            st.session_state.campaign_step -= 1; st.rerun()
    if current_step < total_steps:
        if cols[1].button("Next ➡️", use_container_width=True, type="primary"):
            # Validate current step before proceeding
            if validate_current_step(current_step):
                st.session_state.campaign_step += 1; st.rerun()
    if cols[2].button("Cancel", use_container_width=True):
        st.session_state.campaign_step = 0; st.rerun()

def validate_current_step(step: int) -> bool:
    """Validate that required fields are filled for current step"""
    cfg = st.session_state.new_campaign_config
    
    if step == 1:  # Search
        if not cfg.get('objective'):
            st.error("Please select a campaign objective")
            return False
        if not cfg.get('campaign_type'):
            st.error("Please select a campaign type")
            return False
        if not cfg.get('reach_methods'):
            st.error("Please select at least one way to reach your goal")
            return False
    elif step == 2:  # Bidding
        if cfg.get('bidding_focus') == 'conversions' and cfg.get('set_target_cpa'):
            if not cfg.get('target_cpa'):
                st.error("Please enter a Target CPA amount")
                return False
    elif step == 3:  # Campaign settings
        if not cfg.get('campaign_name'):
            st.error("Please enter a campaign name")
            return False
        if not cfg.get('locations'):
            st.error("Please select at least one location")
            return False
    elif step == 4:  # AI Max
        # AI Max step doesn't require validation - all features are optional
        pass
    elif step == 5:  # Keyword and asset generation
        if not cfg.get('ad_groups') or not any(ag.get('keywords') for ag in cfg.get('ad_groups', [])):
            st.error("Please add at least one keyword")
            return False
    elif step == 6:  # Ad groups
        if not cfg.get('ad_groups'):
            st.error("Please create at least one ad group")
            return False
        for i, ag in enumerate(cfg.get('ad_groups', [])):
            if not ag.get('name'):
                st.error(f"Please enter a name for Ad Group {i+1}")
                return False
    elif step == 7:  # Budget
        if cfg.get('budget_type', 'daily') == 'daily' and not cfg.get('daily_budget'):
            st.error("Please enter a daily budget")
            return False
        elif cfg.get('budget_type') == 'total' and not cfg.get('total_budget'):
            st.error("Please enter a total budget")
            return False
    elif step == 8:  # Review
        # Review step doesn't require validation
        pass
    
    return True

def build_full_simulation_config(cfg: dict) -> dict:
    campaign_id = f"cam_{int(time.time())}"
    ad_groups_list, keywords_list, ads_list = [], [], []
    for i, ag in enumerate(cfg.get("ad_groups", [])):
        ag_id = f"ag_{i+1}_{campaign_id}"
        ad_groups_list.append({"id": ag_id, "campaign_id": campaign_id, "name": ag["name"]})
        if ag.get("keywords"):
            for j, line in enumerate(ag["keywords"].strip().split('\n')):
                if not line.strip(): continue
                parts = [p.strip() for p in line.split(',')]
                keywords_list.append({"id": f"kw_{ag_id}_{j}", "ad_group_id": ag_id, "text": parts[0], "match_type": parts[1] if len(parts) > 1 else "broad"})
        ads_list.append({"id": f"ad_{ag_id}", "ad_group_id": ag_id, "headlines": ag.get("headlines", ["Default Headline"]), "descriptions": ag.get("descriptions", ["Default Description"]), "final_url": cfg.get('website_url', "http://example.com")})
    
    return {
        "campaign": {"id": campaign_id, "name": cfg["campaign_name"], "daily_budget": cfg["daily_budget"]},
        "ad_groups": ad_groups_list,
        "keywords": keywords_list,
        "ads": ads_list,
        "simulation": {"days": 7},
        "geo_targets": cfg.get("locations", ["United States"]),
        "device_bid_adjustments": cfg.get("device_bid_adjustments", {})
    }

# ========== MAIN WIZARD RENDERER ==========
def render_campaign_wizard():
    # Initialize configuration if needed
    if 'new_campaign_config' not in st.session_state:
        st.session_state.new_campaign_config = {
            "objective": None,
            "campaign_type": "Search",
            "campaign_name": f"Campaign - {date.today().strftime('%Y-%m-%d')}",
            "daily_budget": 100.0,
            "networks": ["google_search"],
            "delivery_method": "standard",
            "bidding_strategy": "maximize_clicks",
            "target_cpa": 50.0,
            "target_roas": 4.0,
            "locations": ["United States"],
            "ad_groups": []
        }
    
    cfg = st.session_state.new_campaign_config
    
    # Updated step structure based on Google Ads flow
    total_steps = 8  # Search, Bidding, Campaign settings, AI Max, Keyword generation, Ad groups, Budget, Review
    
    # Show progress bar
    st.progress(st.session_state.campaign_step / total_steps, text=f"Step {st.session_state.campaign_step} of {total_steps}")
    
    # --- STEP 1: SEARCH ---
    if st.session_state.campaign_step == 1:
        st.header("Step 1: Search")
        st.write("Choose your campaign objective and type to get started")
        
        # --- Panel 1: Choose your objective ---
        st.subheader("Choose your objective")
        selected_objective = cfg.get('objective')
        
        cols = st.columns(3)
        objectives_list = [
            ("Sales", "💰", "Drive sales online, in app, by phone, or in store"),
            ("Leads", "🎯", "Get leads and other conversions by encouraging customers to take action"),
            ("Website traffic", "🌐", "Get the right people to visit your website"),
            ("Awareness and consideration", "📢", "Reach a broad audience and build interest"),
            ("Local store visits and promotions", "🏪", "Drive visits to local stores"),
            ("App promotion", "📱", "Get more installs, engagement, and pre-registration for your app")
        ]
        
        for i, (obj, icon, desc) in enumerate(objectives_list):
            with cols[i % 3]:
                button_type = "primary" if selected_objective == obj else "secondary"
                if st.button(f"{icon} **{obj}**\n\n{desc}", use_container_width=True, type=button_type, key=f"obj_{obj}"):
                    cfg['objective'] = obj
                    cfg['campaign_name'] = f"{obj} Campaign {date.today().strftime('%Y-%m-%d')}"
                    st.rerun()

        # Show conversion goals and campaign type only if objective is selected
        if selected_objective:
            st.markdown("---")
            
            # --- Panel 2: Conversion goals (for relevant objectives) ---
            if selected_objective in ["Sales", "Leads"]:
                st.subheader(f"Use these conversion goals to improve {selected_objective}")
                
                conversion_goals = {
                    "Sales": ["Purchase", "Add to cart", "Begin checkout"],
                    "Leads": ["Submit lead form", "Sign-ups", "Phone calls", "Contact"]
                }
                
                goals = conversion_goals.get(selected_objective, [])
                selected_goals = st.multiselect(
                    "Active Conversion Goals",
                    options=goals,
                    default=goals[:2] if goals else [],
                    key="conversion_goals"
                )
                cfg['conversion_goals'] = selected_goals
            
            st.markdown("---")
            
            # --- Panel 3: Campaign type ---
            st.subheader("Select a campaign type")
            
            campaign_types = [
                ("Search", "🔍", "Generate leads on Google Search with text ads.", False),
                ("Performance Max", "⚡", "Reach the right people across all of Google's channels.", True),
                ("Demand Gen", "✨", "Generate demand and conversions on YouTube, Google Discover, and Gmail.", True),
                ("Video", "📺", "Generate leads on YouTube with your video ads.", True),
                ("Display", "🖼️", "Reach potential customers across the web with your creative.", True),
                ("Shopping", "🛍️", "Promote your products from your online store on Google.", True)
            ]
            
            type_cols = st.columns(3)
            for i, (name, icon, desc, disabled) in enumerate(campaign_types):
                with type_cols[i % 3]:
                    button_type = "primary" if cfg.get('campaign_type') == name else "secondary"
                    if st.button(
                        f"{icon} **{name}**\n\n{desc}",
                        key=f"ctype_{name}",
                        disabled=disabled,
                        use_container_width=True,
                        type=button_type
                    ):
                        cfg['campaign_type'] = name
                        st.rerun()
            
            st.markdown("---")
            
            # --- Panel 4: Ways to reach goal ---
            st.subheader("Select the ways you'd like to reach your goal")
            
            # Initialize reach_methods as list
            if 'reach_methods' not in cfg:
                cfg['reach_methods'] = []
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Website visits
                website_checked = st.checkbox("🌐 Website visits", value="Website visits" in cfg['reach_methods'])
                if website_checked:
                    if "Website visits" not in cfg['reach_methods']:
                        cfg['reach_methods'].append("Website visits")
                    cfg['website_url'] = st.text_input("Your business's website", value=cfg.get('website_url', ''), placeholder="https://example.com")
                elif "Website visits" in cfg['reach_methods']:
                    cfg['reach_methods'].remove("Website visits")
                
                # Phone calls
                phone_checked = st.checkbox("📞 Phone calls", value="Phone calls" in cfg['reach_methods'])
                if phone_checked:
                    if "Phone calls" not in cfg['reach_methods']:
                        cfg['reach_methods'].append("Phone calls")
                    cfg['phone_number'] = st.text_input("Phone number", value=cfg.get('phone_number', ''), placeholder="(201) 555-0123")
                elif "Phone calls" in cfg['reach_methods']:
                    cfg['reach_methods'].remove("Phone calls")
            
            with col2:
                # Store visits
                store_checked = st.checkbox("🏪 Store visits", value="Store visits" in cfg['reach_methods'], help="Location targeting in later steps")
                if store_checked and "Store visits" not in cfg['reach_methods']:
                    cfg['reach_methods'].append("Store visits")
                elif not store_checked and "Store visits" in cfg['reach_methods']:
                    cfg['reach_methods'].remove("Store visits")
                
                # Lead forms
                lead_form_checked = st.checkbox("📋 Lead form submissions", value="Lead form submissions" in cfg['reach_methods'])
                if lead_form_checked and "Lead form submissions" not in cfg['reach_methods']:
                    cfg['reach_methods'].append("Lead form submissions")
                elif not lead_form_checked and "Lead form submissions" in cfg['reach_methods']:
                    cfg['reach_methods'].remove("Lead form submissions")
        
        nav_buttons(1, total_steps)
    
    # --- STEP 2: BIDDING ---
    elif st.session_state.campaign_step == 2:
        st.header("Step 2: Bidding")
        st.error("⚠️ Bidding strategy needs attention")
        
        # Main bidding panel
        with st.container():
            st.subheader("Bidding")
            
            # What do you want to focus on?
            bidding_focus = st.selectbox(
                "What do you want to focus on? ℹ️",
                options=["Conversions", "Clicks", "Impression share", "Views"],
                index=0 if cfg.get('bidding_focus', 'Conversions') == 'Conversions' else 1,
                help="Choose your primary bidding goal"
            )
            cfg['bidding_focus'] = bidding_focus
            
            # Set target cost per action (optional)
            if bidding_focus == "Conversions":
                set_target = st.checkbox("☑️ Set a target cost per action (optional)", value=cfg.get('set_target_cpa', False))
                cfg['set_target_cpa'] = set_target
                
                if set_target:
                    st.write("Target CPA ℹ️")
                    target_cpa = st.number_input(
                        "$",
                        min_value=0.01,
                        value=cfg.get('target_cpa', 50.0),
                        step=1.0,
                        help="Enter an amount",
                        label_visibility="collapsed"
                    )
                    cfg['target_cpa'] = target_cpa
                
                st.info("Alternative bid strategies like portfolios are available in settings after you create your campaign")
        
        st.markdown("---")
        
        # Customer acquisition panel
        with st.container():
            st.subheader("Customer acquisition")
            
            new_customers_only = st.checkbox(
                "Bid for new customers only",
                value=cfg.get('new_customers_only', False)
            )
            cfg['new_customers_only'] = new_customers_only
            
            if new_customers_only:
                st.write("Your campaign will be limited to only new customers, regardless of your bid strategy")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("By default, your campaign bids equally for new and existing customers. However, you can configure your customer acquisition settings to optimize for acquiring new customers.")
            with col2:
                st.link_button("Learn more about customer acquisition", "https://support.google.com/google-ads/answer/12080169", use_container_width=True)
        
        nav_buttons(2, total_steps)
    
    # --- STEP 3: CAMPAIGN SETTINGS ---
    elif st.session_state.campaign_step == 3:
        st.header("Step 3: Campaign settings")
        st.success("✅ Campaign settings configured")
        st.write("To reach the right people, start by defining key settings for your campaign")
        
        # Main settings section
        with st.container():
            # Networks section
            with st.expander("**Networks**", expanded=True):
                st.write("Search partners, Display Network")
                
                # Search network is always selected for Search campaigns
                st.checkbox("Google search", value=True, disabled=True, help="Always included for Search campaigns")
                
                # Include search partners option
                include_partners = st.checkbox(
                    "Include Google search partners",
                    value=cfg.get('include_search_partners', True),
                    help="Sites in the Search Network that partner with Google to show ads"
                )
                cfg['include_search_partners'] = include_partners
                
                # Display network option
                include_display = st.checkbox(
                    "Include Display Network",
                    value=cfg.get('include_display', False),
                    help="Google sites like YouTube, Blogger, Gmail and thousands of partnering websites"
                )
                cfg['include_display'] = include_display
            
            # Locations section
            with st.expander("**Locations**", expanded=True):
                location_type = st.radio(
                    "Location targeting",
                    ["All countries and territories", "Enter another location", "United States"],
                    index=2 if "United States" in cfg.get('locations', []) else 0,
                    label_visibility="collapsed"
                )
                
                if location_type == "Enter another location":
                    locations = st.text_area(
                        "Enter locations (one per line)",
                        placeholder="New York, United States\nCalifornia, United States\nTexas, United States",
                        help="Enter cities, states, countries, or postal codes"
                    )
                    cfg['locations'] = [l.strip() for l in locations.split('\n') if l.strip()]
                elif location_type == "United States":
                    cfg['locations'] = ["United States"]
                else:
                    cfg['locations'] = ["All countries and territories"]
                
                # Location options
                st.write("**Location options:**")
                location_target_type = st.radio(
                    "Target",
                    ["Presence: People in or regularly in your targeted locations (recommended)", 
                     "Presence or interest: People in, regularly in, or who've shown interest in your targeted locations",
                     "Search interest: People searching for your targeted locations"],
                    index=0,
                    label_visibility="collapsed"
                )
                cfg['location_target_type'] = location_target_type.split(":")[0]
                
                # Exclude locations
                exclude_locations = st.checkbox("Exclude locations", value=cfg.get('exclude_locations', False))
                if exclude_locations:
                    cfg['excluded_locations'] = st.text_area(
                        "Locations to exclude",
                        placeholder="Enter locations to exclude (one per line)",
                        value=cfg.get('excluded_locations', '')
                    )
            
            # Languages section
            with st.expander("**Languages**", expanded=True):
                language_targeting = st.radio(
                    "Language targeting",
                    ["All languages", "English", "Select specific languages"],
                    index=1 if cfg.get('languages', ['English']) == ['English'] else 0
                )
                
                if language_targeting == "Select specific languages":
                    languages = st.multiselect(
                        "Select languages",
                        options=["English", "Spanish", "French", "German", "Italian", "Portuguese", 
                                "Russian", "Japanese", "Korean", "Chinese (simplified)", "Chinese (traditional)", 
                                "Arabic", "Hindi", "Dutch", "Polish"],
                        default=cfg.get('languages', ["English"])
                    )
                    cfg['languages'] = languages
                elif language_targeting == "English":
                    cfg['languages'] = ["English"]
                else:
                    cfg['languages'] = ["All languages"]
            
            # Dynamic Search Ads section
            with st.expander("**Dynamic Search Ads**", expanded=False):
                enable_dsa = st.checkbox(
                    "Enable Dynamic Search Ads",
                    value=cfg.get('enable_dsa', False),
                    help="Let Google automatically create ads based on your website content"
                )
                cfg['enable_dsa'] = enable_dsa
                
                if enable_dsa:
                    st.write("**DSA Configuration:**")
                    
                    # Website URL for DSA
                    dsa_website_url = st.text_input(
                        "Website URL for DSA",
                        value=cfg.get('dsa_website_url', cfg.get('website_url', '')),
                        placeholder="https://example.com",
                        help="The website URL that Google will crawl for content"
                    )
                    cfg['dsa_website_url'] = dsa_website_url
                    
                    # DSA targeting
                    dsa_targeting = st.selectbox(
                        "DSA Targeting Method",
                        ["All webpages", "Specific pages", "Categories"],
                        index=0,
                        help="Choose how to target your dynamic ads"
                    )
                    cfg['dsa_targeting'] = dsa_targeting
                    
                    if dsa_targeting == "Specific pages":
                        dsa_pages = st.text_area(
                            "Page URLs to target",
                            placeholder="https://example.com/products\nhttps://example.com/services",
                            help="Enter one URL per line"
                        )
                        cfg['dsa_target_pages'] = [url.strip() for url in dsa_pages.split('\n') if url.strip()]
                    
                    elif dsa_targeting == "Categories":
                        dsa_categories = st.multiselect(
                            "Content categories",
                            ["Products", "Services", "Blog Posts", "Landing Pages", "Product Categories"],
                            default=cfg.get('dsa_categories', ["Products"])
                        )
                        cfg['dsa_categories'] = dsa_categories
            
            # EU political ads section
            with st.expander("**EU political ads**", expanded=False):
                st.write("Not specified")
                is_political = st.checkbox(
                    "This campaign contains EU political content",
                    value=cfg.get('is_political_ad', False),
                    help="Required for ads containing political content in the European Union"
                )
                cfg['is_political_ad'] = is_political
                
                if is_political:
                    cfg['political_ad_paying_entity'] = st.text_input(
                        "Paying entity for this political ad",
                        placeholder="Organization or individual paying for the ad"
                    )
        
        # Audience segments section
        with st.container():
            st.markdown("---")
            with st.expander("**Audience segments**", expanded=True):
                st.write("Select audience segments to add to your campaign. You can create new Your data segments by clicking on + New segment in the Search tab.")
                
                # Audience tabs
                tab1, tab2 = st.tabs(["Search", "Browse"])
                
                with tab1:
                    # Search for audiences
                    audience_search = st.text_input(
                        "🔍 Search audiences",
                        placeholder='Try "consumer electronics"',
                        label_visibility="collapsed"
                    )
                    
                    # Predefined audience categories
                    audiences = {
                        "Affinity": [
                            "Technology > Technophiles",
                            "Home Automation Enthusiasts"
                        ],
                        "In-market": [
                            "Computers & Peripherals",
                            "Consumer Electronics"
                        ],
                        "Demographics": [
                            "Age: 25-34",
                            "Age: 35-44",
                            "Gender: Male",
                            "Gender: Female",
                            "Parental Status: Parent",
                            "Household Income: Top 10%"
                        ],
                        "Your data": [
                            "All visitors (Remarketing)",
                            "Cart abandoners",
                            "Past purchasers",
                            "Newsletter subscribers"
                        ]
                    }
                    
                    selected_audiences = cfg.get('audience_segments', [])
                    
                    for category, items in audiences.items():
                        st.write(f"**{category}**")
                        for item in items:
                            if st.checkbox(item, value=item in selected_audiences, key=f"aud_{item}"):
                                if item not in selected_audiences:
                                    selected_audiences.append(item)
                            elif item in selected_audiences:
                                selected_audiences.remove(item)
                    
                    cfg['audience_segments'] = selected_audiences
                
                with tab2:
                    st.write("Browse audience categories to discover new segments")
                    browse_category = st.selectbox(
                        "Category",
                        ["Affinity", "In-market", "Life events", "Detailed demographics", "Your data"]
                    )
                    st.info(f"Browse {browse_category} audiences here")
                
                # Targeting setting
                st.markdown("---")
                st.write("**Targeting setting for this campaign** ℹ️")
                
                targeting_setting = st.radio(
                    "Choose targeting approach",
                    ["Targeting: Narrow the reach of your campaign to the selected segments, with the option to adjust the bids",
                     "Observation (recommended): Don't narrow the reach of your campaign; with the option to adjust the bids on the selected segments"],
                    index=1,
                    label_visibility="collapsed"
                )
                cfg['audience_targeting_setting'] = "targeting" if "Targeting:" in targeting_setting else "observation"
                
                if selected_audiences:
                    st.success(f"✅ {len(selected_audiences)} audience segments selected")
                    if st.button("Clear all"):
                        cfg['audience_segments'] = []
                        st.rerun()
        
        # More settings section
        st.markdown("---")
        with st.expander("🔧 **More settings**", expanded=False):
            # Ad rotation
            st.subheader("Ad rotation")
            ad_rotation = st.selectbox(
                "Optimize",
                ["Optimize: Prefer best performing ads", 
                 "Do not optimize: Rotate ads evenly"],
                index=0,
                help="How Google serves your ads"
            )
            cfg['ad_rotation'] = "optimize" if "Optimize:" in ad_rotation else "rotate_evenly"
            
            # Start and end dates
            st.subheader("Start and end dates")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start date", value=date.today())
                cfg['start_date'] = start_date.isoformat()
            with col2:
                has_end_date = st.checkbox("Set an end date", value=cfg.get('has_end_date', False))
                if has_end_date:
                    end_date = st.date_input("End date", value=date.today() + timedelta(days=30))
                    cfg['end_date'] = end_date.isoformat()
                else:
                    st.write("End date: Not set")
                cfg['has_end_date'] = has_end_date
            
            # Ad schedule
            st.subheader("Ad schedule")
            use_schedule = st.checkbox("Set specific hours or days", value=cfg.get('use_ad_schedule', False))
            if use_schedule:
                cfg['use_ad_schedule'] = True
                schedule_type = st.selectbox(
                    "Schedule type",
                    ["All days", "Weekdays only", "Weekends only", "Custom"]
                )
                cfg['schedule_type'] = schedule_type
                
                if schedule_type == "Custom":
                    st.write("Select days and hours:")
                    days = st.multiselect(
                        "Days",
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    )
                    cfg['schedule_days'] = days
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        start_hour = st.selectbox("Start hour", list(range(24)), index=9)
                    with col2:
                        end_hour = st.selectbox("End hour", list(range(24)), index=17)
                    cfg['schedule_hours'] = {"start": start_hour, "end": end_hour}
            else:
                cfg['use_ad_schedule'] = False
                st.write("All day")
            
            # Campaign URL options
            st.subheader("Campaign URL options")
            use_tracking = st.checkbox("Use tracking template", value=cfg.get('use_tracking', False))
            if use_tracking:
                cfg['tracking_template'] = st.text_input(
                    "Tracking template",
                    placeholder="{lpurl}?utm_source=google&utm_medium=cpc&utm_campaign={campaignid}",
                    help="Add tracking parameters to your URLs"
                )
                
                # URL suffix
                cfg['url_suffix'] = st.text_input(
                    "Final URL suffix",
                    placeholder="utm_content={creative}&utm_term={keyword}",
                    help="Parameters to append to your final URLs"
                )
            else:
                st.write("No options set")
            
            # Page feeds
            st.subheader("Page feeds")
            use_page_feed = st.checkbox("Add page feeds to your campaign", value=cfg.get('use_page_feed', False))
            if use_page_feed:
                cfg['page_feed_url'] = st.text_input(
                    "Page feed URL",
                    placeholder="https://example.com/feeds/pages.csv",
                    help="URL to your page feed file"
                )
            
            # Dynamic Search Ads settings
            st.subheader("Dynamic Search Ads settings")
            use_dsa = st.checkbox("Enable Dynamic Search Ads", value=cfg.get('use_dsa', False))
            if use_dsa:
                cfg['use_dsa'] = True
                dsa_setting_type = st.selectbox(
                    "DSA targeting source",
                    ["Use Google's index of my website",
                     "Use page feeds only",
                     "Use both website and page feeds"]
                )
                cfg['dsa_setting_type'] = dsa_setting_type
                
                if "website" in dsa_setting_type.lower():
                    cfg['dsa_domain'] = st.text_input("Website domain", placeholder="example.com")
                    cfg['dsa_language'] = st.selectbox(
                        "Website language",
                        ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Japanese", "Chinese"]
                    )
            else:
                cfg['use_dsa'] = False
        
        nav_buttons(3, total_steps)
    
    # --- STEP 4: AI MAX ---
    elif st.session_state.campaign_step == 4:
        st.header("Step 4: AI Max")
        st.success("✅ AI Max enabled with Gemini API")
        st.write("Leverage AI to optimize your campaign performance with advanced machine learning")
        
        # AI Max configuration
        with st.container():
            st.subheader("🤖 AI Optimization Features")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Smart Bidding**")
                cfg['ai_smart_bidding'] = st.checkbox(
                    "Enable AI-powered smart bidding",
                    value=cfg.get('ai_smart_bidding', True),
                    help="Let AI optimize your bids for better performance"
                )
                
                cfg['ai_audience_targeting'] = st.checkbox(
                    "AI audience targeting",
                    value=cfg.get('ai_audience_targeting', True),
                    help="Use AI to find and target high-value audiences"
                )
                
                cfg['ai_ad_optimization'] = st.checkbox(
                    "AI ad optimization",
                    value=cfg.get('ai_ad_optimization', True),
                    help="Automatically optimize ad copy and creative elements"
                )
            
            with col2:
                st.markdown("**Advanced Features**")
                cfg['ai_keyword_expansion'] = st.checkbox(
                    "AI keyword expansion",
                    value=cfg.get('ai_keyword_expansion', True),
                    help="Automatically discover new relevant keywords"
                )
                
                cfg['ai_budget_optimization'] = st.checkbox(
                    "AI budget optimization",
                    value=cfg.get('ai_budget_optimization', True),
                    help="Dynamically adjust budget allocation across campaigns"
                )
                
                cfg['ai_performance_prediction'] = st.checkbox(
                    "AI performance prediction",
                    value=cfg.get('ai_performance_prediction', True),
                    help="Predict campaign performance and suggest improvements"
                )
            
            st.markdown("---")
            
            # Gemini API Integration
            st.subheader("🧠 Gemini API Integration")
            gemini_client = get_gemini_client()
            
            if gemini_client:
                st.success("✅ Gemini API connected successfully")
                
                # AI-powered campaign insights
                if st.button("Get AI Campaign Insights", use_container_width=True):
                    with st.spinner("Analyzing campaign with AI..."):
                        try:
                            # Generate AI insights using Gemini
                            insights = gemini_client.generate_campaign_insights(cfg)
                            st.success("AI analysis complete!")
                            
                            # Display insights
                            with st.expander("🤖 AI Campaign Insights", expanded=True):
                                st.write(insights)
                                
                        except Exception as e:
                            st.error(f"AI analysis failed: {e}")
            else:
                st.warning("⚠️ Gemini API not available. AI features will use mock data.")
        
        nav_buttons(4, total_steps)
    
    # --- STEP 5: KEYWORD AND ASSET GENERATION ---
    elif st.session_state.campaign_step == 5:
        st.header("Step 5: Keyword and asset generation")
        st.success("✅ Keywords and assets generated")
        st.write("Create compelling keywords and ad assets for your campaign")
        
        # Initialize ad_groups if not exists
        if 'ad_groups' not in cfg or not cfg['ad_groups']:
            cfg['ad_groups'] = [{"name": "Ad Group 1", "keywords": "", "headlines": [], "descriptions": []}]
        
        # Ad group management
        tab1, tab2, tab3 = st.tabs(["🎯 Keywords", "📝 Ads", "➕ Ad Groups"])
        
        with tab1:
            st.subheader("Keywords")
            
            # Keyword input method
            input_method = st.radio(
                "How would you like to add keywords?",
                ["Enter keywords manually", "Get keyword suggestions", "Upload keywords"]
            )
            
            if input_method == "Enter keywords manually":
                for i, ag in enumerate(cfg['ad_groups']):
                    with st.expander(f"Keywords for {ag['name']}", expanded=i==0):
                        keywords = st.text_area(
                            "Enter keywords (one per line, optionally with match type)",
                            value=ag.get('keywords', ''),
                            placeholder="running shoes, broad\n+nike running shoes, broad modifier\n[exact match shoes], exact\n\"phrase match shoes\", phrase",
                            height=150,
                            key=f"keywords_{i}"
                        )
                        cfg['ad_groups'][i]['keywords'] = keywords
                        
                        # Show keyword count
                        if keywords:
                            keyword_lines = [l for l in keywords.split('\n') if l.strip()]
                            st.info(f"📊 {len(keyword_lines)} keywords added")
            
            elif input_method == "Get keyword suggestions":
                st.info("💡 **AI Generation**: Uses Gemini AI to create diverse keyword variations based on your input\n\n🔍 **URL Extraction**: Analyzes website content to extract relevant keywords")
                
                seed_input = st.text_input(
                    "Enter seed keywords or website URL",
                    placeholder="e.g., 'running shoes' or 'https://example.com'"
                )
                suggestion_method = st.radio(
                    "Choose suggestion method:",
                    ["AI Generation", "URL Extraction"],
                    horizontal=True
                )
                
                if st.button("Get Suggestions"):
                    if not seed_input.strip():
                        st.warning("Please enter seed keywords or a website URL")
                    else:
                        with st.spinner("Getting keyword suggestions..."):
                            try:
                                if suggestion_method == "AI Generation":
                                    # Use Gemini AI for keyword generation
                                    gemini = get_gemini_client()
                                    keywords = gemini.generate_keywords(seed_input)
                                    
                                    # Format keywords with match types
                                    formatted_keywords = []
                                    for i, kw in enumerate(keywords):
                                        if i < 5:
                                            formatted_keywords.append(f"{kw}, exact")
                                        elif i < 10:
                                            formatted_keywords.append(f"{kw}, phrase")
                                        else:
                                            formatted_keywords.append(f"{kw}, broad")
                                    
                                    keyword_text = '\n'.join(formatted_keywords)
                                    
                                else:  # URL Extraction
                                    # Use KeywordExtractor for URL-based extraction
                                    from features.keyword_extractor import KeywordExtractor
                                    extractor = KeywordExtractor()
                                    
                                    if seed_input.startswith(('http://', 'https://')):
                                        # URL extraction
                                        keywords_dict = extractor.extract_from_url(seed_input)
                                        keyword_text = extractor.format_for_campaign(keywords_dict)
                                    else:
                                        # Generate variations from seed keywords
                                        keywords_dict = extractor.generate_variations(seed_input)
                                        keyword_text = extractor.format_for_campaign(keywords_dict)
                                
                                # Display the generated keywords
                                st.success(f"✅ Generated {len(keyword_text.split(chr(10)))} keyword suggestions!")
                                
                                # Show keywords in a text area for editing
                                for i, ag in enumerate(cfg['ad_groups']):
                                    with st.expander(f"Keywords for {ag['name']}", expanded=i==0):
                                        edited_keywords = st.text_area(
                                            "Generated keywords (edit as needed):",
                                            value=keyword_text,
                                            height=200,
                                            key=f"generated_keywords_{i}"
                                        )
                                        cfg['ad_groups'][i]['keywords'] = edited_keywords
                                        
                                        # Show keyword count
                                        if edited_keywords:
                                            keyword_lines = [l for l in edited_keywords.split('\n') if l.strip()]
                                            st.info(f"📊 {len(keyword_lines)} keywords added")
                                
                            except Exception as e:
                                st.error(f"Error generating keyword suggestions: {e}")
                                st.info("Please try again or use manual keyword entry instead.")
        
        with tab2:
            st.subheader("Ad Creative")
            
            for i, ag in enumerate(cfg['ad_groups']):
                with st.expander(f"Ads for {ag['name']}", expanded=i==0):
                    # Headlines
                    st.write("**Headlines** (3-15 headlines, max 30 characters each)")
                    headlines = []
                    for j in range(3):
                        headline = st.text_input(
                            f"Headline {j+1}",
                            max_chars=30,
                            value=ag.get('headlines', [''])[j] if j < len(ag.get('headlines', [])) else '',
                            key=f"headline_{i}_{j}"
                        )
                        if headline:
                            headlines.append(headline)
                    cfg['ad_groups'][i]['headlines'] = headlines
                    
                    # Descriptions
                    st.write("**Descriptions** (2-4 descriptions, max 90 characters each)")
                    descriptions = []
                    for j in range(2):
                        desc = st.text_input(
                            f"Description {j+1}",
                            max_chars=90,
                            value=ag.get('descriptions', [''])[j] if j < len(ag.get('descriptions', [])) else '',
                            key=f"desc_{i}_{j}"
                        )
                        if desc:
                            descriptions.append(desc)
                    cfg['ad_groups'][i]['descriptions'] = descriptions
                    
                    # Ad Strength Indicator
                    if headlines and descriptions:
                        ad_strength = calculate_ad_strength(headlines, descriptions)
                        strength_color = {"Excellent": "🟢", "Good": "🟡", "Average": "🟠", "Poor": "🔴"}.get(ad_strength, "⚪")
                        st.write(f"**Ad Strength:** {strength_color} {ad_strength}")
                        
                        # Ad Strength recommendations
                        if ad_strength != "Excellent":
                            with st.expander("💡 Improve Ad Strength", expanded=False):
                                recommendations = get_ad_strength_recommendations(headlines, descriptions, ad_strength)
                                for rec in recommendations:
                                    st.write(f"• {rec}")
                    
                    # Final URL and Path Fields
                    st.write("**Final URL**")
                    final_url = st.text_input(
                        "Final URL",
                        value=ag.get('final_url', cfg.get('website_url', '')),
                        placeholder="https://example.com",
                        key=f"final_url_{i}"
                    )
                    cfg['ad_groups'][i]['final_url'] = final_url
                    
                    # Path fields
                    col1, col2 = st.columns(2)
                    with col1:
                        path1 = st.text_input(
                            "Path 1 (optional)",
                            value=ag.get('path1', ''),
                            max_chars=15,
                            placeholder="shop",
                            key=f"path1_{i}"
                        )
                        cfg['ad_groups'][i]['path1'] = path1
                    with col2:
                        path2 = st.text_input(
                            "Path 2 (optional)",
                            value=ag.get('path2', ''),
                            max_chars=15,
                            placeholder="deals",
                            key=f"path2_{i}"
                        )
                        cfg['ad_groups'][i]['path2'] = path2
                    
                    # Ad preview
                    if headlines and descriptions:
                        st.write("**Ad Preview:**")
                        display_url = final_url.replace('https://', '').replace('http://', '') if final_url else 'example.com'
                        if path1:
                            display_url += f"/{path1}"
                        if path2:
                            display_url += f"/{path2}"
                        
                        st.info(f"🔷 {headlines[0]}\n📍 {display_url}\n{descriptions[0]}")
        
        with tab3:
            st.subheader("Manage Ad Groups")
            
            # List current ad groups
            for i, ag in enumerate(cfg['ad_groups']):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    new_name = st.text_input(f"Ad Group {i+1} Name", value=ag['name'], key=f"ag_name_{i}")
                    cfg['ad_groups'][i]['name'] = new_name
                with col2:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    if st.button(f"📋 Copy", key=f"copy_{i}"):
                        new_ag = ag.copy()
                        new_ag['name'] = f"{ag['name']} - Copy"
                        cfg['ad_groups'].append(new_ag)
                        st.rerun()
                with col3:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    if len(cfg['ad_groups']) > 1:
                        if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                            cfg['ad_groups'].pop(i)
                            st.rerun()
            
            # Add new ad group button
            if st.button("➕ Add Ad Group", use_container_width=True):
                cfg['ad_groups'].append({
                    "name": f"Ad Group {len(cfg['ad_groups']) + 1}",
                    "keywords": "",
                    "headlines": [],
                    "descriptions": []
                })
                st.rerun()
        
        nav_buttons(4, total_steps)
    
    # --- STEP 5: BUDGET ---
    elif st.session_state.campaign_step == 7:
        st.header("Step 7: Budget")
        st.info("⭕ Budget configuration pending")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Campaign Budget")
            
            # Campaign name
            cfg['campaign_name'] = st.text_input(
                "Campaign Name",
                value=cfg.get('campaign_name', f"{cfg.get('objective', 'Campaign')} {date.today().strftime('%Y-%m-%d')}")
            )
            
            # Budget type
            budget_type = st.radio(
                "Budget Type",
                ["Daily budget", "Campaign total", "Shared budget"],
                index=0 if cfg.get('budget_type', 'daily') == 'daily' else 1
            )
            cfg['budget_type'] = 'daily' if budget_type == "Daily budget" else ('total' if budget_type == "Campaign total" else 'shared')
            
            # Budget amount
            if cfg['budget_type'] == 'daily':
                cfg['daily_budget'] = st.number_input(
                    "Daily Budget ($)",
                    min_value=1.0,
                    max_value=10000.0,
                    value=cfg.get('daily_budget', 100.0),
                    step=10.0
                )
                st.info(f"💡 Estimated monthly spend: ${cfg['daily_budget'] * 30.4:.2f}")
            else:
                cfg['total_budget'] = st.number_input(
                    "Campaign Total Budget ($)",
                    min_value=30.0,
                    max_value=1000000.0,
                    value=cfg.get('total_budget', 3000.0),
                    step=100.0
                )
                if cfg.get('has_end_date') and cfg.get('end_date'):
                    days = (date.fromisoformat(cfg['end_date']) - date.fromisoformat(cfg['start_date'])).days
                    st.info(f"💡 Average daily spend: ${cfg['total_budget'] / days:.2f}")
        
        with col2:
            st.subheader("Delivery Method")
            
            delivery_method = st.radio(
                "Ad Delivery",
                ["Standard (spread throughout the day)", "Accelerated (spend quickly)"],
                index=0 if cfg.get('delivery_method', 'standard') == 'standard' else 1,
                help="How quickly your ads are shown"
            )
            cfg['delivery_method'] = 'standard' if "Standard" in delivery_method else 'accelerated'
            
            if cfg['delivery_method'] == 'standard':
                st.info("✅ Recommended: Your ads will show evenly over time")
            else:
                st.warning("⚠️ Your budget may be spent early in the day")
            
            # Monthly spend cap
            st.subheader("Spend Limits")
            use_monthly_cap = st.checkbox(
                "Set monthly spend cap",
                value=cfg.get('monthly_budget_cap') is not None
            )
            
            if use_monthly_cap:
                if cfg['budget_type'] == 'daily':
                    min_monthly = cfg['daily_budget'] * 28
                    default_monthly = cfg['daily_budget'] * 30.4
                else:
                    min_monthly = cfg.get('total_budget', 3000.0)
                    default_monthly = min_monthly
                
                cfg['monthly_budget_cap'] = st.number_input(
                    "Monthly Budget Cap ($)",
                    min_value=min_monthly,
                    value=cfg.get('monthly_budget_cap', default_monthly),
                    step=100.0
                )
            else:
                cfg['monthly_budget_cap'] = None
        
        nav_buttons(5, total_steps)
    
    # --- STEP 6: AD GROUPS ---
    elif st.session_state.campaign_step == 6:
        st.header("Step 6: Ad groups")
        st.success("✅ Ad groups configured")
        st.write("Organize your keywords and ads into focused ad groups")
        
        # Ad group management
        with st.container():
            st.subheader("📝 Ad Group Management")
            
            # Add new ad group
            if st.button("➕ Add New Ad Group", use_container_width=True):
                if 'ad_groups' not in cfg:
                    cfg['ad_groups'] = []
                cfg['ad_groups'].append({
                    "name": f"Ad Group {len(cfg['ad_groups']) + 1}",
                    "keywords": "",
                    "headlines": [],
                    "descriptions": []
                })
                st.rerun()
            
            # Display existing ad groups
            if cfg.get('ad_groups'):
                for i, ag in enumerate(cfg['ad_groups']):
                    with st.expander(f"📁 {ag['name']}", expanded=i==0):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            ag['name'] = st.text_input(
                                "Ad Group Name",
                                value=ag['name'],
                                key=f"ag_name_{i}"
                            )
                            
                            # Keywords
                            st.write("**Keywords:**")
                            ag['keywords'] = st.text_area(
                                "Enter keywords (one per line)",
                                value=ag.get('keywords', ''),
                                placeholder="running shoes\nathletic footwear\nsports shoes",
                                height=100,
                                key=f"ag_keywords_{i}"
                            )
                            
                            # Ad copy
                            st.write("**Ad Headlines:**")
                            headlines = st.text_area(
                                "Enter headlines (one per line)",
                                value='\n'.join(ag.get('headlines', [])),
                                placeholder="Best Running Shoes\nQuality Athletic Footwear\nComfortable Sports Shoes",
                                height=80,
                                key=f"ag_headlines_{i}"
                            )
                            ag['headlines'] = [h.strip() for h in headlines.split('\n') if h.strip()]
                            
                            st.write("**Ad Descriptions:**")
                            descriptions = st.text_area(
                                "Enter descriptions (one per line)",
                                value='\n'.join(ag.get('descriptions', [])),
                                placeholder="Shop the latest collection of running shoes\nFree shipping on orders over $50\n30-day return policy",
                                height=80,
                                key=f"ag_descriptions_{i}"
                            )
                            ag['descriptions'] = [d.strip() for d in descriptions.split('\n') if d.strip()]
                        
                        with col2:
                            if st.button("🗑️ Delete", key=f"delete_ag_{i}"):
                                cfg['ad_groups'].pop(i)
                                st.rerun()
                            
                            # Show stats
                            keyword_count = len([k for k in ag.get('keywords', '').split('\n') if k.strip()])
                            st.metric("Keywords", keyword_count)
                            st.metric("Headlines", len(ag.get('headlines', [])))
                            st.metric("Descriptions", len(ag.get('descriptions', [])))
        
        nav_buttons(6, total_steps)
    
    # --- STEP 7: BUDGET ---
    elif st.session_state.campaign_step == 7:
        st.header("Step 7: Budget")
        st.info("⭕ Budget configuration pending")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Campaign Budget")
            
            # Campaign name
            cfg['campaign_name'] = st.text_input(
                "Campaign Name",
                value=cfg.get('campaign_name', f"{cfg.get('objective', 'Campaign')} {date.today().strftime('%Y-%m-%d')}")
            )
            
            # Budget type
            budget_type = st.radio(
                "Budget Type",
                ["Daily budget", "Campaign total", "Shared budget"],
                index=0 if cfg.get('budget_type', 'daily') == 'daily' else 1
            )
            cfg['budget_type'] = 'daily' if budget_type == "Daily budget" else ('total' if budget_type == "Campaign total" else 'shared')
            
            # Budget amount
            if cfg['budget_type'] == 'daily':
                cfg['daily_budget'] = st.number_input(
                    "Daily Budget ($)",
                    min_value=1.0,
                    max_value=10000.0,
                    value=cfg.get('daily_budget', 100.0),
                    step=10.0
                )
                st.info(f"💡 Estimated monthly spend: ${cfg['daily_budget'] * 30.4:.2f}")
            else:
                cfg['total_budget'] = st.number_input(
                    "Campaign Total Budget ($)",
                    min_value=30.0,
                    max_value=1000000.0,
                    value=cfg.get('total_budget', 3000.0),
                    step=100.0
                )
                if cfg.get('has_end_date') and cfg.get('end_date'):
                    days = (date.fromisoformat(cfg['end_date']) - date.fromisoformat(cfg['start_date'])).days
                    st.info(f"💡 Average daily spend: ${cfg['total_budget'] / days:.2f}")
        
        with col2:
            st.subheader("Delivery Method")
            
            delivery_method = st.radio(
                "Ad Delivery",
                ["Standard (spread throughout the day)", "Accelerated (spend quickly)"],
                index=0 if cfg.get('delivery_method', 'standard') == 'standard' else 1,
                help="How quickly your ads are shown"
            )
            cfg['delivery_method'] = 'standard' if "Standard" in delivery_method else 'accelerated'
            
            if cfg['delivery_method'] == 'standard':
                st.info("✅ Recommended: Your ads will show evenly over time")
            else:
                st.warning("⚠️ Your budget may be spent early in the day")
            
            # Monthly spend cap
            if st.checkbox("Set monthly spend cap", value=cfg.get('has_monthly_cap', False)):
                cfg['has_monthly_cap'] = True
                cfg['monthly_budget_cap'] = st.number_input(
                    "Monthly Spend Cap ($)",
                    min_value=30.0,
                    max_value=100000.0,
                    value=cfg.get('monthly_budget_cap', 3000.0),
                    step=100.0
                )
            else:
                cfg['has_monthly_cap'] = False
                cfg['monthly_budget_cap'] = None
        
        nav_buttons(7, total_steps)
    
    # --- STEP 8: REVIEW ---
    elif st.session_state.campaign_step == 8:
        st.header("Step 8: Review")
        st.info("⭕ Review and launch pending")
        
        # Summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Campaign Type", cfg.get('campaign_type', 'Search'))
            st.metric("Objective", cfg.get('objective', 'Not set'))
            st.metric("Budget", f"${cfg.get('daily_budget', 0):.2f}/day" if cfg.get('budget_type', 'daily') == 'daily' else f"${cfg.get('total_budget', 0):.2f} total")
        
        with col2:
            st.metric("Bidding Focus", cfg.get('bidding_focus', 'Conversions'))
            if cfg.get('set_target_cpa') and cfg.get('target_cpa'):
                st.metric("Target CPA", f"${cfg.get('target_cpa', 0):.2f}")
            st.metric("Locations", ", ".join(cfg.get('locations', ['Not set'])[:2]) + ("..." if len(cfg.get('locations', [])) > 2 else ""))
        
        with col3:
            st.metric("Ad Groups", len(cfg.get('ad_groups', [])))
            total_keywords = sum(len([l for l in ag.get('keywords', '').split('\n') if l.strip()]) for ag in cfg.get('ad_groups', []))
            st.metric("Total Keywords", total_keywords)
            st.metric("Languages", ", ".join(cfg.get('languages', ['English'])))
        
        st.markdown("---")
        
        # Detailed review
        with st.expander("📋 Campaign Details", expanded=True):
            st.write(f"**Campaign Name:** {cfg.get('campaign_name', 'Not set')}")
            st.write(f"**Start Date:** {cfg.get('start_date', date.today().isoformat())}")
            if cfg.get('has_end_date'):
                st.write(f"**End Date:** {cfg.get('end_date', 'Not set')}")
            
            st.write("\n**Networks:**")
            networks = ["Google Search"]
            if cfg.get('include_search_partners'):
                networks.append("Search Partners")
            if cfg.get('include_display'):
                networks.append("Display Network")
            for network in networks:
                st.write(f"  • {network}")
            
            st.write("\n**Reach Methods:**")
            for method in cfg.get('reach_methods', []):
                st.write(f"  • {method}")
        
        with st.expander("🎯 Ad Groups & Keywords"):
            for i, ag in enumerate(cfg.get('ad_groups', [])):
                st.write(f"\n**{ag['name']}**")
                keywords = [l for l in ag.get('keywords', '').split('\n') if l.strip()]
                st.write(f"  Keywords: {len(keywords)}")
                st.write(f"  Headlines: {len(ag.get('headlines', []))}")
                st.write(f"  Descriptions: {len(ag.get('descriptions', []))}")
        
        nav_buttons(6, total_steps)
    
    # --- STEP 7: LAUNCH ---
    elif st.session_state.campaign_step == 7:
        st.header("🚀 Launch Campaign")
        
        st.success("✅ Your campaign is ready to launch!")
        
        # Final summary
        st.write("### Campaign Summary")
        st.write(f"**Name:** {cfg.get('campaign_name')}")
        st.write(f"**Type:** {cfg.get('campaign_type')} campaign targeting {cfg.get('objective')}")
        st.write(f"**Budget:** ${cfg.get('daily_budget', 100):.2f} daily")
        st.write(f"**Expected Performance:** Based on your settings, we'll simulate campaign performance")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("🚀 Launch Campaign & Run Simulation", type="primary", use_container_width=True):
                with st.spinner("Launching campaign and running simulation..."):
                    # Build and run simulation
                    full_config = build_full_simulation_config(cfg)
                    results_df, pacing_hist = run_simulation(full_config)
                    
                    # Update session state
                    st.session_state.update({
                        'simulation_results': results_df,
                        'pacing_history': pacing_hist,
                        'campaign_config': cfg,
                        'campaign_step': 0,
                        'page_selection': "Dashboard"
                    })
                    
                    st.success("✅ Campaign launched successfully! Redirecting to dashboard...")
                    time.sleep(2)
                    st.rerun()
        
        with col2:
            if st.button("💾 Save as Draft", use_container_width=True):
                st.session_state['draft_campaigns'] = st.session_state.get('draft_campaigns', [])
                st.session_state['draft_campaigns'].append(cfg.copy())
                st.success("Campaign saved as draft!")
        
        with col3:
            if st.button("Cancel", use_container_width=True):
                st.session_state.campaign_step = 0
                st.rerun()