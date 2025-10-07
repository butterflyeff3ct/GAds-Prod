# /app/educational_components.py
"""
Educational components and tooltips for the Google Ads Simulator.
Shows formulas, explanations, and "how it works" information throughout the UI.
"""

import streamlit as st
import plotly.graph_objects as go

def show_formula(title: str, formula: str, explanation: str, example: str = None):
    """
    Display a formula with explanation in an expandable section.
    
    Args:
        title: Formula name (e.g., "Quality Score Calculation")
        formula: LaTeX or plain text formula
        explanation: What the formula does
        example: Optional worked example
    """
    with st.expander(f"📐 {title}", expanded=False):
        st.markdown(f"**Formula:**")
        st.code(formula, language="text")
        
        st.markdown(f"**Explanation:**")
        st.write(explanation)
        
        if example:
            st.markdown(f"**Example:**")
            st.info(example)

def show_metric_tooltip(metric_name: str):
    """Display tooltip/explanation for common Google Ads metrics."""
    
    tooltips = {
        "CTR": {
            "name": "Click-Through Rate",
            "formula": "CTR = (Clicks / Impressions) × 100%",
            "explanation": "Percentage of people who click your ad after seeing it. Higher CTR indicates more relevant ads.",
            "good_value": "2-5% is typical, 5%+ is excellent",
            "how_to_improve": [
                "Make headlines more compelling",
                "Include keywords in ad copy",
                "Use relevant ad extensions",
                "Match ad copy to user intent"
            ]
        },
        "CPC": {
            "name": "Cost Per Click",
            "formula": "CPC = Total Cost / Total Clicks",
            "explanation": "Average amount you pay each time someone clicks your ad.",
            "good_value": "Varies by industry ($0.50-$3.00 is common)",
            "how_to_improve": [
                "Improve Quality Score",
                "Use more specific keywords",
                "Adjust bids based on performance",
                "Use negative keywords"
            ]
        },
        "CVR": {
            "name": "Conversion Rate",
            "formula": "CVR = (Conversions / Clicks) × 100%",
            "explanation": "Percentage of clicks that result in a conversion. Measures landing page effectiveness.",
            "good_value": "2-5% is typical, 5%+ is excellent",
            "how_to_improve": [
                "Optimize landing page",
                "Clear call-to-action",
                "Match landing page to ad",
                "Reduce form friction"
            ]
        },
        "CPA": {
            "name": "Cost Per Acquisition",
            "formula": "CPA = Total Cost / Total Conversions",
            "explanation": "Average cost to acquire one conversion. Key metric for ROI.",
            "good_value": "Should be less than customer lifetime value",
            "how_to_improve": [
                "Improve conversion rate",
                "Lower CPC",
                "Better targeting",
                "Optimize landing pages"
            ]
        },
        "Quality Score": {
            "name": "Quality Score (1-10)",
            "formula": "QS = f(Expected CTR × 0.4, Ad Relevance × 0.35, Landing Page × 0.25)",
            "explanation": "Google's rating of your ad quality and relevance. Higher scores = lower CPCs.",
            "good_value": "7+ is good, 8+ is excellent",
            "how_to_improve": [
                "Improve ad relevance to keywords",
                "Increase expected CTR with better ad copy",
                "Optimize landing page experience",
                "Use tighter keyword groups"
            ]
        },
        "Ad Rank": {
            "name": "Ad Rank",
            "formula": "Ad Rank = Bid × Quality Score × Extensions",
            "explanation": "Determines your ad position. Combining bid and quality.",
            "good_value": "Higher Ad Rank = better positions",
            "how_to_improve": [
                "Increase bid",
                "Improve Quality Score",
                "Add ad extensions",
                "Improve ad relevance"
            ]
        },
        "ROAS": {
            "name": "Return on Ad Spend",
            "formula": "ROAS = Revenue / Cost",
            "explanation": "Revenue generated for every dollar spent. Key profitability metric.",
            "good_value": "4:1 or higher is typically profitable",
            "how_to_improve": [
                "Increase conversion value",
                "Improve conversion rate",
                "Lower CPA",
                "Better audience targeting"
            ]
        }
    }
    
    if metric_name in tooltips:
        info = tooltips[metric_name]
        
        st.markdown(f"### {info['name']}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Formula:**")
            st.code(info['formula'], language="text")
            
            st.markdown("**What it means:**")
            st.write(info['explanation'])
        
        with col2:
            st.markdown("**Benchmark:**")
            st.info(info['good_value'])
            
            st.markdown("**How to improve:**")
            for tip in info['how_to_improve']:
                st.write(f"• {tip}")

