"""
Statement Upload View for Smart Expense Analyzer
Handles PDF bank statement uploads and parsing via API.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List
from datetime import datetime
import sys
from pathlib import Path

# Add ui directory to path for imports
ui_dir = Path(__file__).parent.parent
if str(ui_dir) not in sys.path:
    sys.path.insert(0, str(ui_dir))

from api_client import get_api_client

def _fetch_upload_history(user_id: str):
    """Fetch upload history from API"""
    api = get_api_client()
    print("[STATEMENT_UPLOAD] Calling API: /api/statements/history")
    history_data = api.get_upload_history()
    print(f"[STATEMENT_UPLOAD] Received history: {len(history_data.get('history', []))} entries")
    return history_data


def show_statement_upload(current_user: Dict):
    """Main view for uploading and parsing bank statements."""
    print(f"[STATEMENT_UPLOAD] Loading statement upload page for user: {current_user.get('id')}")
    
    st.header("📄 Upload Bank Statements")
    st.caption("Upload PDF statements from any bank as a backup to Plaid")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📤 Upload New", "📋 Upload History"])
    
    with tab1:
        render_upload_tab(current_user)
    
    with tab2:
        render_history_tab(current_user)


def render_upload_tab(current_user: Dict):
    """Render the file upload and parsing interface."""
    print("[STATEMENT_UPLOAD] Rendering upload tab")
    
    # Set flag to skip API calls in other tabs when file is being selected
    # This prevents unnecessary API calls during file selection
    if 'statement_uploader' in st.session_state and st.session_state.statement_uploader:
        # File is selected, set flag to skip API calls in other tabs
        st.session_state.skip_api_calls = True
        print("[STATEMENT_UPLOAD] File selected - setting skip_api_calls flag")
    
    # Supported banks info
    with st.expander("ℹ️ Supported Banks"):
        st.markdown("""
        **Fully Tested:** Chase (Credit & Checking), Bank of America, Wells Fargo
        
        **Should Work:** Capital One, Discover, American Express, Citi, US Bank, PNC, and most other US banks
        
        **Tips:**
        - Use official PDF statements downloaded from your bank's website
        - Avoid scanned or photographed statements
        - Multi-page statements are supported
        """)
    
    # Check if we have parse results to display
    # Use a simple flag to control display
    if st.session_state.get('parse_results') and not st.session_state.get('hide_upload_results', False):
        st.success(f"✅ Parsing complete! Results shown below.")
        if st.button("📤 Upload New Statements", type="secondary"):
            print("[STATEMENT_UPLOAD] Clearing parse results")
            # Set flag to hide results and show upload form
            st.session_state.hide_upload_results = True
            st.session_state.skip_api_calls = False  # Clear skip flag
        else:
            st.markdown("---")
            # Display stored results
            display_results(st.session_state.parse_results, current_user)
            return
    else:
        # If flag is set, clear results and reset flag
        if st.session_state.get('hide_upload_results', False):
            st.session_state.hide_upload_results = False
            st.session_state.parse_results = None
            st.session_state.parsed_files = None
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload one or more bank statement PDFs",
        key="statement_uploader"
    )
    
    # Clear skip flag if no file is selected
    if not uploaded_files:
        st.session_state.skip_api_calls = False
    
    if not uploaded_files:
        st.info("👆 Upload PDF bank statements to get started")
        return
    
    # Show uploaded files
    st.markdown(f"### 📁 {len(uploaded_files)} file(s) selected")
    
    for f in uploaded_files:
        col1, col2 = st.columns([3, 1])
        col1.text(f"📄 {f.name}")
        col2.text(f"{f.size / 1024:.1f} KB")
    
    # Parse button
    if st.button("🔍 Parse Statements", type="primary", use_container_width=True):
        print(f"[STATEMENT_UPLOAD] Parse button clicked, {len(uploaded_files)} files")
        # Clear skip flag - parsing is an intentional action
        st.session_state.skip_api_calls = False
        # Store files in session state before parsing
        st.session_state.parsed_files = [f.name for f in uploaded_files]
        parse_and_display_results(uploaded_files, current_user)


def parse_and_display_results(uploaded_files: List, current_user: Dict):
    """Parse uploaded files via API and display results."""
    print(f"[STATEMENT_UPLOAD] Parsing {len(uploaded_files)} files via API")
    
    results = []
    progress_bar = st.progress(0, text="Starting...")
    
    try:
        api = get_api_client()
        
        for i, file in enumerate(uploaded_files):
            progress_bar.progress(
                i / len(uploaded_files),
                text=f"Uploading and parsing {file.name}..."
            )
            
            try:
                # Read file bytes
                file_bytes = file.read()
                print(f"[STATEMENT_UPLOAD] Uploading file: {file.name} ({len(file_bytes)} bytes)")
                
                # Upload and parse via API
                print(f"[STATEMENT_UPLOAD] Calling API: /api/statements/upload")
                result = api.upload_statement(file_bytes, file.name)
                print(f"[STATEMENT_UPLOAD] Upload successful: {result.get('transactions_count', 0)} transactions")
                
                # Convert API response to expected format
                results.append({
                    "filename": file.name,
                    "success": True,
                    "result": result,  # Store API result
                    "error": None,
                    "save_result": result.get("save_result", {})
                })
                
            except Exception as e:
                print(f"[STATEMENT_UPLOAD] Error uploading {file.name}: {str(e)}")
                results.append({
                    "filename": file.name,
                    "success": False,
                    "result": None,
                    "error": str(e),
                    "save_result": None
                })
        
        progress_bar.progress(1.0, text="Complete!")
        
        # Store results in session state
        st.session_state.parse_results = results
        st.session_state.parsed_files = [f.name for f in uploaded_files]
        
        # Display results
        st.divider()
        display_results(results, current_user)
        
    except Exception as e:
        print(f"[STATEMENT_UPLOAD] Error in parse_and_display_results: {str(e)}")
        progress_bar.empty()
        st.error(f"Error processing files: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def display_results(results: List[Dict], current_user: Dict):
    """Display parsing results with options to save."""
    print(f"[STATEMENT_UPLOAD] Displaying {len(results)} results")
    
    st.subheader("📊 Parsing Results")
    
    # Summary metrics
    successful = sum(1 for r in results if r["success"])
    total_txns = sum(r.get("result", {}).get("transactions_count", 0) for r in results if r["success"])
    save_results = [r.get("save_result", {}) for r in results if r.get("save_result")]
    total_saved = sum(sr.get("transactions_saved", 0) for sr in save_results)
    total_duplicated = sum(sr.get("transactions_duplicated", 0) for sr in save_results)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Files Parsed", f"{successful}/{len(results)}")
    col2.metric("Total Transactions", total_txns)
    col3.metric("Saved", total_saved)
    col4.metric("Duplicates Skipped", total_duplicated)
    
    if successful > 0:
        confidences = [r.get("result", {}).get("parsing_confidence", 0) for r in results if r["success"]]
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            st.caption(f"Average Confidence: {avg_conf:.0%}")
    
    # Show each result
    for result in results:
        if result["success"]:
            display_successful_parse(result, current_user)
        else:
            display_failed_parse(result)


def display_successful_parse(result: Dict, current_user: Dict):
    """Display a successfully parsed statement."""
    api_result = result.get("result", {})
    filename = result["filename"]
    
    # Confidence indicator
    confidence = api_result.get("parsing_confidence", 0)
    if confidence >= 0.9:
        conf_icon = "🟢"
    elif confidence >= 0.7:
        conf_icon = "🟡"
    else:
        conf_icon = "🔴"
    
    transactions_count = api_result.get("transactions_count", 0)
    
    with st.expander(
        f"{conf_icon} {filename} - {transactions_count} transactions",
        expanded=True
    ):
        # Account info row
        col1, col2, col3, col4 = st.columns(4)
        
        col1.markdown("**Bank**")
        col1.write(api_result.get("bank_name", "Unknown"))
        
        col2.markdown("**Account Type**")
        col2.write(api_result.get("account_type", "Unknown"))
        
        col3.markdown("**Period**")
        period = api_result.get("statement_period", {})
        if period.get("start") and period.get("end"):
            col3.write(f"{period['start']} to {period['end']}")
        else:
            col3.write("Unknown")
        
        col4.markdown("**Confidence**")
        col4.write(f"{confidence:.0%}")
        
        # Transactions table
        transactions = api_result.get("transactions", [])
        if transactions:
            st.markdown("#### 📋 Transactions")
            
            # Convert to DataFrame for display
            txn_data = []
            for t in transactions:
                txn_data.append({
                    "Date": t.get("date", ""),
                    "Description": t.get("description", ""),
                    "Amount": t.get("amount", 0),
                    "Type": t.get("type", "debit"),
                    "Category": t.get("category", "Uncategorized")
                })
            
            df = pd.DataFrame(txn_data)
            
            # Display table (read-only for now, editing can be added later)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Description": st.column_config.TextColumn("Description", width="large"),
                    "Amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Category": st.column_config.TextColumn("Category", width="medium")
                }
            )
            
            # Totals
            credits = df[df['Type'] == 'credit']['Amount'].sum()
            debits = df[df['Type'] == 'debit']['Amount'].sum()
            
            tcol1, tcol2, tcol3 = st.columns(3)
            tcol1.metric("Total In", f"${credits:,.2f}")
            tcol2.metric("Total Out", f"${debits:,.2f}")
            tcol3.metric("Net", f"${credits - debits:,.2f}")
            
            # Show save status
            save_result = result.get("save_result", {})
            if save_result:
                st.markdown("---")
                if save_result.get('transactions_saved', 0) > 0:
                    st.success(
                        f"✅ **Auto-saved:** {save_result['transactions_saved']} new transactions saved, "
                        f"{save_result.get('transactions_duplicated', 0)} duplicates skipped"
                    )
                else:
                    st.info(
                        f"ℹ️ **Already saved:** All {api_result.get('transactions_count', 0)} transactions were already in the database "
                        f"({save_result.get('transactions_duplicated', 0)} duplicates skipped)"
                    )


def display_failed_parse(result: Dict):
    """Display a failed parsing attempt."""
    with st.expander(f"🔴 {result['filename']} - Failed", expanded=False):
        st.error(f"Error: {result['error']}")
        st.info("""
        **Troubleshooting:**
        - Make sure this is a valid PDF (not a scanned image)
        - Try downloading a fresh copy from your bank
        - Some statement formats may not be supported yet
        """)


def render_history_tab(current_user: Dict):
    """Render the upload history tab."""
    print("[STATEMENT_UPLOAD] Loading upload history")
    user_id = current_user.get('id')
    cache_key = f"upload_history_{user_id}"
    
    # Skip API calls if we're in a file upload operation
    if st.session_state.get('skip_api_calls', False):
        print("[STATEMENT_UPLOAD] Skipping API call (file operation in progress)")
        if cache_key in st.session_state and st.session_state[cache_key]:
            history_data = st.session_state[cache_key]
        else:
            st.info("Loading...")
            return
    
    # Manual refresh button
    col1, col2 = st.columns([1, 10])
    with col1:
        refresh_key = f"refresh_{cache_key}"
        if st.button("🔄", help="Refresh history", key="refresh_history"):
            st.session_state[refresh_key] = True
    
    try:
        # Check if we need to fetch (no data or refresh requested)
        refresh_requested = st.session_state.get(f"refresh_{cache_key}", False)
        
        if cache_key not in st.session_state or st.session_state[cache_key] is None or refresh_requested:
            # Fetch from API
            history_data = _fetch_upload_history(user_id)
            st.session_state[cache_key] = history_data
            st.session_state[f"refresh_{cache_key}"] = False
        else:
            # Use cached data from session state
            history_data = st.session_state[cache_key]
            print("[STATEMENT_UPLOAD] Using cached history from session state")
        
        history = history_data.get("history", [])
        
        if not history:
            st.info("No upload history yet. Upload your first statement!")
            return
        
        st.subheader("📋 Upload History")
        
        # Display as table
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Summary stats
        st.markdown("---")
        col1, col2 = st.columns(2)
        col1.metric("Total Uploads", len(history))
        col2.metric("Total Transactions", sum(d.get("transactions", 0) for d in history))
        
    except Exception as e:
        print(f"[STATEMENT_UPLOAD] Error loading history: {str(e)}")
        st.error(f"Error loading upload history: {str(e)}")
