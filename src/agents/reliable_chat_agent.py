"""
Reliable LangGraph Chat Agent - Simplified for Better Initialization
"""

import logging
import os
import json
from typing import Dict, Any, List, TypedDict
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize dependencies at module level
LANGGRAPH_READY = False
OLLAMA_READY = False
chat_client = None

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_READY = True
    logger.info("✅ LangGraph loaded successfully")
except ImportError as e:
    logger.error(f"❌ LangGraph import failed: {e}")

try:
    import ollama
    api_key = os.getenv("OLLAMA_API_KEY", "")
    if api_key:
        chat_client = ollama.Client(
            host=os.getenv("OLLAMA_BASE_URL", "https://ollama.com"),
            headers={'Authorization': api_key}
        )
        # Test the client
        test_response = chat_client.chat(
            model=os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud"),
            messages=[{'role': 'user', 'content': 'test'}],
            stream=False
        )
        OLLAMA_READY = True
        logger.info("✅ Ollama client initialized and tested successfully")
    else:
        logger.error("❌ OLLAMA_API_KEY not set")
except Exception as e:
    logger.error(f"❌ Ollama initialization failed: {e}")

class ChatState(TypedDict):
    message: str
    context: Dict[str, Any]
    response: str
    intent: str
    suggested_actions: List[str]

class ReliableChatAgent:
    """Reliable chat agent with better error handling"""
    
    def __init__(self):
        self.ready = LANGGRAPH_READY and OLLAMA_READY
        self.model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
        
        if self.ready:
            try:
                self.workflow = self._build_workflow()
                self.memory = MemorySaver()
                logger.info("🎉 Reliable Chat Agent fully initialized")
            except Exception as e:
                logger.error(f"❌ Workflow creation failed: {e}")
                self.ready = False
        else:
            logger.warning("⚠️ Chat Agent in fallback mode")
    
    def _build_workflow(self):
        """Build simplified LangGraph workflow"""
        workflow = StateGraph(ChatState)
        
        workflow.add_node("process_message", self._process_message_node)
        workflow.set_entry_point("process_message")
        workflow.add_edge("process_message", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _process_message_node(self, state: ChatState) -> ChatState:
        """Process message with LLM"""
        try:
            message = state["message"]
            
            # Classify intent first
            intent = self._quick_intent_classification(message)
            
            # Generate response using Ollama
            system_context = """You are a helpful UAE Social Support AI assistant.

            Provide specific, detailed information about:
            - UAE social support eligibility
            - Required documents (Emirates ID, bank statements, salary certificates)
            - Support amounts (5,000-50,000 AED based on assessment)
            - Training programs in UAE
            - Application processes

            Be conversational, helpful, and specific to UAE context.
            Always provide actionable information."""

            response_prompt = f"""
            User Question: {message}
            Intent Category: {intent}
            
            Provide a comprehensive, helpful response with specific UAE information.
            """

            response = chat_client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_context},
                    {'role': 'user', 'content': response_prompt}
                ],
                stream=False
            )
            
            llm_response = response['message']['content']
            
            # Generate suggested actions
            suggested_actions = self._get_suggested_actions(intent)
            
            state.update({
                "response": llm_response,
                "intent": intent,
                "suggested_actions": suggested_actions
            })
            
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            # Use detailed fallback
            state.update({
                "response": self._get_detailed_fallback_response(state["message"]),
                "intent": self._quick_intent_classification(state["message"]),
                "suggested_actions": self._get_suggested_actions(self._quick_intent_classification(state["message"]))
            })
        
        return state
    
    def _quick_intent_classification(self, message: str) -> str:
        """Quick rule-based intent classification"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["document", "paper", "file", "emirates id", "bank statement"]):
            return "document_help"
        elif any(word in message_lower for word in ["eligible", "qualify", "criteria", "requirement"]):
            return "eligibility_question"
        elif any(word in message_lower for word in ["amount", "money", "aed", "support", "financial"]):
            return "support_amounts"
        elif any(word in message_lower for word in ["training", "course", "program", "skill", "career"]):
            return "training_programs"
        elif any(word in message_lower for word in ["apply", "application", "process", "submit"]):
            return "application_process"
        elif any(word in message_lower for word in ["status", "progress", "check", "update"]):
            return "status_inquiry"
        else:
            return "general_help"
    
    def _get_detailed_fallback_response(self, message: str) -> str:
        """Detailed fallback responses"""
        intent = self._quick_intent_classification(message)
        
        responses = {
            "document_help": """**📋 Required Documents for UAE Social Support Application:**

**Essential Documents:**
1. **Emirates ID** - Both sides, clear high-resolution photo
2. **Bank Statements** - Last 3 months from all accounts
3. **Salary Certificate** - Recent official letter from employer
4. **Family Book** - If you have dependents
5. **Passport Copy** - Bio page and UAE visa page

