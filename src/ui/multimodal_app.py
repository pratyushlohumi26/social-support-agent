"""
UAE Social Support AI System - Enhanced Streamlit UI
"""
import os
import streamlit as st
import requests
import json
from typing import Dict, Any, Optional
import time
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv 
load_dotenv()

API_PORT = os.getenv("API_PORT", 8005)
API_HOST = os.getenv("API_HOST", "0.0.0.0")

# Page configuration
st.set_page_config(
    page_title="UAE Social Support AI",
    page_icon="🇦🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
def api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None):
    """Make API request"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def main():
    """Main application"""

    # Header
    st.title("🇦🇪 UAE Social Support AI System")
    st.markdown("*Advanced Multimodal AI for Social & Economic Support Assessment*")

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["🏠 Dashboard", "📄 New Application", "💬 Chat Assistant", "📊 Analytics", "🔧 System Status"]
    )

    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📄 New Application":
        show_application_form()
    elif page == "💬 Chat Assistant":
        show_chat_interface()
    elif page == "📊 Analytics":
        show_analytics()
    elif page == "🔧 System Status":
        show_system_status()

def show_dashboard():
    """Dashboard page"""
    st.header("Dashboard Overview")

    # Get system stats
    stats = api_request("/stats")

    if stats:
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Applications", stats.get("total_applications", 0))
        with col2:
            st.metric("Active Agents", stats.get("active_agents", 4))
        with col3:
            st.metric("Success Rate", stats.get("success_rate", "95%"))
        with col4:
            st.metric("Avg Processing Time", stats.get("processing_average_time", "15s"))

    # Recent activity
    st.subheader("Recent Activity")

    # Mock recent applications
    recent_apps = [
        {"ID": "UAE-2024-001", "Applicant": "Ahmed Al Mansouri", "Status": "Approved", "Amount": "15,000 AED"},
        {"ID": "UAE-2024-002", "Applicant": "Fatima Al Zahra", "Status": "Under Review", "Amount": "8,000 AED"},
        {"ID": "UAE-2024-003", "Applicant": "Mohammed Al Rashid", "Status": "Documents Required", "Amount": "12,000 AED"}
    ]

    df = pd.DataFrame(recent_apps)
    st.dataframe(df, use_container_width=True)

def show_application_form():
    """Application submission form"""
    st.header("📄 Submit New Application")

    with st.form("uae_application_form"):
        st.subheader("👤 Personal Information")

        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input("Full Name*", placeholder="Ahmed Al Mansouri")
            emirates_id = st.text_input("Emirates ID*", placeholder="784-2024-1234567-1")
            mobile_number = st.text_input("Mobile Number*", placeholder="+971501234567")

        with col2:
            nationality = st.selectbox("Nationality", ["UAE", "GCC", "Arab", "Asian", "Western", "Other"])
            residency_status = st.selectbox("Residency Status", ["Citizen", "Resident", "Visit Visa"])
            emirate = st.selectbox("Emirate", ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Fujairah", "Ras Al Khaimah", "Umm Al Quwain"])

        st.subheader("👨‍👩‍👧‍👦 Family Information")

        col3, col4 = st.columns(2)
        with col3:
            marital_status = st.selectbox("Marital Status", ["Single", "Married", "Divorced", "Widowed"])
            family_size = st.number_input("Family Size", min_value=1, max_value=20, value=1)
        with col4:
            dependents = st.number_input("Number of Dependents", min_value=0, max_value=15, value=0)

        st.subheader("💼 Employment Information")

        col5, col6 = st.columns(2)
        with col5:
            employment_status = st.selectbox("Employment Status", ["Employed", "Self-Employed", "Unemployed", "Retired", "Student"])
            employer_name = st.text_input("Employer Name", placeholder="Emirates National Bank")
        with col6:
            job_title = st.text_input("Job Title", placeholder="Customer Service Officer")
            monthly_salary = st.number_input("Monthly Salary (AED)", min_value=0.0, value=0.0)

        st.subheader("🎯 Support Request")

        support_type = st.selectbox("Support Type", ["Financial Assistance", "Economic Enablement", "Both", "Emergency Support"])
        amount_requested = st.number_input("Amount Requested (AED)", min_value=0.0, max_value=100000.0, value=0.0)
        urgency_level = st.selectbox("Urgency Level", ["Low", "Medium", "High", "Critical"])
        reason_for_support = st.text_area("Reason for Support*", placeholder="Explain your situation and why you need support...")
        career_goals = st.text_area("Career Goals (if applicable)", placeholder="Describe your career aspirations...")

        st.subheader("📎 Document Upload")

        uploaded_files = st.file_uploader(
            "Upload Required Documents",
            type=['pdf', 'jpg', 'png', 'xlsx', 'csv'],
            accept_multiple_files=True,
            help="Upload Emirates ID, Bank Statements, Salary Certificate, Assets/Liabilities, etc."
        )

        submitted = st.form_submit_button("🚀 Submit Application")

        if submitted:
            if not all([full_name, emirates_id, mobile_number, reason_for_support]):
                st.error("Please fill in all required fields marked with *")
            else:
                # Prepare application data
                application_data = {
                    "personal_info": {
                        "full_name": full_name,
                        "emirates_id": emirates_id,
                        "nationality": nationality.lower(),
                        "residency_status": residency_status.lower(),
                        "emirate": emirate.lower().replace(" ", "_"),
                        "family_size": family_size,
                        "dependents": dependents,
                        "mobile_number": mobile_number,
                        "marital_status": marital_status.lower()
                    },
                    "employment_info": {
                        "employment_status": employment_status.lower(),
                        "employer_name": employer_name,
                        "job_title": job_title,
                        "monthly_salary": monthly_salary
                    },
                    "support_request": {
                        "support_type": support_type.lower().replace(" ", "_"),
                        "urgency_level": urgency_level.lower(),
                        "amount_requested": amount_requested,
                        "reason_for_support": reason_for_support,
                        "career_goals": career_goals
                    }
                }

                # Submit application
                with st.spinner("Processing your application..."):
                    result = api_request("/applications/submit", method="POST", data=application_data)

                    if result and result.get("success"):
                        st.success("🎉 Application submitted successfully!")

                        # Show processing results
                        processing_result = result.get("processing_result", {})
                        final_decision = processing_result.get("final_decision", {})

                        if final_decision:
                            st.subheader("📋 Processing Results")

                            status = final_decision.get("status", "unknown")
                            if status == "approved":
                                st.success(f"✅ Application Approved!")

                                financial_support = final_decision.get("financial_support", {})
                                if financial_support.get("approved_amount", 0) > 0:
                                    st.info(f"💰 Approved Amount: {financial_support['approved_amount']:,.0f} AED")
                                    st.info(f"⏱️ Duration: {financial_support['duration_months']} months")

                            elif status == "conditional_approval":
                                st.warning("⚠️ Conditional Approval - Additional requirements needed")
                            elif status == "review_required":
                                st.info("🔄 Application requires manual review")
                            else:
                                st.error("❌ Application needs additional information")

                            # Economic enablement
                            enablement = final_decision.get("economic_enablement", {})
                            if enablement.get("training_programs"):
                                st.subheader("🎓 Recommended Training Programs")
                                for program in enablement["training_programs"]:
                                    st.write(f"- {program.get('name', 'Training Program')}")

                            # Next steps
                            next_steps = final_decision.get("next_steps", [])
                            if next_steps:
                                st.subheader("📝 Next Steps")
                                for step in next_steps:
                                    st.write(f"• {step}")

                    else:
                        st.error("❌ Application submission failed. Please try again.")

def show_chat_interface_old():
    """Chat interface"""
    st.header("💬 Chat Assistant")
    st.markdown("*Get help with your application, documents, or eligibility questions*")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Chat input
    user_input = st.text_input("Ask me anything about UAE social support...", key="chat_input")

    if st.button("Send") and user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "message": user_input})

        # Get AI response
        with st.spinner("Thinking..."):
            response = api_request("/chat", method="POST", data={"message": user_input})

            if response:
                ai_message = response.get("response", "Sorry, I couldn't process your request.")
                st.session_state.chat_history.append({"role": "assistant", "message": ai_message})

                # Show suggested actions
                suggested_actions = response.get("suggested_actions", [])
                if suggested_actions:
                    st.subheader("💡 Suggested Actions")
                    for action in suggested_actions:
                        st.button(action, key=f"action_{action}")

    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Chat History")
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.markdown(f"**You:** {chat['message']}")
            else:
                st.markdown(f"**Assistant:** {chat['message']}")
def show_analytics():
    """Fixed analytics dashboard with proper chart handling"""
    st.header("📊 Analytics Dashboard")
    st.markdown("*System performance and application statistics*")
    
    try:
        # Get system stats from API
        stats = api_request("/stats")
        
        if stats:
            # Display key metrics
            st.subheader("📈 Key Performance Indicators")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Applications", 
                    stats.get("total_applications", 0),
                    help="Total applications processed"
                )
            
            with col2:
                st.metric(
                    "Active Agents", 
                    stats.get("active_agents", 0),
                    help="AI agents currently operational"
                )
            
            with col3:
                st.metric(
                    "Success Rate", 
                    stats.get("success_rate", "0%"),
                    help="Application processing success rate"
                )
            
            with col4:
                st.metric(
                    "Avg Processing Time", 
                    stats.get("processing_average_time", "N/A"),
                    help="Average time to process applications"
                )
        
        # Create two columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Application Status Distribution")
            
            # Mock data for application status
            status_data = {
                "Approved": 45,
                "Under Review": 25, 
                "Conditional": 15,
                "Documents Required": 10,
                "Declined": 5
            }
            
            try:
                # Create bar chart using st.bar_chart
                status_df = pd.DataFrame(
                    list(status_data.items()), 
                    columns=['Status', 'Count']
                ).set_index('Status')
                
                st.bar_chart(status_df)
                
            except Exception as e:
                st.error(f"Error creating status chart: {e}")
                # Fallback: Display as table
                st.table(pd.DataFrame(list(status_data.items()), columns=['Status', 'Applications']))
        
        with col2:
            st.subheader("🏙️ Applications by Emirate")
            
            # Mock data for emirate distribution
            emirate_data = {
                "Dubai": 40,
                "Abu Dhabi": 25,
                "Sharjah": 15,
                "Ajman": 8,
                "Fujairah": 5,
                "Ras Al Khaimah": 4,
                "Umm Al Quwain": 3
            }
            
            try:
                # Create a proper chart using plotly or matplotlib alternative
                # Using st.bar_chart as it's more reliable than st.pie_chart
                emirate_df = pd.DataFrame(
                    list(emirate_data.items()), 
                    columns=['Emirate', 'Applications']
                ).set_index('Emirate')
                
                st.bar_chart(emirate_df)
                
            except Exception as e:
                st.error(f"Error creating emirate chart: {e}")
                # Fallback: Display as table
                st.table(pd.DataFrame(list(emirate_data.items()), columns=['Emirate', 'Applications']))
        
        # Additional analytics sections
        st.subheader("💰 Support Amount Analysis")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("📈 Monthly Trends")
            
            # Mock monthly data
            monthly_data = pd.DataFrame({
                'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'Applications': [120, 135, 145, 160, 180, 195],
                'Approved': [95, 110, 120, 135, 150, 165],
                'Amount (AED)': [1200000, 1350000, 1450000, 1600000, 1800000, 1950000]
            })
            
            try:
                # Display monthly trends
                chart_data = monthly_data.set_index('Month')[['Applications', 'Approved']]
                st.line_chart(chart_data)
                
            except Exception as e:
                st.error(f"Error creating trend chart: {e}")
                st.table(monthly_data)
        
        with col4:
            st.subheader("🎯 Support Categories")
            
            # Mock support category data
            category_data = {
                "Financial Assistance": 60,
                "Career Development": 25,
                "Emergency Support": 10,
                "Special Circumstances": 5
            }
            
            try:
                category_df = pd.DataFrame(
                    list(category_data.items()), 
                    columns=['Category', 'Percentage']
                ).set_index('Category')
                
                st.bar_chart(category_df)
                
            except Exception as e:
                st.error(f"Error creating category chart: {e}")
                st.table(pd.DataFrame(list(category_data.items()), columns=['Category', 'Percentage']))
        
        # System performance metrics
        st.subheader("🔧 System Performance")
        
        # Get debug information
        debug_info = api_request("/debug/system")
        
        if debug_info:
            col5, col6 = st.columns(2)
            
            with col5:
                st.subheader("🤖 AI System Status")
                
                llm_integration = debug_info.get("llm_integration", {})
                agents_status = debug_info.get("agents_status", {})
                
                # Display AI system metrics
                ai_metrics = {
                    "Ollama Cloud": "✅ Connected" if llm_integration.get("ollama_cloud") == "configured" else "❌ Not configured",
                    "LangGraph Workflow": "✅ Operational" if llm_integration.get("langgraph_workflow") == "operational" else "❌ Unavailable",
                    "Processing Mode": llm_integration.get("processing_mode", "unknown").replace("_", " ").title(),
                    "Active Agents": llm_integration.get("agents_count", 0)
                }
                
                for metric, value in ai_metrics.items():
                    st.write(f"**{metric}:** {value}")
            
            with col6:
                st.subheader("⚡ Performance Metrics")
                
                # Mock performance data
                performance_metrics = {
                    "Average Response Time": "2.3 seconds",
                    "API Uptime": "99.8%",
                    "Memory Usage": "450 MB",
                    "CPU Usage": "23%",
                    "Database Queries": "1,247",
                    "Cache Hit Rate": "94.5%"
                }
                
                for metric, value in performance_metrics.items():
                    st.write(f"**{metric}:** {value}")
        
        # Real-time activity log
        st.subheader("📋 Recent Activity")
        
        # Mock recent activity data
        recent_activity = [
            {"Time": "16:45", "Event": "New application submitted", "User": "Ahmed Al-*****", "Status": "Processing"},
            {"Time": "16:42", "Event": "Application approved", "User": "Fatima Al-*****", "Status": "Completed"},
            {"Time": "16:38", "Event": "Document uploaded", "User": "Mohammed *****", "Status": "Under Review"},
            {"Time": "16:35", "Event": "Training enrollment", "User": "Aisha *****", "Status": "Enrolled"},
            {"Time": "16:32", "Event": "Support disbursed", "User": "Omar *****", "Status": "Completed"},
        ]
        
        activity_df = pd.DataFrame(recent_activity)
        st.dataframe(activity_df, use_container_width=True)
        
        # Download analytics report
        st.subheader("📥 Export Analytics")
        
        col7, col8 = st.columns(2)
        
        with col7:
            if st.button("📊 Download Summary Report", use_container_width=True):
                # Create summary report
                summary_report = {
                    "report_date": datetime.now().isoformat(),
                    "total_applications": stats.get("total_applications", 0) if stats else 0,
                    "success_rate": stats.get("success_rate", "0%") if stats else "0%",
                    "status_distribution": status_data,
                    "emirate_distribution": emirate_data,
                    "category_distribution": category_data,
                    "system_status": debug_info.get("system_status", "unknown") if debug_info else "unknown"
                }
                
                import json
                report_json = json.dumps(summary_report, indent=2)
                
                st.download_button(
                    label="📄 Download JSON Report",
                    data=report_json,
                    file_name=f"uae_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col8:
            if st.button("📈 Download Raw Data", use_container_width=True):
                # Create CSV data
                combined_data = pd.DataFrame({
                    'Metric': list(status_data.keys()) + list(emirate_data.keys()),
                    'Value': list(status_data.values()) + list(emirate_data.values()),
                    'Type': ['Status'] * len(status_data) + ['Emirate'] * len(emirate_data)
                })
                
                csv_data = combined_data.to_csv(index=False)
                
                st.download_button(
                    label="📊 Download CSV Data",
                    data=csv_data,
                    file_name=f"uae_analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"❌ Error loading analytics: {e}")
        st.info("🔄 Please refresh the page or contact support if the issue persists.")
        
        # Show basic fallback analytics
        st.subheader("📊 Basic System Information")
        
        basic_info = {
            "System Status": "Operational",
            "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Version": "3.0.0",
            "Environment": "Production"
        }
        
        for key, value in basic_info.items():
            st.write(f"**{key}:** {value}")

def show_system_status():
    """System status page"""
    st.header("🔧 System Status")

    # Get system debug info
    debug_info = api_request("/debug/system")

    if debug_info:
        st.subheader("🎛️ System Health")

        status = debug_info.get("system_status", "unknown")
        if status == "healthy":
            st.success("✅ System is running normally")
        else:
            st.error("❌ System issues detected")

        st.subheader("🤖 AI Agents Status")
        agents_status = debug_info.get("agents_status", {})

        for agent_name, agent_status in agents_status.items():
            if agent_status == "operational":
                st.success(f"✅ {agent_name.replace('_', ' ').title()}: {agent_status}")
            else:
                st.error(f"❌ {agent_name.replace('_', ' ').title()}: {agent_status}")

        st.subheader("📋 System Information")
        st.json(debug_info)
    else:
        st.error("❌ Unable to connect to system")

def show_chat_interface():
    """Fixed chat interface with proper suggested actions handling"""
    st.header("💬 Chat Assistant")
    st.markdown("*Get help with your application, documents, or eligibility questions*")
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize suggested actions
    if "last_suggested_actions" not in st.session_state:
        st.session_state.last_suggested_actions = []
    
    # Initialize pending message (for suggested actions)
    if "pending_message" not in st.session_state:
        st.session_state.pending_message = ""
    
    # Check for suggested action click
    suggested_action_clicked = None
    if st.session_state.last_suggested_actions:
        st.subheader("💡 Suggested Actions")
        st.markdown("*Click any suggestion below:*")
        
        # Create clickable buttons for suggested actions
        cols = st.columns(min(len(st.session_state.last_suggested_actions), 2))  # Max 2 columns
        
        for i, action in enumerate(st.session_state.last_suggested_actions):
            col_index = i % 2
            with cols[col_index]:
                if st.button(
                    action, 
                    key=f"suggest_action_{i}",
                    help="Click to send this question",
                    use_container_width=True
                ):
                    suggested_action_clicked = action
                    st.session_state.pending_message = action
                    break
    
    # Chat input with default value from suggested action
    default_value = st.session_state.pending_message if st.session_state.pending_message else ""
    user_input = st.text_input(
        "Ask me anything about UAE social support...", 
        key="chat_input",
        value=default_value,
        placeholder="Type your question or click a suggested action above..."
    )
    
    # Send button
    send_clicked = st.button("Send", type="primary", disabled=not user_input.strip())
    
    # Process message when send is clicked or suggested action is selected
    if send_clicked and user_input.strip():
        message_to_process = user_input.strip()
        
        # Clear pending message after processing
        st.session_state.pending_message = ""
        
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user", 
            "message": message_to_process,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get AI response
        with st.spinner("Getting response..."):
            response_data = api_request("/chat", method="POST", data={"message": message_to_process})
            
            if response_data and response_data.get("success"):
                ai_message = response_data.get("response", "I couldn't process your request.")
                suggested_actions = response_data.get("suggested_actions", [])
                intent = response_data.get("intent", "general")
                llm_powered = response_data.get("llm_powered", False)
                
                # Add AI response to history
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "message": ai_message,
                    "timestamp": datetime.now().isoformat(),
                    "intent": intent,
                    "llm_powered": llm_powered
                })
                
                # Update suggested actions for next interaction
                st.session_state.last_suggested_actions = suggested_actions
                
                # Show success message
                if llm_powered:
                    st.success("✅ Response generated using AI")
                else:
                    st.info("ℹ️ Response from knowledge base")
                    
            else:
                st.error("❌ Failed to get response. Please try again.")
                
        # Force rerun to clear input and show new messages
        st.rerun()
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("💬 Conversation History")
        
        # Show recent messages (last 8 for better performance)
        recent_messages = st.session_state.chat_history[-8:]
        
        for chat in recent_messages:
            if chat["role"] == "user":
                # User message
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 15px;
                        border-radius: 15px 15px 5px 15px;
                        margin: 10px 0;
                        margin-left: 20%;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    ">
                        <strong>🧑‍💼 You</strong><br>
                        {chat['message']}
                        <br><small style="opacity: 0.8; font-size: 0.8em;">
                            {datetime.fromisoformat(chat['timestamp']).strftime('%I:%M %p')}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Assistant message
                llm_indicator = "🤖" if chat.get("llm_powered") else "🔧"
                llm_text = "AI Assistant" if chat.get("llm_powered") else "Knowledge Base"
                intent_display = f" • {chat.get('intent', '').replace('_', ' ').title()}" if chat.get('intent') else ""
                
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                        padding: 15px;
                        border-radius: 15px 15px 15px 5px;
                        margin: 10px 0;
                        margin-right: 20%;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    ">
                        <strong>{llm_indicator} {llm_text}{intent_display}</strong><br>
                        {chat['message'].replace(chr(10), '<br>')}
                        <br><small style="opacity: 0.8; font-size: 0.8em;">
                            {datetime.fromisoformat(chat['timestamp']).strftime('%I:%M %p')}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        # Welcome message when no chat history
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin: 20px 0;
        ">
            <h3>👋 Welcome to UAE Social Support AI Assistant!</h3>
            <p>I'm here to help you with:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>✅ Application eligibility and requirements</li>
                <li>📄 Required documents and preparation</li>
                <li>💰 Support amounts and calculations</li>
                <li>🎓 Training and career programs</li>
                <li>📊 Application status and process</li>
            </ul>
            <p><strong>Ask me anything about UAE social support!</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Initial suggested actions
        st.subheader("💡 Popular Questions")
        initial_actions = [
            "Am I eligible for UAE social support?",
            "What documents do I need for my application?",
            "How much financial support can I get?",
            "What training programs are available?"
        ]
        
        cols = st.columns(2)
        for i, action in enumerate(initial_actions):
            col_index = i % 2
            with cols[col_index]:
                if st.button(
                    action, 
                    key=f"initial_action_{i}",
                    help="Click to ask this question",
                    use_container_width=True
                ):
                    st.session_state.pending_message = action
                    st.rerun()
    
    # Chat management in sidebar
    with st.sidebar:
        st.subheader("💬 Chat Management")
        
        # Chat statistics
        if st.session_state.chat_history:
            total_messages = len(st.session_state.chat_history)
            user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
            ai_responses = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant" and msg.get("llm_powered")])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Messages", total_messages)
                st.metric("AI Responses", ai_responses)
            with col2:
                st.metric("Questions", user_messages)
                st.metric("Knowledge Base", total_messages - ai_responses - user_messages)
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("🆕 New Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.last_suggested_actions = []
            st.session_state.pending_message = ""
            st.rerun()
        
        if st.button("💾 Export Chat", use_container_width=True):
            if st.session_state.chat_history:
                # Create exportable chat log
                chat_export = []
                for msg in st.session_state.chat_history:
                    chat_export.append({
                        "timestamp": msg["timestamp"],
                        "role": msg["role"],
                        "message": msg["message"],
                        "intent": msg.get("intent", ""),
                        "ai_powered": msg.get("llm_powered", False)
                    })
                
                import json
                chat_json = json.dumps(chat_export, indent=2)
                
                st.download_button(
                    label="📥 Download Chat History",
                    data=chat_json,
                    file_name=f"uae_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            else:
                st.info("No chat history to export")
        
        # System status
        st.subheader("🔧 System Status")
        
        # Check API health
        health_status = api_request("/chat/health")
        if health_status:
            overall_status = health_status.get("overall_status", "unknown")
            if overall_status == "healthy":
                st.success("✅ All systems operational")
            elif overall_status == "partial":
                st.warning("⚠️ Limited functionality")
            else:
                st.error("❌ System issues detected")
            
            # Show detailed status
            with st.expander("View Details"):
                st.json(health_status)
        else:
            st.error("❌ Cannot connect to chat system")


if __name__ == "__main__":
    main()
