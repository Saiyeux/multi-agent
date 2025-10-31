"""Streamlit Web UI for Multi-Agent Development System (Refactored)"""

import streamlit as st
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.builders.workflow_builder import WorkflowBuilder


st.set_page_config(
    page_title="Multi-Agent Dev System",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Multi-Agent Software Development System")
st.markdown("基于本地 LLM 的自动化开发系统 (新架构)")

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")
config_file = st.sidebar.text_input("Config File", value="config.yaml")
debug_mode = st.sidebar.checkbox("Debug Mode (Unlimited iterations)", value=False)

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = None
if 'result' not in st.session_state:
    st.session_state.result = None
if 'running' not in st.session_state:
    st.session_state.running = False


def init_engine():
    """Initialize workflow engine"""
    try:
        config_path = Path(config_file)
        if not config_path.exists():
            st.error(f"Configuration file not found: {config_file}")
            return False

        st.session_state.engine = WorkflowBuilder.build_from_config(str(config_path))

        # Apply debug mode
        if debug_mode:
            st.session_state.engine.debug_mode = True
            st.session_state.engine.max_iterations = float('inf')

        st.sidebar.success("✓ Engine initialized")
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
            # Initialize engine if needed
            if not st.session_state.engine:
                if not init_engine():
                    st.stop()

            st.session_state.running = True

            # Run engine
            with st.spinner("Development in progress..."):
                try:
                    result = asyncio.run(
                        st.session_state.engine.run({'requirement': requirement})
                    )
                    st.session_state.result = result
                    st.session_state.running = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.session_state.running = False

with col2:
    st.header("📊 Status")
    if st.session_state.engine:
        status = st.session_state.engine.get_current_state()
        st.metric("Current Stage", status.get('current_stage', 'N/A'))
        st.metric("Iteration", f"{status['iteration']}/{status['max_iterations']}")
        st.metric("Debug Mode", "✓" if status['debug_mode'] else "✗")
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
            st.metric("Duration", result.get('duration', 'N/A'))
        with col3:
            st.metric("Iterations", result.get('iterations', 0))

        st.subheader("📦 Package")
        st.code(result.get('output', 'N/A'))

        # Display workspace contents
        st.subheader("📁 Workspace Files")
        if st.session_state.engine:
            context = st.session_state.engine.context.memory.get_context()

            tabs = st.tabs(["Requirements", "Design", "Code", "Tests"])

            with tabs[0]:
                for filename, content in context.get('requirements', {}).items():
                    with st.expander(filename):
                        st.markdown(content)

            with tabs[1]:
                for filename, content in context.get('design', {}).items():
                    with st.expander(filename):
                        st.markdown(content)

            with tabs[2]:
                for filename, content in context.get('code', {}).items():
                    with st.expander(filename):
                        st.code(content, language='python')

            with tabs[3]:
                for filename, content in context.get('tests', {}).items():
                    with st.expander(filename):
                        st.code(content, language='python')

    elif result['status'] == 'aborted':
        st.warning("⚠️ Workflow aborted by user")

    else:
        st.error("❌ Development failed")
        st.write("Reason:", result.get('error', 'Unknown'))
        st.write("Duration:", result.get('duration', 'N/A'))
        st.write("Iterations:", result.get('iterations', 0))

        # Show error details
        if st.expander("View Error Details"):
            st.json(result)

# Footer
st.divider()
st.markdown("""
**Multi-Agent Dev System** (New Architecture) | Powered by Ollama & qwen2.5:3b
""")