**Additional Documents (if applicable):**
- Rental agreement/Ejari
- Utility bills (DEWA/ADDC/SEWA)
- Medical reports (for medical support requests)
- School certificates (for education support)
- Previous social support documentation

**Document Quality Requirements:**
✅ Clear, readable scans or photos
✅ All text must be visible
✅ No shadows or glare
✅ File size under 5MB per document
✅ Accepted formats: PDF, JPG, PNG

**Pro Tips:**
- Use document scanner apps for best quality
- Ensure Arabic documents are clearly visible
- Double-check Emirates ID expiry date
- Bank statements must show transaction history""",

            "eligibility_question": """**✅ UAE Social Support Eligibility Criteria:**

**Income Thresholds by Emirate:**
🏙️ **Dubai**: Up to 25,000 AED/month
🏛️ **Abu Dhabi**: Up to 23,000 AED/month  
🏘️ **Sharjah**: Up to 20,000 AED/month
🏖️ **Other Emirates**: Up to 18,000 AED/month

**Family Factors:**
👨‍👩‍👧‍👦 **Family Size Bonus**: +2,000 AED threshold per dependent
👶 **Children Under 18**: Higher priority scoring
🏠 **Single Parents**: Additional consideration
👴 **Elderly Dependents**: Extra support available

**Employment Status:**
✅ **Employed**: Full-time, part-time, or contract workers
✅ **Self-Employed**: With valid trade license  
✅ **Unemployed**: Actively seeking employment
✅ **Students**: Full-time with proof of enrollment

**Residency Requirements:**
🇦🇪 **UAE Nationals**: All income levels considered
🏡 **Long-term Residents**: 2+ years in UAE
📋 **Valid Visa**: Current residence visa required

**Priority Categories:**
🚨 **Emergency**: Medical, housing, food security
👨‍👩‍👧‍👦 **Family Support**: Large families, single parents
🎓 **Career Development**: Training and upskilling
💼 **Economic Enablement**: Job placement assistance""",

            "support_amounts": """**💰 UAE Social Support Amount Guidelines:**

**Financial Support Categories:**

🚨 **Emergency Support (Immediate)**
- Amount: 2,000 - 8,000 AED
- Duration: One-time payment
- For: Medical emergencies, urgent bills, food security

💚 **Basic Support (Regular)**  
- Amount: 5,000 - 15,000 AED
- Duration: 3-6 months
- For: Monthly living expenses, rent assistance

⭐ **Enhanced Support (Comprehensive)**
- Amount: 15,000 - 35,000 AED  
- Duration: 6-12 months
- For: Family support, career transition

🎯 **Special Circumstances**
- Amount: Up to 50,000 AED
- Duration: 12-18 months
- For: Major life changes, disability support

**Amount Calculation Factors:**
📊 **Income Gap**: Difference between earnings and needs
👨‍👩‍👧‍👦 **Family Size**: +1,500 AED per dependent typically
🏠 **Living Costs**: Adjusted by emirate cost of living
🎯 **Support Type**: Emergency vs. ongoing assistance

**Disbursement Schedule:**
📅 **Monthly**: Most common for regular support  
📅 **Quarterly**: For larger amounts
💳 **Bank Transfer**: Direct to your UAE bank account
📱 **Digital Wallet**: Als available for quick access

**Additional Benefits:**
🎓 **Training Allowance**: 1,000-3,000 AED during courses
🔍 **Job Search Support**: 500-1,000 AED monthly
👶 **Child Support**: 300-800 AED per child monthly""",

            "training_programs": """**🎓 UAE Career Development & Training Programs:**

**Technology Sector:**
💻 **Digital Marketing Certificate** (Dubai Future Academy)
   - Duration: 3 months | Cost: Free for qualifying applicants
   - Skills: Social media, SEO, Google Ads, Analytics
   
🔢 **Data Analysis Bootcamp** (ADEK Training)
   - Duration: 4 months | Cost: Subsidized 
   - Skills: Excel, Power BI, SQL, Python basics

🔐 **Cybersecurity Essentials** (UAE Cyber Security Council)
   - Duration: 6 months | Cost: Free for UAE nationals
   - Skills: Network security, ethical hacking, compliance

**Healthcare Sector:**
🏥 **Healthcare Administration** (UAE Health Authority)
   - Duration: 6 months | Cost: Free
   - Skills: Hospital management, patient care systems

💊 **Medical Coding Certification** (DHA Approved)
   - Duration: 4 months | Cost: 2,500 AED (reimbursable)
   - Skills: ICD-10, medical terminology, billing

**Finance Sector:**
🏦 **Banking Excellence Program** (Emirates Institute)
   - Duration: 5 months | Cost: Free for UAE residents
   - Skills: Islamic banking, customer service, compliance

