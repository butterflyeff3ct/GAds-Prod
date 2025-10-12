# 🔍 Gemini API Quota Integration Analysis

## Current State Analysis

Based on my scan of the entire project, here's where user ID and session ID mapping needs to be integrated to limit Gemini API queries per user session:

---

## 🎯 **Integration Points Identified**

### 1. **Primary Gemini API Usage Locations**

#### **A. Keyword Generation** (`services/gemini_client.py`)
- **Function**: `generate_keywords(prompt: str)`
- **Location**: Lines 100-139
- **Current Quota Check**: ✅ Already implemented
- **Integration Status**: ✅ Uses `quota_mgr.can_use_gemini()` and `quota_mgr.increment_gemini_tokens(500)`

#### **B. Ad Copy Generation** (`services/gemini_client.py`)
- **Function**: `generate_ads(prompt, num_headlines, num_descriptions, tone)`
- **Location**: Lines 141-179
- **Current Quota Check**: ✅ Already implemented
- **Integration Status**: ✅ Uses quota system

#### **C. Campaign Insights** (`services/gemini_client.py`)
- **Function**: `generate_campaign_insights(campaign_config)`
- **Location**: Lines 181-220
- **Current Quota Check**: ✅ Already implemented
- **Integration Status**: ✅ Uses quota system

#### **D. Campaign Wizard Usage** (`app/campaign_wizard.py`)
- **Location**: Lines 851, 876
- **Current Status**: ✅ Uses `gemini.generate_keywords()` and `gemini.model.generate_content()`
- **Integration Status**: ✅ Already integrated through GeminiClient

---

## 🔧 **Required Integration Points**

### 1. **Session State Initialization** (`core/auth.py`)

**Current Location**: Lines 208-240 (`_initialize_session_tracking`)

**Required Changes**:
```python
# ADD: Initialize quota system with user context
def _initialize_session_tracking(self, user_info: Dict[str, Any]):
    # ... existing code ...
    
    # NEW: Initialize quota system with user context
    from app.quota_system.quota_manager import get_quota_manager
    quota_mgr = get_quota_manager()
    
    # Set user context in quota manager
    quota_mgr.set_user_context(
        user_id=user_info.get("sub"),
        email=user_info.get("email"),
        session_id=session_tracker.session_id
    )
    
    # Load user's existing quota usage from sheets
    quota_mgr.load_quotas_from_sheets(user_info.get("email"))
```

### 2. **Quota Manager Enhancement** (`app/quota_system/quota_manager.py`)

**Required New Methods**:
```python
class QuotaManager:
    def __init__(self):
        # ... existing code ...
        self.current_user_id = None
        self.current_session_id = None
        self.current_user_email = None
    
    def set_user_context(self, user_id: str, email: str, session_id: str):
        """Set current user context for quota tracking"""
        self.current_user_id = user_id
        self.current_user_email = email
        self.current_session_id = session_id
        
        # Update session state with user context
        st.session_state['quota_user_id'] = user_id
        st.session_state['quota_user_email'] = email
        st.session_state['quota_session_id'] = session_id
    
    def get_user_context(self) -> Dict[str, str]:
        """Get current user context"""
        return {
            'user_id': self.current_user_id or st.session_state.get('quota_user_id'),
            'email': self.current_user_email or st.session_state.get('quota_user_email'),
            'session_id': self.current_session_id or st.session_state.get('quota_session_id')
        }
    
    def increment_gemini_tokens(self, count: int) -> bool:
        """Enhanced with user context logging"""
        # ... existing quota logic ...
        
        # NEW: Log to user-specific tracking
        user_context = self.get_user_context()
        if user_context['user_id']:
            self._log_gemini_usage_to_user_tracking(
                user_id=user_context['user_id'],
                session_id=user_context['session_id'],
                tokens_used=count,
                operation_type="gemini_api_call"
            )
        
        return within_quota
```

### 3. **Google Sheets Integration** (`utils/gsheet_writer.py`)

