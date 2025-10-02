"""Streamlit Web UI for Multi-Agent Development System"""

import streamlit as st
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator import DevOrchestrator, WorkflowState


st.set_page_config(
    page_title="Multi-Agent Dev System",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Multi-Agent Software Development System")
st.markdown("基于本地 LLM 的自动化开发系统")

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")
config_file = st.sidebar.text_input("Config File", value="config.yaml")

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None
if 'result' not in st.session_state:
    st.session_state.result = None
if 'running' not in st.session_state:
    st.session_state.running = False


def init_orchestrator():
    """Initialize orchestrator"""
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            st.error(f"Configuration file not found: {config_file}")
            return False

        config = DevOrchestrator.load_config(str(config_path))
        st.session_state.orchestrator = DevOrchestrator(config)
        st.sidebar.success("✓ Orchestrator initialized")
        return True
    except Exception as e:
        st.sidebar.error(f"Failed to initialize: {str(e)}")
        return False


# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 User Requirement")
    requirement = st.text_area(
        "Enter your software requirement",
        height=200,
        placeholder="例如：创建一个命令行计算器，支持加减乘除四则运算...",
        key="requirement_input"
    )

    if st.button("🚀 Start Development", disabled=st.session_state.running):
        if not requirement:
            st.error("Please enter a requirement")
        else:
            if not st.session_state.orchestrator:
                if not init_orchestrator():
                    st.stop()

            st.session_state.running = True

            # Run orchestrator
            with st.spinner("Development in progress..."):
                try:
                    result = asyncio.run(
                        st.session_state.orchestrator.run(requirement)
                    )
                    st.session_state.result = result
                    st.session_state.running = False
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.session_state.running = False

with col2:
    st.header("📊 Status")
    if st.session_state.orchestrator:
        status = st.session_state.orchestrator.get_status()
        st.metric("Current State", status['state'])
        st.metric("Iteration", f"{status['iteration']}/{status['max_iterations']}")
    else:
        st.info("Not initialized")

# Results section
if st.session_state.result:
    st.divider()
    st.header("📋 Results")

    result = st.session_state.result

    if result['status'] == 'success':
        st.success("✅ Development completed successfully!")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", "Success")
        with col2:
            st.metric("Total Tests", result['report']['total'])
        with col3:
            st.metric("Failed Tests", result['report']['failed'])

        st.subheader("📦 Package")
        st.code(result['package'])

        # Display workspace contents
        st.subheader("📁 Workspace Files")
        if st.session_state.orchestrator:
            context = st.session_state.orchestrator.memory.get_context()

            tabs = st.tabs(["Requirements", "Design", "Code", "Tests"])

            with tabs[0]:
                for filename, content in context['requirements'].items():
                    with st.expander(filename):
                        st.markdown(content)

            with tabs[1]:
                for filename, content in context['design'].items():
                    with st.expander(filename):
                        st.markdown(content)

            with tabs[2]:
                for filename, content in context['code'].items():
                    with st.expander(filename):
                        st.code(content, language='python')

            with tabs[3]:
                for filename, content in context['tests'].items():
                    with st.expander(filename):
                        st.code(content, language='python')

    else:
        st.error("❌ Development failed")
        st.write("Reason:", result.get('reason', result.get('message', 'Unknown')))

        if 'last_result' in result:
            st.subheader("Last Test Result")
            st.json(result['last_result'])

# Footer
st.divider()
st.markdown("""
**Multi-Agent Dev System** | Powered by Ollama & qwen2.5:3b
""")