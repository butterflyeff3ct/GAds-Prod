# /app/campaign_wizard.py
import streamlit as st
from datetime import date, timedelta
import time
from app.state import OBJECTIVES_ENHANCED, GEO_LOCATIONS, AUDIENCE_SEGMENTS
from data_models.schemas import BiddingStrategy
from features.keyword_extractor import KeywordExtractor, ADVANCED_KEYWORDS
from services.gemini_client import get_gemini_client
from core.simulation import run_simulation

# NEW: Import functional components
from app.components.keyword_manager import render_keyword_manager, render_campaign_negative_keywords
from app.components.schedule_manager import render_ad_schedule_manager, render_device_bid_adjustments
from app.components.extensions_manager import render_extensions_manager
from app.components.location_manager import (
    render_location_targeting,
    render_impression_share_bidding_setup
)
from app.components.audience_manager import render_audience_targeting
from app.components.conversion_manager import render_conversion_actions

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
                # Handle comma-separated format: "keyword, match_type, bid, status"
                if ',' in line:
                    parts = line.split(',')
                    keyword_text = parts[0].strip()
                    match_type = parts[1].strip() if len(parts) > 1 else "broad"
                    bid = parts[2].strip() if len(parts) > 2 else None
                    status = parts[3].strip() if len(parts) > 3 else "enabled"
                    
                    # Validate match_type
                    if match_type not in ['exact', 'phrase', 'broad']:
                        match_type = "broad"
                    
                    # Parse bid if provided
                    cpc_bid = None
                    if bid and bid.strip():
                        try:
                            cpc_bid = float(bid)
                        except ValueError:
                            cpc_bid = None
                else:
                    keyword_text = line.strip()
                    match_type = "broad"
                    cpc_bid = None
                    status = "enabled"
                
                keywords_list.append({
                    "id": f"kw_{ag_id}_{j}", 
                    "ad_group_id": ag_id, 
                    "text": keyword_text, 
                    "match_type": match_type,
                    "cpc_bid": cpc_bid,
                    "status": status
                })
        # Ensure headlines and descriptions are not empty
        headlines = ag.get("headlines", [])
        descriptions = ag.get("descriptions", [])
        
        if not headlines:
            headlines = ["Default Headline"]
        if not descriptions:
            descriptions = ["Default Description"]
            
        ads_list.append({
            "id": f"ad_{ag_id}", 
            "ad_group_id": ag_id, 
            "headlines": headlines, 
            "descriptions": descriptions, 
            "final_url": ag.get("final_url", cfg.get('website_url', "http://example.com"))
        })
    
    # Handle different budget types
    budget_type = cfg.get("budget_type", "daily")
    if budget_type == "daily":
        daily_budget = cfg.get("daily_budget", 100.0)
    elif budget_type == "total":
        total_budget = cfg.get("total_budget", 3000.0)
        # Convert total budget to daily budget (assuming 30 days)
        daily_budget = total_budget / 30.0
    elif budget_type == "shared":
        shared_budget = cfg.get("shared_daily_budget", 500.0)
        daily_budget = shared_budget / 10.0  # Assume 10 campaigns sharing
    else:
        daily_budget = cfg.get("daily_budget", 100.0)
    
    return {
        "campaign": {"id": campaign_id, "name": cfg.get("campaign_name", "Campaign"), "daily_budget": daily_budget},
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
    total_steps = 9  # Search, Bidding, Campaign settings, AI Max, Keyword generation, Ad groups, Budget, Review, Launch
    
    # Show progress bar (ensure value doesn't exceed 1.0)
    progress_value = min(st.session_state.campaign_step / total_steps, 1.0)
    st.progress(progress_value, text=f"Step {st.session_state.campaign_step} of {total_steps}")
    
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
                st.markdown("[Learn more about customer acquisition](https://support.google.com/google-ads/answer/12080169)")
        
        st.markdown("---")
        
        # Conversion Actions section
        with st.container():
            st.subheader("Conversion Actions")
            st.write("Set up conversion tracking to measure the success of your campaign and optimize your bidding.")
            
            render_conversion_actions(cfg)
        
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
            
            # Locations section - Use new component
            with st.expander("**Location Targeting**", expanded=True):
                render_location_targeting(cfg)
            
            # Impression Share Bidding Setup
            with st.expander("**Impression Share Bidding**", expanded=False):
                st.write("Configure Target Impression Share bidding strategy for better visibility.")
                render_impression_share_bidding_setup(cfg)
            
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
            
            # Campaign-level negative keywords section
            with st.expander("**Negative Keywords (Campaign Level)**", expanded=False):
                st.write("Add negative keywords to prevent your ads from showing for irrelevant searches across all ad groups in this campaign.")
                
                render_campaign_negative_keywords(cfg)
            
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
        
        # Audience segments section - Use new component
        with st.container():
            st.markdown("---")
            with st.expander("**Audience Targeting**", expanded=True):
                render_audience_targeting(cfg)
        
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
            
            # Ad schedule - Use new component
            st.subheader("Ad Schedule & Device Targeting")
            render_ad_schedule_manager(cfg)
            
            # Device bid adjustments
            st.markdown("---")
            st.subheader("Device Bid Adjustments")
            render_device_bid_adjustments(cfg)
            
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
        
        # Get help creating your ad section
        with st.container():
            st.subheader("Get help creating your ad")
            st.write("Google AI uses your URL and description to create assets like keywords, headlines, and descriptions for you to review. Generated content might be inaccurate or offensive. Please review all content before publishing. Human reviewers may read and process the information you provide.")
            
            # Terms and Privacy links
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("[Terms of Service](https://policies.google.com/terms)")
            with col2:
                st.markdown("[Generative AI Additional Terms](https://policies.google.com/terms/generative-ai)")
            with col3:
                st.markdown("[Privacy Policy](https://policies.google.com/privacy)")
        
        st.markdown("---")
        
        # Final URL section
        st.subheader("What is the URL of the products or service you want to advertise?")
        final_url = st.text_input(
            "Final URL (required)*",
            value=cfg.get('final_url', ''),
            placeholder="https://example.com",
            help="🌐 Keyword and asset generation is not available in all languages."
        )
        cfg['final_url'] = final_url
        
        st.markdown("---")
        
        # Product description section
        st.subheader("What makes your products or services unique?")
        product_description = st.text_area(
            "Describe the product or service to advertise (required)*",
            value=cfg.get('product_description', ''),
            placeholder="Describe your products or services in detail. Include key features, benefits, and what makes them unique. This helps AI generate relevant keywords and ad copy.",
            height=150,
            help="The more detailed your description, the better the AI can generate relevant keywords and ad copy."
        )
        cfg['product_description'] = product_description
        
        st.markdown("---")
        
        # Review ad groups section
        st.subheader("Review ad groups")
        st.write("Google AI suggests ad groups relevant to keywords. You can edit these in the next step.")
        st.markdown("[Organize your account with ad groups](https://support.google.com/google-ads/answer/2375430)")
        
        # AI Generated Ad Groups
        if final_url and product_description and st.button("🚀 Generate", use_container_width=True, type="primary", key="generate_ad_groups"):
            with st.spinner("AI is generating keywords and ad groups..."):
                try:
                    # Use Gemini AI to generate ad groups
                    gemini = get_gemini_client()
                    
                    # Generate keywords first
                    keywords = gemini.generate_keywords(product_description)
                    
                    # Generate ad groups based on keywords and description
                    ad_groups_prompt = f"""
                    Based on the product description: "{product_description}"
                    And the base URL: "{final_url}"
                    
                    Create 3-5 relevant ad groups with:
                    1. Descriptive ad group names
                    2. Relevant final URLs (can be variations of the base URL)
                    3. 5-8 keywords per ad group
                    
                    Format as JSON:
                    {{
                        "ad_groups": [
                            {{
                                "name": "Ad Group Name",
                                "final_url": "https://example.com/category",
                                "keywords": ["keyword1", "keyword2", "keyword3"]
                            }}
                        ]
                    }}
                    """
                    
                    if gemini.use_real_api:
                        response = gemini.model.generate_content(ad_groups_prompt)
                        try:
                            import json
                            ad_groups_data = json.loads(response.text)
                            generated_ad_groups = ad_groups_data.get('ad_groups', [])
                        except:
                            # Fallback if JSON parsing fails
                            generated_ad_groups = [
                                {"name": "Main Products", "final_url": final_url, "keywords": keywords[:8]},
                                {"name": "Services", "final_url": f"{final_url}/services", "keywords": keywords[8:16] if len(keywords) > 8 else keywords[:8]},
                                {"name": "Support", "final_url": f"{final_url}/support", "keywords": keywords[16:24] if len(keywords) > 16 else keywords[:8]}
                            ]
                    else:
                        # Mock data for development
                        generated_ad_groups = [
                            {"name": "Main Products", "final_url": final_url, "keywords": keywords[:8]},
                            {"name": "Services", "final_url": f"{final_url}/services", "keywords": keywords[8:16] if len(keywords) > 8 else keywords[:8]},
                            {"name": "Support", "final_url": f"{final_url}/support", "keywords": keywords[16:24] if len(keywords) > 16 else keywords[:8]}
                        ]
                    
                    # Store generated ad groups
                    cfg['generated_ad_groups'] = generated_ad_groups
                    st.success(f"✅ Generated {len(generated_ad_groups)} ad groups with keywords!")
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower():
                        st.error("⚠️ API quota exceeded. Please wait a moment and try again, or use the manual keyword entry option.")
                        st.info("💡 **Tip:** The free tier has rate limits. You can still create campaigns manually or try again in a few minutes.")
                    else:
                        st.error(f"Error generating ad groups: {e}")
                    
                    # Fallback to simple ad groups
                    cfg['generated_ad_groups'] = [
                        {"name": "Main Products", "final_url": final_url, "keywords": ["product", "service", "buy", "shop"]},
                        {"name": "Services", "final_url": f"{final_url}/services", "keywords": ["services", "support", "help", "contact"]}
                    ]
        
        # Display generated ad groups
        if cfg.get('generated_ad_groups'):
            st.write("**Generated Ad Groups:**")
            for i, ag in enumerate(cfg['generated_ad_groups']):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{ag['name']}**")
                    st.write(f"Final URL: {ag['final_url']}")
                with col2:
                    if st.button("✏️", key=f"edit_generated_{i}", help="Edit ad group"):
                        st.session_state[f"editing_generated_{i}"] = True
                with col3:
                    if st.button("🗑️", key=f"delete_generated_{i}", help="Delete ad group"):
                        cfg['generated_ad_groups'].pop(i)
                        st.rerun()
            
            # Add ad group button
            if st.button("+ Add an ad group", use_container_width=True):
                new_ag = {
                    "name": f"Custom Ad Group {len(cfg['generated_ad_groups']) + 1}",
                    "final_url": final_url,
                    "keywords": ["custom", "keyword"]
                }
                cfg['generated_ad_groups'].append(new_ag)
                st.rerun()
        
        # Disclaimer
        st.markdown("---")
        st.info("⚠️ **Disclaimer:** By adding generated assets, you're confirming that you'll review the suggested keywords and assets on the next page and ensure that they're accurate, not misleading, and not in violation of any Google advertising policies or applicable laws before publishing them.")
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Skip", use_container_width=True, key="keyword_step_skip"):
                st.session_state.campaign_step += 1
                st.rerun()
        with col2:
            if st.button("Next ➡️", use_container_width=True, type="primary", key="keyword_step_next"):
                # Convert generated ad groups to regular ad groups
                if cfg.get('generated_ad_groups'):
                    cfg['ad_groups'] = []
                    for ag in cfg['generated_ad_groups']:
                        keyword_text = '\n'.join([f"{kw}, broad" for kw in ag['keywords']])
                        cfg['ad_groups'].append({
                            "name": ag['name'],
                            "keywords": keyword_text,
                            "final_url": ag['final_url'],
                            "headlines": [],
                            "descriptions": [],
                            "path1": "",
                            "path2": ""
                        })
                st.session_state.campaign_step += 1
                st.rerun()
        
        # Note: nav_buttons removed to avoid duplicate button IDs

    
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
        
        nav_buttons(7, total_steps)
    
        # --- STEP 6: AD GROUPS ---
    elif st.session_state.campaign_step == 6:
        st.header("Step 6: Ad groups")
        
        # Initialize ad_groups if not exists
        if 'ad_groups' not in cfg or not cfg['ad_groups']:
            cfg['ad_groups'] = [{"name": "Ad Group 1", "keywords": "", "headlines": [], "descriptions": [], "final_url": "", "path1": "", "path2": ""}]
        
        # Ad group selector
        ad_group_names = [ag['name'] for ag in cfg.get('ad_groups', [])]
        if not ad_group_names:
            ad_group_names = ["Ad Group 1"]
        
        selected_ag_index = st.session_state.get('selected_ad_group_index', 0)
        if selected_ag_index >= len(ad_group_names):
            selected_ag_index = 0
            st.session_state.selected_ad_group_index = 0
        
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_ag_name = st.selectbox(
                "Select Ad Group",
                options=ad_group_names,
                index=selected_ag_index,
                key="ad_group_selector"
            )
            st.session_state.selected_ad_group_index = ad_group_names.index(selected_ag_name)
        
        with col2:
            if st.button("+ Add Ad Group", key="add_new_ad_group"):
                new_name = f"Ad Group {len(cfg['ad_groups']) + 1}"
                cfg['ad_groups'].append({
                    "name": new_name,
                    "keywords": "",
                    "headlines": [],
                    "descriptions": [],
                    "final_url": "",
                    "path1": "",
                    "path2": ""
                })
                st.rerun()
        
        # Get selected ad group
        selected_ag = cfg['ad_groups'][st.session_state.selected_ad_group_index]
        
        # Ad group name editing
        st.write("**Ad Group Name:**")
        new_name = st.text_input(
            "Ad Group Name",
            value=selected_ag['name'],
            key=f"edit_ag_name_{st.session_state.selected_ad_group_index}"
        )
        if new_name != selected_ag['name']:
            selected_ag['name'] = new_name
        
        st.write("Ad groups help you organize your ads around a common theme. For the best results, focus your ads and keywords on one product or service.")
        
        # Main content area with tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Keywords", "AI Max", "Ads", "Extensions"])
        
        with tab1:
            st.subheader("Add details to match your ads to the right searches")
            
            # Use the new keyword manager component
            render_keyword_manager(
                ad_group_index=st.session_state.selected_ad_group_index,
                config=cfg
            )
            
            # Add negative keywords section for this ad group
            st.markdown("---")
            st.subheader("Negative Keywords (Ad Group Level)")
            st.write("Add negative keywords to prevent your ads from showing for irrelevant searches.")
            
            # Initialize ad group negative keywords if not exists
            if 'negative_keywords' not in selected_ag:
                selected_ag['negative_keywords'] = []
            
            negatives_text = st.text_area(
                "Ad Group Negative Keywords",
                value='\n'.join(selected_ag.get('negative_keywords', [])),
                placeholder='free\ncheap\n"competitor brand"\n[exact competitor name]',
                help='Prevents ads from showing for these searches in this ad group only',
                height=120,
                key=f"adgroup_negatives_{st.session_state.selected_ad_group_index}"
            )
            
            # Update the ad group's negative keywords
            selected_ag['negative_keywords'] = [n.strip() for n in negatives_text.split('\n') if n.strip()]
        
        with tab2:
            st.subheader("Ad group settings for AI Max")
            
            # AI Max settings
            with st.expander("Ad group settings for AI Max", expanded=True):
                st.write("**BETA** - Turn off for your ad group")
                
                # Info banner
                st.info("ℹ️ Turn on AI Max in your campaign to use these ad group level settings.")
                
                if st.button("Go to AI Max", key="goto_ai_max"):
                    st.session_state.campaign_step = 4  # Go to AI Max step
                    st.rerun()
                
                # AI Max settings sections
                settings = [
                    ("Search term matching", "Using only your keywords and match types.", "BETA"),
                    ("Brand inclusions", "Add brand lists.", ""),
                    ("Locations of interest", "Add locations of interest.", ""),
                    ("URL inclusions", "No URL inclusions.", "")
                ]
                
                for setting_name, description, beta_tag in settings:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{setting_name}** {beta_tag if beta_tag else ''}")
                        st.write(description)
                    with col2:
                        st.selectbox("Settings", ["▼"], key=f"ai_max_{setting_name.lower().replace(' ', '_')}")
        
        with tab3:
            st.subheader("Create ads to get more website traffic")
            
            # Ad creation interface
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                # Ad strength and suggestions
                st.write("**Ad Strength & Suggestions**")
                
                # Navigation arrows (placeholder)
                st.write("◀️ ▶️")
                
                # Ad strength meter (circular progress)
                headlines_count = len([h for h in selected_ag.get('headlines', []) if h.strip()])
                descriptions_count = len([d for d in selected_ag.get('descriptions', []) if d.strip()])
                
                # Calculate ad strength
                if headlines_count >= 10 and descriptions_count >= 3:
                    ad_strength = "Excellent"
                    strength_score = 90
                elif headlines_count >= 5 and descriptions_count >= 2:
                    ad_strength = "Good"
                    strength_score = 70
                elif headlines_count >= 3 and descriptions_count >= 1:
                    ad_strength = "Average"
                    strength_score = 50
                else:
                    ad_strength = "Poor"
                    strength_score = 30
                
                # Display ad strength
                st.metric("Ad Strength", ad_strength)
                st.progress(strength_score / 100, text=f"{strength_score}%")
                
                # Suggestions checklist
                suggestions = [
                    ("Add headlines", headlines_count >= 3, "Add at least 3 headlines"),
                    ("Include popular keywords", True, "Include relevant keywords"),
                    ("Make headlines unique", headlines_count >= 5, "Add more unique headlines"),
                    ("Make descriptions unique", descriptions_count >= 2, "Add more descriptions"),
                    ("Add more sitelinks", False, "Add sitelinks for better performance")
                ]
                
                for suggestion, completed, tooltip in suggestions:
                    status = "✅" if completed else "☐"
                    st.write(f"{status} {suggestion}")
                    if not completed:
                        st.markdown("[View ideas](#)")
            
            with col2:
                # Ad asset input fields
                st.write("**Ad Assets**")
                
                # Final URL
                final_url_ad = st.text_input(
                    "Final URL",
                    value=selected_ag.get('final_url', ''),
                    placeholder="https://example.com",
                    key=f"ad_final_url_{st.session_state.selected_ad_group_index}"
                )
                selected_ag['final_url'] = final_url_ad
                
                # Display path
                display_path = st.text_input(
                    "Display path",
                    value=f"{selected_ag.get('path1', '')}/{selected_ag.get('path2', '')}".strip('/'),
                    placeholder="shop/deals",
                    key=f"ad_display_path_{st.session_state.selected_ad_group_index}"
                )
                if display_path:
                    path_parts = display_path.split('/')
                    selected_ag['path1'] = path_parts[0] if len(path_parts) > 0 else ""
                    selected_ag['path2'] = path_parts[1] if len(path_parts) > 1 else ""
                
                # Calls
                st.text_input(
                    "Calls - Add a phone number",
                    placeholder="+1 (555) 123-4567",
                    key=f"ad_calls_{st.session_state.selected_ad_group_index}"
                )
                
                # Lead forms
                st.text_input(
                    "Lead forms - Add a form",
                    placeholder="Contact form",
                    key=f"ad_forms_{st.session_state.selected_ad_group_index}"
                )
                
                # Headlines
                st.write(f"**Headlines {headlines_count}/15**")
                headlines_text = st.text_area(
                    "Headlines",
                    value='\n'.join(selected_ag.get('headlines', [])),
                    placeholder="Enter headlines, one per line:\nBest Running Shoes 2024\nFree Shipping on All Orders\n30-Day Return Policy",
                    height=120,
                    key=f"ad_headlines_{st.session_state.selected_ad_group_index}"
                )
                selected_ag['headlines'] = [h.strip() for h in headlines_text.split('\n') if h.strip()]
                
                # Descriptions
                st.write(f"**Descriptions {descriptions_count}/4**")
                descriptions_text = st.text_area(
                    "Descriptions",
                    value='\n'.join(selected_ag.get('descriptions', [])),
                    placeholder="Enter descriptions, one per line:\nShop the latest collection of running shoes with free shipping.\nQuality athletic footwear for every sport and activity.",
                    height=100,
                    key=f"ad_descriptions_{st.session_state.selected_ad_group_index}"
                )
                selected_ag['descriptions'] = [d.strip() for d in descriptions_text.split('\n') if d.strip()]
                
                # Additional assets
                st.write("**More Assets**")
                st.text_input("Images - Add Images to your campaign", placeholder="Upload images", key=f"ad_images_{st.session_state.selected_ad_group_index}")
                st.text_input("Business name and logos", placeholder="Your business name", key=f"ad_business_{st.session_state.selected_ad_group_index}")
                st.text_input("Sitelinks", placeholder="Additional links", key=f"ad_sitelinks_{st.session_state.selected_ad_group_index}")
                
                # More asset types
                st.write("**More asset types (0/5)**")
                st.checkbox("Improve your ad performance and make your ad more interactive by adding more details about your business and website.", key=f"ad_more_assets_{st.session_state.selected_ad_group_index}")
                st.checkbox("Ad URL options", key=f"ad_url_options_{st.session_state.selected_ad_group_index}")
            
            with col3:
                # Ad preview
                st.write("**Preview**")
                st.markdown("[Share](#)")
                st.markdown("[Preview ads](#)")
                
                # Mobile preview
                st.write("📱 **Mobile Preview**")
                
                # Create a simple mobile preview
                if selected_ag.get('headlines') and selected_ag.get('descriptions'):
                    headline = selected_ag['headlines'][0][:30] if selected_ag['headlines'] else "Your Headline"
                    description = selected_ag['descriptions'][0][:70] if selected_ag['descriptions'] else "Your description text"
                    display_url = final_url_ad.replace('https://', '').replace('http://', '') if final_url_ad else "example.com"
                    
                    # Mobile preview box
                    st.markdown(f"""
                    <div style="border: 1px solid #ccc; border-radius: 10px; padding: 10px; width: 200px; background: white;">
                        <div style="font-size: 12px; color: #666;">Google</div>
                        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 5px; margin: 5px 0; background: #f5f5f5;">
                            <div style="font-size: 10px; color: #666;">🔍 Search</div>
                        </div>
                        <div style="color: #1a73e8; font-weight: bold; font-size: 14px;">{headline}</div>
                        <div style="color: #006621; font-size: 12px;">{display_url}</div>
                        <div style="color: #666; font-size: 12px; margin-top: 2px;">{description}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Preview navigation
                st.write("◀️ ▶️")
                st.write("●●●●●")  # Dots for multiple previews
        
        with tab4:
            st.subheader("Ad Extensions")
            st.write("Add extensions to make your ads more informative and increase click-through rates.")
            
            # Use the new extensions manager component
            render_extensions_manager(
                ad_group_index=st.session_state.selected_ad_group_index,
                config=cfg
            )
        
        # Bottom section
        st.markdown("---")
        st.write("Ad previews are examples. You're responsible for your ad content.")
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Back to all ad groups", key="back_to_all_adgroups"):
                # Could go back to a summary view
                pass
        with col2:
            if st.button("Save", type="primary", key="save_adgroup"):
                st.success("✅ Ad group saved successfully!")
        
        nav_buttons(6, total_steps)

    
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
    elif st.session_state.campaign_step == 9:
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
                    try:
                        # Show campaign configuration summary
                        st.info("📋 Campaign Configuration:")
                        st.write(f"• Campaign: {cfg.get('campaign_name', 'Unnamed')}")
                        st.write(f"• Budget: ${cfg.get('daily_budget', 100):.2f}/day")
                        st.write(f"• Ad Groups: {len(cfg.get('ad_groups', []))}")
                        total_keywords = sum(len([l for l in ag.get('keywords', '').split('\n') if l.strip()]) for ag in cfg.get('ad_groups', []))
                        st.write(f"• Total Keywords: {total_keywords}")
                        st.write(f"• Total Ads: {len(cfg.get('ad_groups', []))}")
                        
                        # Validate configuration
                        if total_keywords == 0:
                            st.error("❌ No keywords found in campaign. Please add keywords to your ad groups.")
                            return
                        
                        if len(cfg.get('ad_groups', [])) == 0:
                            st.error("❌ No ad groups found in campaign. Please add ad groups.")
                            return
                        
                        # Build and run simulation
                        full_config = build_full_simulation_config(cfg)
                        results_df = run_simulation(full_config)
                        
                        # Check simulation results
                        if results_df.empty:
                            st.error("❌ Simulation completed but returned no results. Check the debug information above.")
                            st.info("💡 Common causes: API quota exceeded, keyword/ad matching issues, or budget constraints.")
                            return
                        
                        # Update session state - avoid modifying widget-bound keys
                        st.session_state['simulation_results'] = results_df
                        st.session_state['pacing_history'] = []
                        st.session_state['campaign_config'] = cfg
                        st.session_state['campaign_step'] = 0
                        st.session_state['campaign_launched'] = True  # Use a flag instead
                        
                        st.success("✅ Campaign launched successfully! Redirecting to dashboard...")
                        st.balloons()  # Celebration!
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Campaign launch failed: {str(e)}")
                        st.exception(e)
                        st.info("💡 Please check your campaign configuration and try again.")
        
        with col2:
            if st.button("💾 Save as Draft", use_container_width=True):
                st.session_state['draft_campaigns'] = st.session_state.get('draft_campaigns', [])
                st.session_state['draft_campaigns'].append(cfg.copy())
                st.success("Campaign saved as draft!")
        
        with col3:
            if st.button("Cancel", use_container_width=True):
                st.session_state.campaign_step = 0
                st.rerun()