def show_auction_mechanics():
    """Interactive explanation of how the Google Ads auction works."""
    
    st.markdown("### 🎯 How the Google Ads Auction Works")
    
    st.write("""
    Every time someone searches on Google, an auction happens in milliseconds to determine:
    1. Which ads show
    2. In what order
    3. How much each advertiser pays
    """)
    
    # Example auction
    st.markdown("#### Example Auction")
    
    auction_data = {
        'Advertiser': ['You', 'Competitor A', 'Competitor B', 'Competitor C'],
        'Max Bid': [2.00, 2.50, 1.75, 3.00],
        'Quality Score': [8, 6, 7, 5],
        'Ad Rank': [16.0, 15.0, 12.25, 15.0],
        'Position': [1, 2, 4, 3],
        'Actual CPC': [1.88, 1.75, 0.0, 1.22]
    }
    
    df = st.dataframe(auction_data, use_container_width=True)
    
    st.markdown("""
    **Key Insights:**
    - You won Position 1 with a LOWER bid than Competitor C!
    - Your Quality Score (8) gave you an advantage
    - You paid less than your max bid ($1.88 vs $2.00)
    - This is why Quality Score matters!
    """)
    
    # CPC formula
    st.markdown("#### How CPC is Calculated (GSP Auction)")
    
    st.code("""
    Actual CPC = (Ad Rank of advertiser below you / Your Quality Score) + $0.01
    
    Your example:
    Actual CPC = (15.0 / 8) + 0.01 = $1.88
    """, language="text")
    
    show_formula(
        "Quality Score Components",
        """
        Quality Score = (Expected CTR × 0.40) + 
                       (Ad Relevance × 0.35) + 
                       (Landing Page Experience × 0.25)
        
        Final Score = 1 + (weighted_score × 9)
        Capped between 1 and 10
        """,
        """
        Quality Score combines three factors:
        1. **Expected CTR** (40%): Will people click your ad?
        2. **Ad Relevance** (35%): Does your ad match the search?
        3. **Landing Page** (25%): Is your landing page relevant and high-quality?
        
        Each component is rated: Above Average, Average, or Below Average
        """,
        """
        Example:
        - Expected CTR: 0.08 (Above Average) → normalized to 0.53
        - Ad Relevance: 0.75 (Above Average)
        - Landing Page: 0.65 (Average)
        
        Weighted Score = (0.53 × 0.40) + (0.75 × 0.35) + (0.65 × 0.25) = 0.63
        Quality Score = 1 + (0.63 × 9) = 6.7 → rounds to 7/10
        """
    )

