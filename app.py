"""Universal AI Browser Agent - Modern Streamlit Web UI for SLAB Hackathon."""

import json
import os
import sys
from pathlib import Path

# Inject project root directory into sys.path for direct execution from any terminal
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from src.brain import analyze_and_route_intent
from src.config import GEMINI_MODEL, WEBCMD_BIN
from src.memory import (
    get_billing_accounts,
    get_healthcare_preferences,
    get_recruitment_company,
    get_student_profile,
    load_memory,
    save_memory,
    update_memory,
)
from src.universal_agent import ADAPTERS, _context_for, build_command_preview
from src.webcmd_bridge import execute_webcmd

# Page Config
st.set_page_config(
    page_title="Universal AI Browser Agent",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Modern CSS Styling
st.markdown(
    """
    <style>
    /* Main Theme Variables & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Gradient & Hero Section */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%);
        padding: 1.8rem 2.2rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #cbd5e1;
        margin-bottom: 1rem;
    }

    /* Badge Pills */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .badge-blue { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
    .badge-purple { background: rgba(147, 51, 234, 0.2); color: #c084fc; }
    .badge-green { background: rgba(34, 197, 94, 0.2); color: #86efac; }
    .badge-amber { background: rgba(245, 158, 11, 0.2); color: #fde047; }
    
    /* Confirmation Card */
    .confirm-card {
        background: linear-gradient(135deg, #451a03 0%, #78350f 100%);
        border: 2px solid #f59e0b;
        border-radius: 12px;
        padding: 1.5rem;
        color: #fef3c7;
        margin: 1rem 0;
        box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.2);
    }

    /* Result Card Styling */
    .result-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    
    .card-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f8fafc;
        border-bottom: 1px solid #334155;
        padding-bottom: 0.5rem;
        margin-bottom: 0.75rem;
    }

    /* Code block styling */
    .stCodeBlock {
        font-family: 'JetBrains Mono', monospace !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "memory_data" not in st.session_state:
    st.session_state.memory_data = load_memory()

if "execution_state" not in st.session_state:
    st.session_state.execution_state = None

if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None


# ==========================================
# SIDEBAR - Memory Editor & Agent Settings
# ==========================================
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.caption("Universal AI Browser Agent Configuration")
    st.markdown("---")

    # WebCMD Settings
    st.subheader("🌐 WebCMD Settings")
    webcmd_profile = st.text_input("Profile Name", value="default", help="WebCMD browser profile")
    webcmd_session = st.text_input("Session ID", value="session-01", help="WebCMD browser session ID")
    
    st.markdown(
        f"""
        <div style="font-size:0.85rem; padding: 0.5rem; background: #0f172a; border-radius: 8px; border: 1px solid #334155;">
        <b>Binary:</b> <code>{WEBCMD_BIN}</code><br/>
        <b>Platform:</b> <code>{'Windows' if os.name == 'nt' else 'Unix/Linux'}</code><br/>
        <b>Gemini Model:</b> <code>{GEMINI_MODEL}</code>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("---")

    # User Memory Editor
    st.subheader("💾 User Memory & Context")
    memory = st.session_state.memory_data
    
    with st.expander("🎓 Student Profile", expanded=False):
        sp = memory.get("student_profile", {})
        sp_name = st.text_input("Full Name", value=sp.get("name", "Alex Rivera"))
        sp_univ = st.text_input("University", value=sp.get("university", "VSSUT Burla"))
        sp_branch = st.text_input("Branch", value=sp.get("branch", "Computer Science & Engineering"))
        sp_reg = st.text_input("Reg. Number", value=sp.get("registration_number", "2102060045"))
        sp_cgpa = st.number_input("CGPA", value=float(sp.get("cgpa", 8.95)), step=0.05, min_value=0.0, max_value=10.0)
        sp_skills_str = st.text_area("Skills (comma separated)", value=", ".join(sp.get("skills", ["Python", "React", "ML"])))
        sp_resume = st.text_input("Resume Path", value=sp.get("resume_path", "Alex_Rivera_CV.pdf"))

    with st.expander("💼 Recruitment Company", expanded=False):
        rc = memory.get("recruitment_company", {})
        rc_name = st.text_input("Company Name", value=rc.get("company_name", "TechCorp Innovations"))
        rc_job = st.text_input("Active Job Post", value=rc.get("active_job", "Senior Full Stack Engineer"))

    with st.expander("⚡ Billing Accounts", expanded=False):
        ba = memory.get("billing_accounts", {})
        ba_elec = st.text_input("Electricity Account", value=ba.get("electricity", "ELEC-8839201"))
        ba_bb = st.text_input("Broadband Account", value=ba.get("broadband", ba.get("internet", "BB-9920144")))
        ba_mob = st.text_input("Mobile Account", value=ba.get("mobile", "MOB-9876543210"))

    with st.expander("🏥 Healthcare Preferences", expanded=False):
        hp = memory.get("healthcare_preferences", {})
        hp_loc = st.text_input("Preferred Location", value=hp.get("preferred_location", hp.get("location", "Downtown Medical Center")))
        hp_ins = st.text_input("Insurance Provider", value=hp.get("insurance_provider", hp.get("insurance", "HealthGuard Premium")))

    if st.button("💾 Save Memory Updates", use_container_width=True, type="primary"):
        updated_memory = {
            "student_profile": {
                "name": sp_name,
                "university": sp_univ,
                "branch": sp_branch,
                "registration_number": sp_reg,
                "cgpa": sp_cgpa,
                "skills": [s.strip() for s in sp_skills_str.split(",") if s.strip()],
                "document_paths": [sp_resume],
                "resume_path": sp_resume,
            },
            "recruitment_company": {
                "company_name": rc_name,
                "active_job": rc_job,
                "filter_criteria": {"min_experience": 2, "required_skills": ["React", "Python"], "location": "Remote"},
            },
            "billing_accounts": {
                "electricity": ba_elec,
                "broadband": ba_bb,
                "internet": ba_bb,
                "mobile": ba_mob,
            },
            "healthcare_preferences": {
                "preferred_location": hp_loc,
                "location": hp_loc,
                "insurance_provider": hp_ins,
                "insurance": hp_ins,
                "preferred_slots": ["Morning (9:00 AM - 12:00 PM)", "Weekend Slots"],
            },
        }
        save_memory(updated_memory)
        st.session_state.memory_data = updated_memory
        st.success("Memory updated and saved successfully!")


# ==========================================
# MAIN CONTENT AREA
# ==========================================

# Hero Banner
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🌐 Universal AI Browser Agent</div>
        <div class="hero-subtitle">SLAB Hackathon Autonomous Multi-Domain WebCMD Bridge</div>
        <div>
            <span class="badge-pill badge-blue">🎓 Student Opportunities</span>
            <span class="badge-pill badge-purple">💼 Recruitment Aggregator</span>
            <span class="badge-pill badge-amber">⚡ Utility & Bills</span>
            <span class="badge-pill badge-green">🏥 Healthcare Booking</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Preset Prompt Quick Launchers
st.markdown("##### 🚀 Quick-Launch Presets")
c1, c2, c3, c4 = st.columns(4)

preset_prompt = None
if c1.button("🎓 CS Scholarships", use_container_width=True):
    preset_prompt = "Find computer science research fellowships matching my Python and Machine Learning skills"
if c2.button("💼 Collated ATS Candidates", use_container_width=True):
    preset_prompt = "Screen candidate pool and collate Alex Rivera's resume package for Senior Full Stack Engineer at TechCorp"
if c3.button("⚡ Electricity Bill Status", use_container_width=True):
    preset_prompt = "Check my electricity bill balance for account ELEC-8839201"
if c4.button("🏥 Cardio Appointment", use_container_width=True):
    preset_prompt = "Find available cardiologist appointment slots near Downtown covered by HealthGuard Premium"

# Prompt Input Bar
user_prompt_input = st.text_input(
    "Enter your prompt query for the Universal Agent:",
    value=preset_prompt if preset_prompt else "Check my electricity bill balance for account ELEC-8839201",
    placeholder="e.g. Find computer science research scholarships for me...",
)

col_exec, col_clear = st.columns([4, 1])
with col_exec:
    run_clicked = st.button("✨ Run Universal Agent Command", type="primary", use_container_width=True)
with col_clear:
    if st.button("🧹 Reset State", use_container_width=True):
        st.session_state.execution_state = None
        st.session_state.pending_confirmation = None
        st.rerun()

# Process Execution Request
if run_clicked and user_prompt_input.strip():
    st.session_state.pending_confirmation = None
    with st.spinner("🧠 Brain Intent Routing with Gemini..."):
        try:
            intent = analyze_and_route_intent(user_prompt_input)
            module = intent["module"]
            context = _context_for(module)
            
            # Check if high-impact action requires confirmation
            if intent.get("requires_confirmation"):
                # Run dry run preview
                preview_action = "status" if module == "bills" else ("find_slots" if module == "healthcare" else "search")
                preview_args = {
                    "target": intent.get("target", ""),
                    "action": preview_action,
                    **intent.get("parameters", {}),
                    **context,
                }
                preview_cmd = build_command_preview(module, preview_args, webcmd_profile, webcmd_session)
                preview_result = execute_webcmd(
                    ADAPTERS[module],
                    preview_args,
                    profile=webcmd_profile,
                    session=webcmd_session,
                )
                
                st.session_state.pending_confirmation = {
                    "intent": intent,
                    "context": context,
                    "preview_cmd": preview_cmd,
                    "preview_result": preview_result,
                    "prompt": user_prompt_input,
                }
            else:
                # Direct execution for read-only actions
                args = {
                    "target": intent.get("target", ""),
                    "action": intent.get("action", "search"),
                    **intent.get("parameters", {}),
                    **context,
                }
                cmd_str = build_command_preview(module, args, webcmd_profile, webcmd_session)
                result = execute_webcmd(
                    ADAPTERS[module],
                    args,
                    profile=webcmd_profile,
                    session=webcmd_session,
                )
                
                st.session_state.execution_state = {
                    "intent": intent,
                    "context": context,
                    "command_str": cmd_str,
                    "result": result,
                }
        except Exception as exc:
            st.error(f"Execution Error: {exc}")


# ==========================================
# ACTION CONFIRMATION MODAL / CARD
# ==========================================
if st.session_state.pending_confirmation:
    pending = st.session_state.pending_confirmation
    intent = pending["intent"]
    module = intent["module"]
    
    st.markdown(
        f"""
        <div class="confirm-card">
            <h3>⚠️ High-Impact Action Confirmation Required</h3>
            <p>The AI Agent determined that executing action <b>'{intent.get('action').upper()}'</b> on module <b>'{module}'</b> will perform an official transaction or submission.</p>
            <ul>
                <li><b>Target:</b> {intent.get('target', 'N/A')}</li>
                <li><b>Action Requested:</b> {intent.get('action')}</li>
                <li><b>WebCMD Profile:</b> {webcmd_profile}</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.subheader("🔍 Dry-Run Action Preview Result")
    st.json(pending["preview_result"])
    
    col_approve, col_deny = st.columns(2)
    with col_approve:
        if st.button("✅ Approve & Execute High-Impact Action", type="primary", use_container_width=True):
            with st.spinner("⚡ Executing confirmed action via WebCMD Bridge..."):
                final_action = intent.get("action", "pay")
                final_args = {
                    "target": intent.get("target", ""),
                    "action": final_action,
                    **intent.get("parameters", {}),
                    **pending["context"],
                }
                final_cmd = build_command_preview(module, final_args, webcmd_profile, webcmd_session)
                final_result = execute_webcmd(
                    ADAPTERS[module],
                    final_args,
                    profile=webcmd_profile,
                    session=webcmd_session,
                )
                
                st.session_state.execution_state = {
                    "intent": intent,
                    "context": pending["context"],
                    "command_str": final_cmd,
                    "result": final_result,
                }
                st.session_state.pending_confirmation = None
                st.rerun()

    with col_deny:
        if st.button("❌ Cancel Action", use_container_width=True):
            st.session_state.execution_state = {
                "intent": intent,
                "context": pending["context"],
                "command_str": pending["preview_cmd"],
                "result": {"status": "cancelled", "message": "High-impact action was declined by user."},
            }
            st.session_state.pending_confirmation = None
            st.rerun()


# ==========================================
# EXECUTION VISUALIZER DASHBOARD
# ==========================================
if st.session_state.execution_state:
    st.markdown("---")
    st.subheader("📊 Execution Visualizer Pipeline")
    
    state = st.session_state.execution_state
    intent = state["intent"]
    context = state["context"]
    command_str = state["command_str"]
    result = state["result"]

    tab_brain, tab_memory, tab_cmd, tab_output = st.tabs([
        "🧠 1. Brain Routing",
        "💾 2. Injected Memory Context",
        "🛠️ 3. WebCMD Command",
        "✨ 4. Structured Results",
    ])

    # Tab 1: Brain Intent
    with tab_brain:
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        col_b1.metric("Module", intent.get("module"))
        col_b2.metric("Target", intent.get("target") or "Default")
        col_b3.metric("Action", intent.get("action"))
        col_b4.metric("Confirmation Required", str(intent.get("requires_confirmation")))
        
        st.markdown("**Extracted Intent Object:**")
        st.json(intent)

    # Tab 2: Context Injected
    with tab_memory:
        st.caption("User memory subset passed into adapter arguments:")
        st.json(context)

    # Tab 3: Command String
    with tab_cmd:
        st.caption("Exact WebCMD CLI invocation executed by Python bridge:")
        st.code(command_str, language="bash")
        
        st.caption("Bridge Details:")
        st.json({
            "binary_resolved": WEBCMD_BIN,
            "adapter_used": ADAPTERS.get(intent.get("module")),
            "profile": webcmd_profile,
            "session": webcmd_session,
        })

    # Tab 4: Rich Output & Results
    with tab_output:
        st.markdown("### Domain Outcome Card")
        
        module = result.get("module", intent.get("module"))
        status = result.get("status", "unknown")
        
        if status in {"paid", "payment_successful", "appointment_booked", "application_submitted"}:
            st.success(f"✅ Success: {result.get('note', 'Action completed successfully.')}")
        else:
            st.info(f"ℹ️ Status ({status}): {result.get('note', 'Query completed.')}")

        # Specialized Visual Cards
        if module == "bills":
            if result.get("payment_receipt"):
                receipt = result["payment_receipt"]
                st.markdown(
                    f"""
                    <div style="background:#064e3b; border:1px solid #10b981; padding:1rem; border-radius:10px; color:#a7f3d0;">
                        <h4>🎉 Payment Settlement Authorized</h4>
                        <p><b>Payment Token:</b> <code>{receipt.get('payment_token')}</code></p>
                        <p><b>Transaction ID:</b> <code>{receipt.get('transaction_id')}</code></p>
                        <p><b>Amount Settled:</b> ₹{receipt.get('amount_settled')} ({receipt.get('currency')})</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if result.get("bills"):
                st.write("**Account Bills Breakdown:**")
                st.dataframe(result["bills"], use_container_width=True)

        elif module == "healthcare":
            if result.get("booking_confirmation"):
                bconf = result["booking_confirmation"]
                st.markdown(
                    f"""
                    <div style="background:#1e1b4b; border:1px solid #6366f1; padding:1rem; border-radius:10px; color:#c7d2fe;">
                        <h4>🏥 Appointment Confirmed</h4>
                        <p><b>Confirmation ID:</b> <code>{bconf.get('appointment_id')}</code></p>
                        <p><b>Doctor:</b> {bconf.get('doctor_name')} ({bconf.get('specialty')})</p>
                        <p><b>Location:</b> {bconf.get('clinic_name')} ({bconf.get('address')})</p>
                        <p><b>Slot:</b> {bconf.get('appointment_date')} at {bconf.get('appointment_time')}</p>
                        <p><b>Insurance Voucher:</b> {bconf.get('insurance_applied')} ({bconf.get('co_pay_amount')})</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if result.get("clinics"):
                st.write("**Discovered Clinics & Specialists:**")
                for clinic in result["clinics"]:
                    with st.expander(f"🏥 {clinic['clinic_name']} - {clinic['doctor_name']} ({clinic['rating']}⭐)", expanded=True):
                        st.write(f"**Specialty:** {clinic['specialty']} | **Experience:** {clinic['experience_years']} years")
                        st.write(f"**Fee:** {clinic['consultation_fee']} | **Insurance:** {', '.join(clinic['accepted_insurance'])}")
                        st.write("**Available Slots:**")
                        st.dataframe(clinic["available_slots"], use_container_width=True)

        elif module == "student_opportunities":
            if result.get("application_payload"):
                app = result["application_payload"]
                st.markdown(
                    f"""
                    <div style="background:#064e3b; border:1px solid #10b981; padding:1rem; border-radius:10px; color:#a7f3d0;">
                        <h4>🎓 Student Application Pre-filled & Submitted</h4>
                        <p><b>Verification Code:</b> <code>{app.get('verification_code')}</code></p>
                        <p><b>Applicant:</b> {app.get('applicant_name')} ({app.get('registration_number')})</p>
                        <p><b>Program:</b> {app.get('selected_opportunity')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if result.get("opportunities"):
                st.write("**Matched Opportunities & Skill Alignment:**")
                st.dataframe(result["opportunities"], use_container_width=True)

        elif module == "recruitment":
            if result.get("candidate_evaluation"):
                ceval = result["candidate_evaluation"]
                st.markdown(
                    f"""
                    <div style="background:#311042; border:1px solid #c084fc; padding:1rem; border-radius:10px; color:#f5d0fe;">
                        <h4>💼 Candidate Screening & Skill Alignment</h4>
                        <p><b>Primary Candidate:</b> {ceval.get('primary_candidate')}</p>
                        <p><b>Skills Overlap:</b> {ceval.get('skills_overlap_percentage')}% ({', '.join(ceval.get('matched_skills', []))})</p>
                        <p><b>ATS Recommendation:</b> {ceval.get('recommendation')}</p>
                        <p><b>Resume Attached:</b> <code>{ceval.get('resume_attached')}</code></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if result.get("candidate_pool"):
                st.write("**Candidate Pool Summary:**")
                st.dataframe(result["candidate_pool"], use_container_width=True)

        st.markdown("---")
        st.write("**Raw JSON Payload:**")
        st.json(result)