**Required New Methods**:
```python
class GSheetLogger:
    def log_gemini_usage(self, user_id: str, session_id: str, 
                        tokens_used: int, operation_type: str) -> bool:
        """Log individual Gemini API usage to sheets"""
        if not self.enabled:
            return False
        
        try:
            # Create or get Gemini Usage worksheet
            self._ensure_gemini_usage_worksheet()
            
            self._rate_limit()
            self.gemini_usage_worksheet.append_row([
                user_id,
                session_id,
                operation_type,
                tokens_used,
                self._get_timestamp(),
                "active"
            ])
            return True
        except Exception as e:
            print(f"Failed to log Gemini usage: {e}")
            return False
    
    def get_user_gemini_usage(self, user_id: str, session_id: str = None) -> Dict:
        """Get user's Gemini usage for current session or all sessions"""
        if not self.enabled:
            return {}
        
        try:
            self._rate_limit()
            all_rows = self.gemini_usage_worksheet.get_all_values()
            
            user_usage = []
            for row in all_rows[1:]:  # Skip header
                if len(row) >= 6 and row[0] == user_id:
                    if session_id is None or row[1] == session_id:
                        user_usage.append({
                            'session_id': row[1],
                            'operation_type': row[2],
                            'tokens_used': int(row[3]) if row[3] else 0,
                            'timestamp': row[4],
                            'status': row[5]
                        })
            
            return {
                'total_tokens': sum(usage['tokens_used'] for usage in user_usage),
                'operations': len(user_usage),
                'by_session': self._group_usage_by_session(user_usage)
            }
        except Exception:
            return {}
```

### 4. **Session Cleanup Integration** (`main.py`)

**Current Location**: Lines 90-110 (`cleanup_on_exit`)

**Required Enhancement**:
```python
def cleanup_on_exit():
    """Enhanced cleanup with quota tracking"""
    try:
        auth = GoogleAuthManager()
        user = auth.get_user()
        session_tracker = auth.get_session_tracker()
        
        # NEW: Sync final quota usage
        if user and session_tracker:
            from app.quota_system.quota_manager import get_quota_manager
            quota_mgr = get_quota_manager()
            quota_mgr.sync_all_quotas()
            
            # Log session end with final quota usage
            if auth.gsheet_logger_safe and auth.gsheet_logger_safe.enabled:
                session_data = session_tracker.get_session_data()
                quota_summary = quota_mgr.get_quota_summary()
                
                auth.gsheet_logger_safe.log_session_end(
                    email=user.get("email"),
                    session_id=session_data["session_id"],
                    tokens_used=quota_summary['gemini']['used'],
                    operations=quota_summary['gemini']['operations'],
                    status="session_ended"
                )
    except Exception:
        pass
```

---

## 🚀 **Implementation Priority**

### **Phase 1: Core Integration** (High Priority)
1. **Enhance QuotaManager** with user context methods
2. **Update authentication flow** to initialize quota system with user context
3. **Add user-specific quota loading** from Google Sheets

### **Phase 2: Enhanced Tracking** (Medium Priority)
1. **Add Gemini usage worksheet** to Google Sheets
2. **Implement detailed usage logging** per operation
3. **Add quota reset functionality** for admins

### **Phase 3: Advanced Features** (Low Priority)
1. **Add quota analytics** and usage patterns
2. **Implement quota alerts** and notifications
3. **Add quota management UI** for admins

---

## 📊 **Current Quota System Status**

✅ **Already Implemented**:
- Quota tracking in session state
- Quota checks before Gemini API calls
- Token increment tracking
- Google Sheets synchronization
- Fallback to mock data when quota exceeded

❌ **Missing Integration**:
- User ID mapping to quota usage
- Session-specific quota tracking
- Per-user quota limits (currently global)
- User-specific quota persistence across sessions

---

## 🔧 **Quick Implementation Steps**

1. **Add user context to QuotaManager** (30 minutes)
2. **Update authentication flow** to set user context (15 minutes)
3. **Enhance Google Sheets logging** with user-specific tracking (45 minutes)
4. **Test integration** with existing quota system (30 minutes)

**Total Estimated Time**: ~2 hours for basic integration

The existing quota system is well-designed and just needs user context integration to map quota usage to specific users and sessions.