💰 **Financial Planning Certificate** (Dubai Financial Market)
   - Duration: 4 months | Cost: 1,800 AED
   - Skills: Investment planning, insurance, retirement planning

**Government Sector:**
🏛️ **Public Administration** (Federal Authority for Government HR)
   - Duration: 6 months | Cost: Free
   - Skills: Policy development, citizen services

📱 **Digital Government Services** (Smart Dubai)
   - Duration: 3 months | Cost: Free
   - Skills: Digital transformation, e-government platforms

**Program Benefits:**
✅ **Job Placement Assistance**: 85% placement rate
💰 **Training Allowance**: 1,000-2,000 AED monthly during training
🎯 **Skill Certification**: Internationally recognized certificates  
🤝 **Mentorship**: Assigned industry mentors
📚 **Materials Provided**: Books, software access, equipment""",

            "application_process": """**📝 UAE Social Support Application Process:**

**Step 1: Pre-Application (Day 1-2)**
✅ Check eligibility requirements for your emirate
✅ Gather all required documents  
✅ Create account on UAE Social Support portal
✅ Complete eligibility self-assessment

**Step 2: Document Preparation (Day 3-5)**
📋 Emirates ID (both sides, clear photo)
🏦 Bank statements (last 3 months, all accounts)
💼 Employment documents (salary certificate, contract)
🏠 Residence documents (Ejari, utility bills)
👨‍👩‍👧‍👦 Family documents (family book, school certificates)

**Step 3: Online Application (Day 6)**
🌐 Login to UAE Social Support portal
📝 Complete application form (45-60 minutes)
📤 Upload all documents (ensure quality)
💰 Specify support amount and type needed
📋 Write detailed reason for support request
✅ Review and submit application

**Step 4: Initial Review (Day 7-10)**
🔍 Automated document verification
📞 May receive call for clarification
📧 Email/SMS updates on progress
⚠️ Request for additional documents if needed

**Step 5: Assessment (Day 11-15)**
👥 Case worker assignment  
📊 Eligibility score calculation
🏠 Possible home visit (for large amounts)
💼 Employment verification call
👨‍👩‍👧‍👦 Family situation assessment

**Step 6: Decision (Day 16-21)**
✅ **Approved**: Congratulations message + next steps
⚠️ **Conditional**: Requirements to fulfill
🔄 **Under Review**: More time needed
❌ **Declined**: Reason provided + appeal options

**Step 7: Disbursement (Day 22-30)**
🏦 Bank account verification
💳 First payment processed  
📱 Payment confirmation SMS
📞 Orientation call scheduled
📅 Follow-up appointment booked

**Timeline:**
⚡ **Fast Track** (7-14 days): Emergency cases
📅 **Standard** (14-21 days): Regular applications  
🔍 **Detailed Review** (21-30 days): Complex cases

**Support During Process:**
📞 **Hotline**: 800-SUPPORT (24/7)
💬 **Live Chat**: Available 8AM-8PM
📧 **Email Updates**: At each stage
📱 **SMS Notifications**: Real-time status updates""",

            "status_inquiry": """**🔍 Check Your UAE Social Support Application Status:**

**Online Status Check:**
🌐 **UAE Social Support Portal**: https://socialsupport.uae.gov.ae
🔐 Login with Emirates ID + password
📊 View real-time application status
📄 Download status reports and letters

**Status Categories Explained:**

📝 **"Submitted"** - Application received successfully
   ⏱️ Processing time: 1-2 days
   📋 Next: Document verification begins

🔍 **"Under Review"** - Documents being verified
   ⏱️ Processing time: 3-7 days  
   📋 Next: Eligibility assessment

📊 **"Assessment"** - Eligibility being determined
   ⏱️ Processing time: 5-10 days
   📋 Next: Case worker review

👥 **"Case Worker Review"** - Human evaluation  
   ⏱️ Processing time: 3-7 days
   📋 Next: Final decision

✅ **"Approved"** - Congratulations! Support approved
   ⏱️ Processing time: 2-5 days
   📋 Next: Disbursement setup

💳 **"Disbursement"** - Payment being processed
   ⏱️ Processing time: 1-3 days  
   📋 Next: Payment received

**Alternative Status Check Methods:**

📱 **SMS Service**: Send "STATUS [Application ID]" to 4567
📞 **Phone Inquiry**: Call 800-SUPPORT
   - Have your Emirates ID and application ID ready
   - Available 24/7 in Arabic and English

📧 **Email Updates**: Automatic notifications sent to registered email

**If Your Application is Delayed:**
⏰ **Beyond 21 Days**: Contact case worker directly  
📞 **Emergency Cases**: Call priority hotline 800-URGENT
💬 **Live Chat**: Quick status updates available
📝 **Follow-up Request**: Submit through portal