def show_budget_pacing_explanation():
    """Explain how budget pacing works."""
    
    st.markdown("### 💰 How Budget Pacing Works")
    
    st.write("""
    Google Ads doesn't spend your budget all at once. Instead, it:
    1. Distributes budget throughout the day
    2. Adjusts bids to maintain pacing
    3. Prevents early exhaustion
    """)
    
    # Visual representation
    import plotly.graph_objects as go
    
    hours = list(range(24))
    standard_distribution = [
        0.02, 0.01, 0.01, 0.01, 0.02, 0.03,
        0.04, 0.05, 0.06, 0.07, 0.08, 0.08,
        0.07, 0.07, 0.06, 0.06, 0.07, 0.08,
        0.07, 0.06, 0.05, 0.04, 0.03, 0.02
    ]
    
    # Convert to cumulative
    cumulative = []
    total = 0
    for pct in standard_distribution:
        total += pct
        cumulative.append(total * 100)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hours,
        y=cumulative,
        mode='lines',
        name='Standard Pacing',
        line=dict(color='#4285F4', width=3)
    ))
    
    # Add even pacing for comparison
    even_cumulative = [(i+1)/24 * 100 for i in range(24)]
    fig.add_trace(go.Scatter(
        x=hours,
        y=even_cumulative,
        mode='lines',
        name='Even Pacing',
        line=dict(color='#EA4335', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='Budget Distribution Throughout the Day',
        xaxis_title='Hour of Day',
        yaxis_title='Cumulative Budget Spent (%)',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    **Standard Pacing Strategy:**
    - Higher budget allocation during business hours (9am-5pm)
    - Lower during night hours (12am-6am)
    - Follows typical search volume patterns
    - Prevents wasteful spending during low-traffic hours
    
    **Bid Throttling:**
    When spending too fast → Lower bids
    When spending too slow → Raise bids
    
    Formula: `Throttle Factor = f(spend_rate, hours_remaining, budget_remaining)`
    """)

def show_match_type_comparison():
    """Visual comparison of keyword match types."""
    
    st.markdown("### 🎯 Keyword Match Types Explained")
    
    match_types_data = {
        'Match Type': ['Exact', 'Phrase', 'Broad'],
        'Syntax': ['[keyword]', '"keyword"', 'keyword'],
        'Reach': ['Lowest', 'Medium', 'Highest'],
        'Relevance': ['Highest', 'Medium', 'Variable'],
        'Example Keyword': ['[running shoes]', '"running shoes"', 'running shoes'],
        'Matches Query': [
            'running shoes (exact only)',
            'best running shoes, running shoes sale',
            'shoes for running, athletic footwear, sneakers'
        ]
    }
    
    st.table(match_types_data)
    
    st.markdown("""
    **Which to use?**
    
    **Exact Match** `[keyword]`
    - ✅ Most control, highest relevance
    - ✅ Best Quality Scores
    - ❌ Limited reach
    - 💡 Use for: High-value, proven keywords
    
    **Phrase Match** `"keyword"`
    - ✅ Balance of reach and relevance
    - ✅ Keyword must appear as phrase
    - ❌ Some irrelevant queries
    - 💡 Use for: Core keyword themes
    
    **Broad Match** `keyword`
    - ✅ Maximum reach
    - ✅ Discover new keywords
    - ❌ Can waste budget on irrelevant queries
    - ❌ Requires careful negative keyword management
    - 💡 Use for: Discovery, with negative keywords
    """)

def show_attribution_comparison():
    """Compare different attribution models."""
    
    st.markdown("### 📊 Attribution Models Comparison")
    
    st.write("""
    **The Scenario:** A user sees your ad 4 times before converting for $100:
    1. Day 1: Display Ad (9am)
    2. Day 3: Search Ad (2pm)
    3. Day 5: Email (10am)
    4. Day 5: Search Ad (3pm) → Conversion!
    """)
    
    attribution_data = {
        'Model': ['Last Click', 'First Click', 'Linear', 'Time Decay', 'Position-Based', 'Data-Driven'],
        'Display (Day 1)': ['$0', '$100', '$25', '$10', '$40', '$15'],
        'Search (Day 3)': ['$0', '$0', '$25', '$20', '$10', '$25'],
        'Email (Day 5)': ['$0', '$0', '$25', '$30', '$10', '$20'],
        'Search (Day 5)': ['$100', '$0', '$25', '$40', '$40', '$40']
    }
    
    st.table(attribution_data)
    
    st.markdown("""
    **Which model should you use?**
    
    - **Last Click**: Simple, focuses on final driver
    - **First Click**: Values awareness
    - **Linear**: Fair, but may overvalue weak touchpoints
    - **Time Decay**: Rewards recency
    - **Position-Based**: Values both awareness and conversion
    - **Data-Driven**: Most accurate, needs lots of data
    """)

def show_glossary_term(term: str):
    """Show definition and explanation for Google Ads terms."""
    
    glossary = {
        "Impression": "When your ad is shown to someone",
        "Click": "When someone clicks on your ad",
        "Conversion": "When someone completes your desired action (purchase, signup, etc.)",
        "Quality Score": "Google's 1-10 rating of ad quality and relevance",
        "Ad Rank": "Determines ad position: Bid × Quality Score",
        "CPC": "Cost Per Click - what you pay when someone clicks",
        "CPM": "Cost Per Thousand Impressions",
        "CPA": "Cost Per Acquisition - cost to get one conversion",
        "ROAS": "Return on Ad Spend - revenue divided by cost",
        "Search Terms": "Actual queries users typed that triggered your ads",
        "Negative Keywords": "Keywords you exclude to prevent irrelevant traffic",
        "Ad Extension": "Additional information shown with your ad (sitelinks, callouts, etc.)",
        "Impression Share": "Percentage of possible impressions your ad received"
    }
    
    if term in glossary:
        st.info(f"**{term}:** {glossary[term]}")
        
def create_interactive_calculator(calc_type: str):
    """Interactive calculators for common Google Ads calculations."""
    
    if calc_type == "CPA":
        st.markdown("### 🧮 CPA Calculator")
        
        col1, col2 = st.columns(2)
        with col1:
            cost = st.number_input("Total Cost ($)", min_value=0.0, value=1000.0, step=50.0)
        with col2:
            conversions = st.number_input("Conversions", min_value=1, value=50, step=5)
        
        cpa = cost / conversions
        st.metric("Cost Per Acquisition (CPA)", f"${cpa:.2f}")
        
        target_cpa = st.number_input("What's your target CPA? ($)", min_value=0.0, value=25.0, step=5.0)
        
        if cpa > target_cpa:
            diff = cpa - target_cpa
            st.error(f"⚠️ You're ${diff:.2f} over target. Need to improve conversion rate or lower costs.")
        else:
            diff = target_cpa - cpa
            st.success(f"✅ You're ${diff:.2f} under target. Great performance!")
    
    elif calc_type == "ROAS":
        st.markdown("### 🧮 ROAS Calculator")
        
        col1, col2 = st.columns(2)
        with col1:
            revenue = st.number_input("Revenue ($)", min_value=0.0, value=5000.0, step=100.0)
        with col2:
            cost = st.number_input("Ad Spend ($)", min_value=0.01, value=1000.0, step=50.0)
        
        roas = revenue / cost
        st.metric("Return on Ad Spend (ROAS)", f"{roas:.2f}x")
        
        st.write(f"For every $1 spent, you earn ${roas:.2f}")
        
        if roas >= 4.0:
            st.success("✅ Excellent ROAS!")
        elif roas >= 2.0:
            st.info("👍 Good ROAS")
        else:
            st.warning("⚠️ ROAS could be improved")