**Common Status Issues:**
❓ **"Additional Documents Required"**: Check email/SMS for specific requests
⚠️ **"On Hold"**: Usually waiting for document clarification  
🔄 **"Returned for Correction"**: Update required information and resubmit

**Status Update Frequency:**
📅 **Daily**: For applications in active processing
📅 **Weekly**: For applications under detailed review
📅 **Immediate**: For status changes (approved/declined)""",

            "general_help": """**🇦🇪 Welcome to UAE Social Support AI Assistant!**

**I'm here to help you navigate the UAE social support system. Here's what I can assist you with:**

**📋 Application Support:**
✅ Check eligibility requirements by emirate
✅ Guide you through document preparation  
✅ Explain the complete application process
✅ Help you calculate potential support amounts
✅ Track your application status

**💰 Financial Support Information:**
💵 Support amounts: 5,000 - 50,000 AED
⏰ Duration: 3-12 months typically
🎯 Types: Emergency, regular, career development
📊 Calculation factors: income, family size, emirate

**🎓 Career Development:**
🎯 Training programs in tech, healthcare, finance  
💼 Job placement assistance (85% success rate)
🤝 Mentorship and career counseling
💰 Training allowances during programs

**🏛️ UAE-Specific Features:**
🇦🇪 All 7 emirates covered with specific criteria
📱 Arabic and English language support
🏦 Direct bank transfer disbursements
👨‍👩‍👧‍👦 Family and cultural considerations

**🚀 Quick Actions:**
- **"Check eligibility"** - See if you qualify
- **"Required documents"** - Complete document list
- **"Support amounts"** - Amount guidelines  
- **"Training programs"** - Available courses
- **"Application status"** - Track your application

**📞 Need Human Help?**
- Hotline: 800-SUPPORT (24/7)
- Emergency: 800-URGENT
- Live chat: 8AM-8PM daily
- In-person: Visit any UAE Social Support office

**💡 Pro Tips:**
- Have your Emirates ID ready for faster service
- Keep documents updated and high-quality
- Apply early - processing takes 14-21 days
- Use the self-assessment tool first

**What would you like help with today?** Just ask me anything about UAE social support!"""
        }
        
        return responses.get(intent, responses["general_help"])
    
    def _get_suggested_actions(self, intent: str) -> List[str]:
        """Get suggested actions with proper formatting for UI"""
        
        action_map = {
            "document_help": [
                "What documents do I need for my application?",
                "How do I scan documents properly?", 
                "Can I submit documents in Arabic?",
                "What if my Emirates ID is expired?"
            ],
            "eligibility_question": [
                "Am I eligible for UAE social support?",
                "What are the income limits for Dubai?",
                "Do I qualify with my family size?",
                "How does residency status affect eligibility?"
            ],
            "support_amounts": [
                "How much financial support can I get?",
                "What determines the support amount?",
                "When will I receive the payment?",
                "Can I get additional support later?"
            ],
            "training_programs": [
                "What training programs are available?",
                "How do I apply for career training?",
                "Are there any free courses?",
                "Will training help me get a job?"
            ],
            "application_process": [
                "How do I apply for social support?",
                "What is the application timeline?",
                "Can I apply online?",
                "What happens after I submit?"
            ],
            "status_inquiry": [
                "How do I check my application status?",
                "Why is my application taking so long?",
                "Can I update my application?",
                "Who is my assigned case worker?"
            ],
            "general_help": [
                "Ask about eligibility requirements",
                "Ask about required documents",
                "Ask about support amounts", 
                "Ask about training programs"
            ]
        }
        
        return action_map.get(intent, action_map["general_help"])
    
    async def process_chat(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process chat message"""
        
        if self.ready:
            try:
                # Use LangGraph workflow
                initial_state = ChatState(
                    message=message,
                    context=context or {},
                    response="",
                    intent="",
                    suggested_actions=[]
                )
                
                result = await self.workflow.ainvoke(initial_state)
                
                return {
                    "success": True,
                    "response": result["response"],
                    "intent": result["intent"],
                    "suggested_actions": result["suggested_actions"],
                    "llm_powered": True,
                    "langgraph_used": True,
                    "timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Workflow failed: {e}")
                # Fall through to detailed fallback
        
        # Detailed fallback mode
        intent = self._quick_intent_classification(message)
        
        return {
            "success": True,
            "response": self._get_detailed_fallback_response(message),
            "intent": intent,
            "suggested_actions": self._get_suggested_actions(intent),
            "llm_powered": False,
            "fallback_mode": True,
            "timestamp": datetime.now().isoformat()
        }

# Initialize the reliable chat agent
reliable_chat_agent = None
try:
    reliable_chat_agent = ReliableChatAgent()
    logger.info(f"🎉 Reliable Chat Agent ready: {reliable_chat_agent.ready}")
except Exception as e:
    logger.error(f"❌ Failed to initialize reliable chat agent: {e}")