# # """
# # views/pdf_upload.py

# # Streamlit view for uploading and parsing bank statement PDFs.
# # Integrates with the Smart Expense Analyzer's existing architecture.
# # """
# # import sys
# # from pathlib import Path

# # # Add the project root to Python path so we can import from src/
# # project_root = Path(__file__).parent.parent
# # sys.path.insert(0, str(project_root))


# # import streamlit as st
# # import pandas as pd
# # from datetime import datetime
# # from decimal import Decimal
# # import json
# # import os
# # from pathlib import Path

# # # Import your existing modules
# # from src.config import Config
# # from src.database import get_db, save_transactions
# # from src.services.statement_parser import EnhancedStatementParser, ParsedStatement


# # def render_pdf_upload_view():
# #     """Main view for PDF statement upload and parsing."""
    
# #     st.header("📄 Upload Bank Statements")
# #     st.caption("Upload PDF statements as a backup to Plaid or for banks not supported by Plaid")
    
# #     # Check for API key
# #     if not settings.GEMINI_API_KEY:
# #         st.error("⚠️ Gemini API key not configured. Add GEMINI_API_KEY to your .env file.")
# #         return
    
# #     # Initialize parser
# #     parser = get_parser()
    
# #     # Create tabs for different upload options
# #     tab1, tab2 = st.tabs(["📤 Upload New", "📋 Upload History"])
    
# #     with tab1:
# #         render_upload_section(parser)
    
# #     with tab2:
# #         render_upload_history()


# # @st.cache_resource
# # def get_parser():
# #     """Cache the parser instance."""
# #     from config import settings
# #     return EnhancedStatementParser(settings.GEMINI_API_KEY)


# # def render_upload_section(parser: EnhancedStatementParser):
# #     """Render the file upload and parsing section."""
    
# #     # File uploader
# #     uploaded_files = st.file_uploader(
# #         "Choose PDF files",
# #         type=['pdf'],
# #         accept_multiple_files=True,
# #         help="Upload bank or credit card statement PDFs. Supports Chase, Bank of America, Wells Fargo, and more."
# #     )
    
# #     if not uploaded_files:
# #         # Show supported banks info
# #         with st.expander("ℹ️ Supported Banks & Formats"):
# #             st.markdown("""
# #             **Fully Tested:**
# #             - Chase (Checking, Credit Cards)
# #             - Bank of America
# #             - Wells Fargo
            
# #             **Should Work (LLM-based parsing):**
# #             - Capital One
# #             - Discover
# #             - American Express
# #             - Most US bank statements
            
# #             **Tips for best results:**
# #             - Use official PDF statements downloaded from your bank
# #             - Avoid scanned/photographed statements if possible
# #             - Multi-page statements are supported
# #             """)
# #         return
    
# #     # Show uploaded files
# #     st.subheader(f"📁 {len(uploaded_files)} file(s) ready to parse")
    
# #     # Preview uploaded files
# #     file_info = []
# #     for f in uploaded_files:
# #         file_info.append({
# #             "Filename": f.name,
# #             "Size": f"{f.size / 1024:.1f} KB",
# #             "Status": "Ready"
# #         })
    
# #     st.dataframe(pd.DataFrame(file_info), use_container_width=True, hide_index=True)
    
# #     # Parse options
# #     col1, col2 = st.columns(2)
# #     with col1:
# #         auto_categorize = st.checkbox(
# #             "Auto-categorize transactions", 
# #             value=True,
# #             help="Use AI to categorize transactions (recommended)"
# #         )
# #     with col2:
# #         save_to_db = st.checkbox(
# #             "Save to database",
# #             value=True,
# #             help="Store transactions for analysis"
# #         )
    
# #     # Parse button
# #     if st.button("🔍 Parse Statements", type="primary", use_container_width=True):
# #         parse_uploaded_files(uploaded_files, parser, auto_categorize, save_to_db)


# # def parse_uploaded_files(
# #     uploaded_files: list,
# #     parser: EnhancedStatementParser,
# #     auto_categorize: bool,
# #     save_to_db: bool
# # ):
# #     """Parse all uploaded files and display results."""
    
# #     results = []
# #     progress_bar = st.progress(0, text="Starting...")
    
# #     for i, file in enumerate(uploaded_files):
# #         progress_bar.progress(
# #             (i) / len(uploaded_files),
# #             text=f"Parsing {file.name}..."
# #         )
        
# #         try:
# #             # Read file bytes
# #             file_bytes = file.read()
            
# #             # Parse the statement
# #             result = parser.parse_pdf(file_bytes)
            
# #             results.append({
# #                 "filename": file.name,
# #                 "success": True,
# #                 "result": result,
# #                 "error": None
# #             })
            
# #         except Exception as e:
# #             results.append({
# #                 "filename": file.name,
# #                 "success": False,
# #                 "result": None,
# #                 "error": str(e)
# #             })
    
# #     progress_bar.progress(1.0, text="Complete!")
    
# #     # Display results
# #     display_parsing_results(results, auto_categorize, save_to_db)


# # def display_parsing_results(
# #     results: list,
# #     auto_categorize: bool,
# #     save_to_db: bool
# # ):
# #     """Display parsed results with options to review and save."""
    
# #     st.divider()
# #     st.subheader("📊 Parsing Results")
    
# #     # Summary metrics
# #     successful = sum(1 for r in results if r["success"])
# #     total_transactions = sum(
# #         len(r["result"].transactions) for r in results if r["success"]
# #     )
    
# #     col1, col2, col3 = st.columns(3)
# #     col1.metric("Files Parsed", f"{successful}/{len(results)}")
# #     col2.metric("Total Transactions", total_transactions)
    
# #     avg_confidence = 0
# #     if successful > 0:
# #         avg_confidence = sum(
# #             r["result"].parsing_confidence for r in results if r["success"]
# #         ) / successful
# #     col3.metric("Avg Confidence", f"{avg_confidence:.0%}")
    
# #     # Show each result
# #     for result in results:
# #         if result["success"]:
# #             render_successful_result(result, auto_categorize, save_to_db)
# #         else:
# #             render_failed_result(result)


# # def render_successful_result(
# #     result: dict,
# #     auto_categorize: bool,
# #     save_to_db: bool
# # ):
# #     """Render a successfully parsed statement."""
    
# #     parsed: ParsedStatement = result["result"]
# #     filename = result["filename"]
    
# #     # Determine confidence color
# #     if parsed.parsing_confidence >= 0.9:
# #         confidence_color = "🟢"
# #     elif parsed.parsing_confidence >= 0.7:
# #         confidence_color = "🟡"
# #     else:
# #         confidence_color = "🔴"
    
# #     with st.expander(
# #         f"{confidence_color} {filename} - {len(parsed.transactions)} transactions",
# #         expanded=True
# #     ):
# #         # Account info
# #         col1, col2, col3, col4 = st.columns(4)
        
# #         with col1:
# #             st.markdown("**Bank**")
# #             st.write(parsed.account_info.bank_name or "Unknown")
        
# #         with col2:
# #             st.markdown("**Account Type**")
# #             st.write(parsed.account_info.account_type or "Unknown")
        
# #         with col3:
# #             st.markdown("**Period**")
# #             if parsed.account_info.statement_start_date:
# #                 period = f"{parsed.account_info.statement_start_date} to {parsed.account_info.statement_end_date}"
# #             else:
# #                 period = "Unknown"
# #             st.write(period)
        
# #         with col4:
# #             st.markdown("**Confidence**")
# #             st.write(f"{parsed.parsing_confidence:.0%}")
        
# #         # Summary based on account type
# #         if parsed.credit_card_summary:
# #             render_credit_card_summary(parsed.credit_card_summary)
# #         elif parsed.checking_summary:
# #             render_checking_summary(parsed.checking_summary)
        
# #         # Transactions table
# #         if parsed.transactions:
# #             st.markdown("#### Transactions")
            
# #             # Convert to DataFrame
# #             df = transactions_to_dataframe(parsed.transactions)
            
# #             # Add editing capability
# #             edited_df = st.data_editor(
# #                 df,
# #                 use_container_width=True,
# #                 hide_index=True,
# #                 column_config={
# #                     "date": st.column_config.DateColumn("Date"),
# #                     "description": st.column_config.TextColumn("Description", width="large"),
# #                     "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
# #                     "transaction_type": st.column_config.SelectboxColumn(
# #                         "Type",
# #                         options=["credit", "debit"],
# #                         width="small"
# #                     ),
# #                     "category": st.column_config.SelectboxColumn(
# #                         "Category",
# #                         options=get_category_options(),
# #                         width="medium"
# #                     )
# #                 },
# #                 num_rows="dynamic"
# #             )
            
# #             # Totals
# #             credits = edited_df[edited_df['transaction_type'] == 'credit']['amount'].sum()
# #             debits = edited_df[edited_df['transaction_type'] == 'debit']['amount'].sum()
            
# #             tcol1, tcol2, tcol3 = st.columns(3)
# #             tcol1.metric("Total Credits", f"${credits:,.2f}")
# #             tcol2.metric("Total Debits", f"${debits:,.2f}")
# #             tcol3.metric("Net", f"${credits - debits:,.2f}")
            
# #             # Save button
# #             if save_to_db:
# #                 if st.button(f"💾 Save to Database", key=f"save_{filename}"):
# #                     save_parsed_transactions(edited_df, parsed.account_info, filename)
        
# #         # Parsing notes
# #         if parsed.parsing_notes:
# #             st.markdown("#### ⚠️ Parsing Notes")
# #             for note in parsed.parsing_notes:
# #                 st.warning(note)


# # def render_credit_card_summary(summary):
# #     """Render credit card summary section."""
# #     st.markdown("#### Account Summary")
    
# #     cols = st.columns(4)
    
# #     if summary.previous_balance is not None:
# #         cols[0].metric("Previous Balance", f"${summary.previous_balance:,.2f}")
# #     if summary.new_balance is not None:
# #         cols[1].metric("New Balance", f"${summary.new_balance:,.2f}")
# #     if summary.minimum_payment is not None:
# #         cols[2].metric("Minimum Payment", f"${summary.minimum_payment:,.2f}")
# #     if summary.payment_due_date:
# #         cols[3].metric("Due Date", str(summary.payment_due_date))


# # def render_checking_summary(summary):
# #     """Render checking account summary section."""
# #     st.markdown("#### Account Summary")
    
# #     cols = st.columns(4)
    
# #     if summary.beginning_balance is not None:
# #         cols[0].metric("Beginning Balance", f"${summary.beginning_balance:,.2f}")
# #     if summary.ending_balance is not None:
# #         cols[1].metric("Ending Balance", f"${summary.ending_balance:,.2f}")
# #     if summary.deposits_additions is not None:
# #         cols[2].metric("Deposits", f"${summary.deposits_additions:,.2f}")
# #     if summary.withdrawals is not None:
# #         cols[3].metric("Withdrawals", f"${summary.withdrawals:,.2f}")


# # def render_failed_result(result: dict):
# #     """Render a failed parsing attempt."""
# #     with st.expander(f"🔴 {result['filename']} - Failed", expanded=False):
# #         st.error(f"Error: {result['error']}")
# #         st.info("Try re-uploading the file or use a different statement format.")


# # def transactions_to_dataframe(transactions: list) -> pd.DataFrame:
# #     """Convert Transaction objects to DataFrame."""
# #     data = []
# #     for t in transactions:
# #         data.append({
# #             "date": t.date,
# #             "description": t.description,
# #             "amount": float(t.amount),
# #             "transaction_type": t.transaction_type.value,
# #             "category": t.category or "Uncategorized",
# #             "location": t.location or "",
# #             "is_recurring": t.is_recurring
# #         })
# #     return pd.DataFrame(data)


# # def get_category_options() -> list:
# #     """Get list of transaction categories."""
# #     return [
# #         "Uncategorized",
# #         "Groceries",
# #         "Dining",
# #         "Transportation",
# #         "Gas/Fuel",
# #         "Shopping",
# #         "Entertainment",
# #         "Subscriptions",
# #         "Utilities",
# #         "Rent/Mortgage",
# #         "Healthcare",
# #         "Personal Care",
# #         "Travel",
# #         "Education",
# #         "Income",
# #         "Transfer",
# #         "Fees",
# #         "Other"
# #     ]


# # def save_parsed_transactions(
# #     df: pd.DataFrame,
# #     account_info,
# #     filename: str
# # ):
# #     """Save parsed transactions to the database."""
# #     try:
# #         # Convert DataFrame back to transaction records
# #         transactions = []
# #         for _, row in df.iterrows():
# #             transactions.append({
# #                 "date": str(row["date"]),
# #                 "description": row["description"],
# #                 "amount": row["amount"],
# #                 "transaction_type": row["transaction_type"],
# #                 "category": row["category"],
# #                 "source": "pdf_upload",
# #                 "source_file": filename,
# #                 "bank_name": account_info.bank_name,
# #                 "account_type": account_info.account_type
# #             })
        
# #         # Save to database (using your existing database module)
# #         save_transactions(transactions)
        
# #         # Also log the upload
# #         log_upload(filename, len(transactions), account_info)
        
# #         st.success(f"✅ Saved {len(transactions)} transactions to database!")
        
# #     except Exception as e:
# #         st.error(f"Failed to save: {str(e)}")


# # def log_upload(filename: str, transaction_count: int, account_info):
# #     """Log the upload to history."""
# #     history_file = Path("data/upload_history.json")
# #     history_file.parent.mkdir(exist_ok=True)
    
# #     # Load existing history
# #     if history_file.exists():
# #         with open(history_file) as f:
# #             history = json.load(f)
# #     else:
# #         history = []
    
# #     # Add new entry
# #     history.append({
# #         "filename": filename,
# #         "uploaded_at": datetime.now().isoformat(),
# #         "transaction_count": transaction_count,
# #         "bank_name": account_info.bank_name,
# #         "account_type": account_info.account_type
# #     })
    
# #     # Save back
# #     with open(history_file, "w") as f:
# #         json.dump(history, f, indent=2)


# # def render_upload_history():
# #     """Render the upload history tab."""
# #     history_file = Path("data/upload_history.json")
    
# #     if not history_file.exists():
# #         st.info("No upload history yet. Upload your first statement!")
# #         return
    
# #     with open(history_file) as f:
# #         history = json.load(f)
    
# #     if not history:
# #         st.info("No upload history yet.")
# #         return
    
# #     st.subheader("📋 Previous Uploads")
    
# #     # Convert to DataFrame and display
# #     df = pd.DataFrame(history)
# #     df['uploaded_at'] = pd.to_datetime(df['uploaded_at']).dt.strftime('%Y-%m-%d %H:%M')
    
# #     st.dataframe(
# #         df[['filename', 'uploaded_at', 'transaction_count', 'bank_name', 'account_type']],
# #         use_container_width=True,
# #         hide_index=True,
# #         column_config={
# #             "filename": "File",
# #             "uploaded_at": "Uploaded",
# #             "transaction_count": "Transactions",
# #             "bank_name": "Bank",
# #             "account_type": "Account Type"
# #         }
# #     )
    
# #     # Summary
# #     total_uploads = len(history)
# #     total_transactions = sum(h['transaction_count'] for h in history)
    
# #     col1, col2 = st.columns(2)
# #     col1.metric("Total Uploads", total_uploads)
# #     col2.metric("Total Transactions", total_transactions)


# # # Entry point for the view
# # if __name__ == "__main__":
# #     render_pdf_upload_view()

# """
# Statement Upload View for Smart Expense Analyzer
# Handles PDF bank statement uploads and parsing.

# Place this file at: views/statement_upload.py
# """

# import streamlit as st
# import pandas as pd
# from typing import Dict, List
# from datetime import datetime

# # Import config - matching YOUR project structure
# from src.config import Config

# # NOTE: We do NOT import get_db or save_transactions
# # The db object is passed as a parameter to show_statement_upload()


# def show_statement_upload(db, current_user: Dict):
#     """Main view for uploading and parsing bank statements."""
    
#     st.header("📄 Upload Bank Statements")
#     st.caption("Upload PDF statements from any bank as a backup to Plaid")
    
#     # Check for required packages
#     try:
#         import pdfplumber
#         import google.generativeai
#     except ImportError as e:
#         st.error("⚠️ Missing required packages!")
#         st.code("pip install pdfplumber google-generativeai pydantic", language="bash")
#         return
    
#     # Check for Gemini API key
#     if not Config.GEMINI_API_KEY:
#         st.error("⚠️ Gemini API key not configured!")
#         st.markdown("""
#         To use PDF parsing, add your Gemini API key to `.env`:
#         ```
#         GEMINI_API_KEY=your_api_key_here
#         ```
#         Get a free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
#         """)
#         return
    
#     # Create tabs
#     tab1, tab2 = st.tabs(["📤 Upload New", "📋 Upload History"])
    
#     with tab1:
#         render_upload_tab(db, current_user)
    
#     with tab2:
#         render_history_tab(db, current_user)


# def render_upload_tab(db, current_user: Dict):
#     """Render the file upload and parsing interface."""
    
#     # Initialize parser in session state
#     if 'statement_parser' not in st.session_state:
#         try:
#             from src.services.statement_parser import StatementParser
#             st.session_state.statement_parser = StatementParser(Config.GEMINI_API_KEY)
#             st.session_state.parser_error = None
#         except Exception as e:
#             st.session_state.statement_parser = None
#             st.session_state.parser_error = str(e)
    
#     if st.session_state.get('parser_error'):
#         st.error(f"Failed to initialize parser: {st.session_state.parser_error}")
#         st.info("Make sure you have created `src/services/statement_parser.py` and `src/services/pii_sanitizer.py`")
#         return
    
#     if not st.session_state.get('statement_parser'):
#         st.error("Parser not available")
#         return
    
#     parser = st.session_state.statement_parser
    
#     # Supported banks info
#     with st.expander("ℹ️ Supported Banks"):
#         st.markdown("""
#         **Fully Tested:** Chase (Credit & Checking), Bank of America, Wells Fargo
        
#         **Should Work:** Capital One, Discover, American Express, Citi, US Bank, PNC, and most other US banks
        
#         **Tips:**
#         - Use official PDF statements downloaded from your bank's website
#         - Avoid scanned or photographed statements
#         - Multi-page statements are supported
#         """)
    
#     # File uploader
#     uploaded_files = st.file_uploader(
#         "Choose PDF files",
#         type=['pdf'],
#         accept_multiple_files=True,
#         help="Upload one or more bank statement PDFs"
#     )
    
#     if not uploaded_files:
#         st.info("👆 Upload PDF bank statements to get started")
#         return
    
#     # Show uploaded files
#     st.markdown(f"### 📁 {len(uploaded_files)} file(s) selected")
    
#     for f in uploaded_files:
#         col1, col2 = st.columns([3, 1])
#         col1.text(f"📄 {f.name}")
#         col2.text(f"{f.size / 1024:.1f} KB")
    
#     # Parse button
#     if st.button("🔍 Parse Statements", type="primary", use_container_width=True):
#         parse_and_display_results(uploaded_files, parser, db, current_user)


# def parse_and_display_results(uploaded_files: List, parser, db, current_user: Dict):
#     """Parse uploaded files and display results."""
    
#     results = []
#     progress_bar = st.progress(0, text="Starting...")
    
#     for i, file in enumerate(uploaded_files):
#         progress_bar.progress(
#             i / len(uploaded_files),
#             text=f"Parsing {file.name}..."
#         )
        
#         try:
#             # Read file bytes
#             file_bytes = file.read()
            
#             # Parse the statement
#             parsed = parser.parse_with_retry(file_bytes, file.name)
            
#             results.append({
#                 "filename": file.name,
#                 "success": True,
#                 "parsed": parsed,
#                 "error": None
#             })
            
#         except Exception as e:
#             results.append({
#                 "filename": file.name,
#                 "success": False,
#                 "parsed": None,
#                 "error": str(e)
#             })
    
#     progress_bar.progress(1.0, text="Complete!")
    
#     # Display results
#     st.divider()
#     display_results(results, db, current_user)


# def display_results(results: List[Dict], db, current_user: Dict):
#     """Display parsing results with options to save."""
    
#     st.subheader("📊 Parsing Results")
    
#     # Summary metrics
#     successful = sum(1 for r in results if r["success"])
#     total_txns = sum(len(r["parsed"].transactions) for r in results if r["success"])
    
#     col1, col2, col3 = st.columns(3)
#     col1.metric("Files Parsed", f"{successful}/{len(results)}")
#     col2.metric("Total Transactions", total_txns)
    
#     if successful > 0:
#         avg_conf = sum(r["parsed"].parsing_confidence for r in results if r["success"]) / successful
#         col3.metric("Avg Confidence", f"{avg_conf:.0%}")
    
#     # Show each result
#     for result in results:
#         if result["success"]:
#             display_successful_parse(result, db, current_user)
#         else:
#             display_failed_parse(result)


# def display_successful_parse(result: Dict, db, current_user: Dict):
#     """Display a successfully parsed statement."""
    
#     parsed = result["parsed"]
#     filename = result["filename"]
    
#     # Confidence indicator
#     if parsed.parsing_confidence >= 0.9:
#         conf_icon = "🟢"
#     elif parsed.parsing_confidence >= 0.7:
#         conf_icon = "🟡"
#     else:
#         conf_icon = "🔴"
    
#     with st.expander(
#         f"{conf_icon} {filename} - {len(parsed.transactions)} transactions",
#         expanded=True
#     ):
#         # Account info row
#         col1, col2, col3, col4 = st.columns(4)
        
#         col1.markdown("**Bank**")
#         col1.write(parsed.account_info.bank_name or "Unknown")
        
#         col2.markdown("**Account Type**")
#         acc_type = parsed.account_info.account_type
#         col2.write(acc_type.value if hasattr(acc_type, 'value') else str(acc_type) or "Unknown")
        
#         col3.markdown("**Period**")
#         if parsed.account_info.statement_start_date and parsed.account_info.statement_end_date:
#             col3.write(f"{parsed.account_info.statement_start_date} to {parsed.account_info.statement_end_date}")
#         else:
#             col3.write("Unknown")
        
#         col4.markdown("**Confidence**")
#         col4.write(f"{parsed.parsing_confidence:.0%}")
        
#         # Summary section
#         render_summary(parsed)
        
#         # Transactions table
#         if parsed.transactions:
#             st.markdown("#### 📋 Transactions")
            
#             # Convert to DataFrame for editing
#             txn_data = []
#             for t in parsed.transactions:
#                 t_type = t.transaction_type
#                 txn_data.append({
#                     "Date": str(t.date),
#                     "Description": t.description,
#                     "Amount": t.amount,
#                     "Type": t_type.value if hasattr(t_type, 'value') else str(t_type),
#                     "Category": t.category or "Uncategorized"
#                 })
            
#             df = pd.DataFrame(txn_data)
            
#             # Editable table
#             edited_df = st.data_editor(
#                 df,
#                 use_container_width=True,
#                 hide_index=True,
#                 column_config={
#                     "Date": st.column_config.TextColumn("Date", width="small"),
#                     "Description": st.column_config.TextColumn("Description", width="large"),
#                     "Amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
#                     "Type": st.column_config.SelectboxColumn(
#                         "Type",
#                         options=["credit", "debit"],
#                         width="small"
#                     ),
#                     "Category": st.column_config.SelectboxColumn(
#                         "Category",
#                         options=get_category_options(),
#                         width="medium"
#                     )
#                 },
#                 num_rows="fixed"
#             )
            
#             # Totals
#             credits = edited_df[edited_df['Type'] == 'credit']['Amount'].sum()
#             debits = edited_df[edited_df['Type'] == 'debit']['Amount'].sum()
            
#             tcol1, tcol2, tcol3 = st.columns(3)
#             tcol1.metric("Total In", f"${credits:,.2f}")
#             tcol2.metric("Total Out", f"${debits:,.2f}")
#             tcol3.metric("Net", f"${credits - debits:,.2f}")
            
#             # Save button
#             st.markdown("---")
#             if st.button(f"💾 Save {len(parsed.transactions)} Transactions", key=f"save_{filename}", type="primary"):
#                 save_parsed_statement(parsed, edited_df, db, current_user, filename)
        
#         # Parsing notes
#         if parsed.parsing_notes:
#             st.markdown("#### ⚠️ Notes")
#             for note in parsed.parsing_notes:
#                 st.warning(note)


# def render_summary(parsed):
#     """Render the statement summary section."""
#     summary = parsed.summary
#     account_type = parsed.account_info.account_type
    
#     st.markdown("#### 📊 Statement Summary")
    
#     # Get account type value
#     acc_type_val = account_type.value if hasattr(account_type, 'value') else str(account_type)
    
#     if acc_type_val == "credit_card":
#         # Credit card summary
#         cols = st.columns(4)
#         if hasattr(summary, 'previous_balance') and summary.previous_balance is not None:
#             cols[0].metric("Previous Balance", f"${summary.previous_balance:,.2f}")
#         if hasattr(summary, 'new_balance') and summary.new_balance is not None:
#             cols[1].metric("New Balance", f"${summary.new_balance:,.2f}")
#         if hasattr(summary, 'minimum_payment') and summary.minimum_payment is not None:
#             cols[2].metric("Minimum Payment", f"${summary.minimum_payment:,.2f}")
#         if hasattr(summary, 'payment_due_date') and summary.payment_due_date:
#             cols[3].metric("Due Date", str(summary.payment_due_date))
#     else:
#         # Checking/savings summary
#         cols = st.columns(4)
#         if hasattr(summary, 'beginning_balance') and summary.beginning_balance is not None:
#             cols[0].metric("Beginning Balance", f"${summary.beginning_balance:,.2f}")
#         if hasattr(summary, 'ending_balance') and summary.ending_balance is not None:
#             cols[1].metric("Ending Balance", f"${summary.ending_balance:,.2f}")
#         if hasattr(summary, 'total_deposits') and summary.total_deposits is not None:
#             cols[2].metric("Deposits", f"${summary.total_deposits:,.2f}")
#         if hasattr(summary, 'total_withdrawals') and summary.total_withdrawals is not None:
#             cols[3].metric("Withdrawals", f"${summary.total_withdrawals:,.2f}")


# def get_category_options() -> list:
#     """Get list of transaction categories."""
#     return [
#         "Uncategorized",
#         "Groceries",
#         "Dining & Restaurants",
#         "Transportation",
#         "Gas & Fuel",
#         "Shopping",
#         "Entertainment",
#         "Subscriptions",
#         "Utilities",
#         "Rent & Mortgage",
#         "Healthcare",
#         "Personal Care",
#         "Travel",
#         "Education",
#         "Income",
#         "Transfer",
#         "Fees & Charges",
#         "Other"
#     ]


# def save_parsed_statement(parsed, edited_df: pd.DataFrame, db, current_user: Dict, filename: str):
#     """Save parsed transactions to the database."""
    
#     try:
#         user_id = current_user["id"]
        
#         # Create a virtual account for this PDF upload
#         import hashlib
#         account_id = f"pdf_{hashlib.md5(f'{user_id}_{filename}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
#         # Save account
#         account_data = {
#             "account_id": account_id,
#             "name": f"{parsed.account_info.bank_name or 'Unknown'} - PDF Upload",
#             "institution_name": parsed.account_info.bank_name or "PDF Upload",
#             "type": parsed.account_info.account_type.value if hasattr(parsed.account_info.account_type, 'value') else "unknown",
#             "subtype": "pdf_upload",
#             "mask": parsed.account_info.account_number_last4 or "****",
#             "source": "pdf_upload",
#             "current_balance": None,
#             "available_balance": None
#         }
        
#         db.save_bank_account(user_id, account_data)
        
#         # Convert edited DataFrame to transactions
#         transactions = []
#         for i, row in edited_df.iterrows():
#             orig_txn = parsed.transactions[i] if i < len(parsed.transactions) else None
            
#             # Plaid format: positive = spent, negative = received
#             amount = float(row["Amount"])
#             if row["Type"] == "credit":
#                 plaid_amount = -amount  # Money in = negative
#             else:
#                 plaid_amount = amount   # Money out = positive
            
#             txn = {
#                 "transaction_id": orig_txn.transaction_id if orig_txn else f"pdf_{i}_{datetime.now().timestamp()}",
#                 "account_id": account_id,
#                 "amount": plaid_amount,
#                 "date": row["Date"],
#                 "name": row["Description"],
#                 "merchant_name": row["Description"].split()[0] if row["Description"] else None,
#                 "category": [row["Category"]],
#                 "pending": False,
#                 "payment_channel": "other",
#                 "transaction_type": "place" if row["Type"] == "debit" else "credit",
#                 "source": "pdf_upload"
#             }
#             transactions.append(txn)
        
#         # Save transactions using existing db method
#         new_count = db.save_transactions(user_id, account_id, transactions)
        
#         st.success(f"✅ Saved {new_count} new transactions!")
#         st.balloons()
        
#     except Exception as e:
#         st.error(f"Failed to save: {str(e)}")
#         import traceback
#         st.code(traceback.format_exc())


# def display_failed_parse(result: Dict):
#     """Display a failed parsing attempt."""
#     with st.expander(f"🔴 {result['filename']} - Failed", expanded=False):
#         st.error(f"Error: {result['error']}")
#         st.info("""
#         **Troubleshooting:**
#         - Make sure this is a valid PDF (not a scanned image)
#         - Try downloading a fresh copy from your bank
#         - Some statement formats may not be supported yet
#         """)


# def render_history_tab(db, current_user: Dict):
#     """Render the upload history tab."""
    
#     # Get all accounts that are from PDF uploads
#     accounts = db.get_user_accounts(current_user["id"])
#     pdf_accounts = [a for a in accounts if a.get("source") == "pdf_upload"]
    
#     if not pdf_accounts:
#         st.info("No upload history yet. Upload your first statement!")
#         return
    
#     st.subheader("📋 Upload History")
    
#     # Display as table
#     data = []
#     for acc in pdf_accounts:
#         transactions = db.get_transactions(current_user["id"], acc.get("account_id"))
#         data.append({
#             "Bank": acc.get("institution_name", "Unknown"),
#             "Account": acc.get("name", "Unknown"),
#             "Transactions": len(transactions),
#             "Created": acc.get("created_at", "")[:10] if acc.get("created_at") else "Unknown"
#         })
    
#     df = pd.DataFrame(data)
#     st.dataframe(df, use_container_width=True, hide_index=True)
    
#     # Summary stats
#     st.markdown("---")
#     col1, col2 = st.columns(2)
#     col1.metric("Total Uploads", len(pdf_accounts))
#     col2.metric("Total Transactions", sum(d["Transactions"] for d in data))


"""
Statement Upload View for Smart Expense Analyzer
Handles PDF bank statement uploads and parsing.

Place this file at: views/statement_upload.py
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from datetime import datetime

# Import config - matching YOUR project structure
# from src.config import Config

from pathlib import Path
import os
from dotenv import load_dotenv
config_path=Path(__file__).parent.parent.parent/'src'/'config'
print(config_path)

# Import config - matching YOUR project structure
# from src.config import Config
from src.config import Config
# print(Config)
# NOTE: We do NOT import get_db or save_transactions
# The db object is passed as a parameter to show_statement_upload()


def show_statement_upload(db, current_user: Dict):
    """Main view for uploading and parsing bank statements."""
    
    st.header("📄 Upload Bank Statements")
    st.caption("Upload PDF statements from any bank as a backup to Plaid")
    
    # Check for required packages
    try:
        import pdfplumber
        import google.generativeai
    except ImportError as e:
        st.error("⚠️ Missing required packages!")
        st.code("pip install pdfplumber google-generativeai pydantic", language="bash")
        return
    
    # Check for Gemini API key
    if not Config.GEMINI_API_KEY:
        st.error("⚠️ Gemini API key not configured!")
        st.markdown("""
        To use PDF parsing, add your Gemini API key to `.env`:
```
        GEMINI_API_KEY=your_api_key_here
```
        Get a free API key at [Google AI Studio](https://makersuite.google.com/app/apikey)
        """)
        return
    
    # Create tabs
    tab1, tab2 = st.tabs(["📤 Upload New", "📋 Upload History"])
    
    with tab1:
        render_upload_tab(db, current_user)
    
    with tab2:
        render_history_tab(db, current_user)


def render_upload_tab(db, current_user: Dict):
    """Render the file upload and parsing interface."""
    
    # Initialize parser in session state
    if 'statement_parser' not in st.session_state:
        try:
            from src.services.statement_parser import StatementParser
            st.session_state.statement_parser = StatementParser(Config.GEMINI_API_KEY)
            st.session_state.parser_error = None
        except Exception as e:
            st.session_state.statement_parser = None
            st.session_state.parser_error = str(e)
    
    if st.session_state.get('parser_error'):
        st.error(f"Failed to initialize parser: {st.session_state.parser_error}")
        st.info("Make sure you have created `src/services/statement_parser.py` and `src/services/pii_sanitizer.py`")
        return
    
    if not st.session_state.get('statement_parser'):
        st.error("Parser not available")
        return
    
    parser = st.session_state.statement_parser
    
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
    if st.session_state.get('parse_results'):
        st.success(f"✅ Parsing complete! Results shown below.")
        if st.button("📤 Upload New Statements", type="secondary"):
            # Clear all session state related to parsing
            st.session_state.parsed_files = None
            st.session_state.parse_results = None
            # Clear the file uploader state to reset the widget
            if 'statement_uploader' in st.session_state:
                del st.session_state.statement_uploader
            st.rerun()
        st.markdown("---")
        # Display stored results
        display_results(st.session_state.parse_results, db, current_user)
        return
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload one or more bank statement PDFs",
        key="statement_uploader"
    )
    
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
        # Store files in session state before parsing
        st.session_state.parsed_files = [f.name for f in uploaded_files]
        parse_and_display_results(uploaded_files, parser, db, current_user)
        # Trigger rerun to refresh the page (files will be cleared from view)
        st.rerun()


def parse_and_display_results(uploaded_files: List, parser, db, current_user: Dict):
    """Parse uploaded files and display results."""
    
    results = []
    progress_bar = st.progress(0, text="Starting...")
    
    for i, file in enumerate(uploaded_files):
        progress_bar.progress(
            i / len(uploaded_files),
            text=f"Parsing {file.name}..."
        )
        
        try:
            # Read file bytes
            file_bytes = file.read()
            
            # Parse the statement
            parsed = parser.parse_with_retry(file_bytes, file.name)
            
            # Automatically save transactions to database
            save_result = None
            try:
                from src.services.statement_transaction_saver import save_parsed_statement_transactions
                save_result = save_parsed_statement_transactions(
                    parsed, db, current_user["id"], file.name, auto_create_account=True
                )
            except Exception as save_error:
                # Log error but don't fail the parsing
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to auto-save transactions for {file.name}: {str(save_error)}")
            
            results.append({
                "filename": file.name,
                "success": True,
                "parsed": parsed,
                "error": None,
                "save_result": save_result
            })
            
        except Exception as e:
            results.append({
                "filename": file.name,
                "success": False,
                "parsed": None,
                "error": str(e),
                "save_result": None
            })
    
    progress_bar.progress(1.0, text="Complete!")
    
    # Store results in session state so they persist after rerun
    st.session_state.parse_results = results
    st.session_state.parsed_files = [f.name for f in uploaded_files]
    
    # Display results
    st.divider()
    display_results(results, db, current_user)


def display_results(results: List[Dict], db, current_user: Dict):
    """Display parsing results with options to save."""
    
    st.subheader("📊 Parsing Results")
    
    # Summary metrics
    successful = sum(1 for r in results if r["success"])
    total_txns = sum(len(r["parsed"].transactions) for r in results if r["success"])
    total_saved = sum(r.get("save_result", {}).get("transactions_saved", 0) for r in results if r.get("save_result"))
    total_duplicated = sum(r.get("save_result", {}).get("transactions_duplicated", 0) for r in results if r.get("save_result"))
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Files Parsed", f"{successful}/{len(results)}")
    col2.metric("Total Transactions", total_txns)
    col3.metric("Saved", total_saved)
    col4.metric("Duplicates Skipped", total_duplicated)
    
    if successful > 0:
        avg_conf = sum(r["parsed"].parsing_confidence for r in results if r["success"]) / successful
        st.caption(f"Average Confidence: {avg_conf:.0%}")
    
    # Show each result
    for result in results:
        if result["success"]:
            display_successful_parse(result, db, current_user)
        else:
            display_failed_parse(result)


def display_successful_parse(result: Dict, db, current_user: Dict):
    """Display a successfully parsed statement."""
    
    parsed = result["parsed"]
    filename = result["filename"]
    
    # Confidence indicator
    if parsed.parsing_confidence >= 0.9:
        conf_icon = "🟢"
    elif parsed.parsing_confidence >= 0.7:
        conf_icon = "🟡"
    else:
        conf_icon = "🔴"
    
    with st.expander(
        f"{conf_icon} {filename} - {len(parsed.transactions)} transactions",
        expanded=True
    ):
        # Account info row
        col1, col2, col3, col4 = st.columns(4)
        
        col1.markdown("**Bank**")
        col1.write(parsed.account_info.bank_name or "Unknown")
        
        col2.markdown("**Account Type**")
        acc_type = parsed.account_info.account_type
        col2.write(acc_type.value if hasattr(acc_type, 'value') else str(acc_type) or "Unknown")
        
        col3.markdown("**Period**")
        if parsed.account_info.statement_start_date and parsed.account_info.statement_end_date:
            col3.write(f"{parsed.account_info.statement_start_date} to {parsed.account_info.statement_end_date}")
        else:
            col3.write("Unknown")
        
        col4.markdown("**Confidence**")
        col4.write(f"{parsed.parsing_confidence:.0%}")
        
        # Summary section
        render_summary(parsed)
        
        # Transactions table
        if parsed.transactions:
            st.markdown("#### 📋 Transactions")
            
            # Convert to DataFrame for editing
            txn_data = []
            for t in parsed.transactions:
                t_type = t.transaction_type
                txn_data.append({
                    "Date": str(t.date),
                    "Description": t.description,
                    "Amount": t.amount,
                    "Type": t_type.value if hasattr(t_type, 'value') else str(t_type),
                    "Category": t.category or "Uncategorized"
                })
            
            df = pd.DataFrame(txn_data)
            
            # Editable table
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Description": st.column_config.TextColumn("Description", width="large"),
                    "Amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                    "Type": st.column_config.SelectboxColumn(
                        "Type",
                        options=["credit", "debit"],
                        width="small"
                    ),
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=get_category_options(),
                        width="medium"
                    )
                },
                num_rows="fixed"
            )
            
            # Totals
            credits = edited_df[edited_df['Type'] == 'credit']['Amount'].sum()
            debits = edited_df[edited_df['Type'] == 'debit']['Amount'].sum()
            
            tcol1, tcol2, tcol3 = st.columns(3)
            tcol1.metric("Total In", f"${credits:,.2f}")
            tcol2.metric("Total Out", f"${debits:,.2f}")
            tcol3.metric("Net", f"${credits - debits:,.2f}")
            
            # Show save status if already auto-saved
            save_result = result.get("save_result")
            if save_result:
                st.markdown("---")
                if save_result['transactions_saved'] > 0:
                    st.success(
                        f"✅ **Auto-saved:** {save_result['transactions_saved']} new transactions saved, "
                        f"{save_result['transactions_duplicated']} duplicates skipped"
                    )
                else:
                    st.info(
                        f"ℹ️ **Already saved:** All {save_result['total_transactions']} transactions were already in the database "
                        f"({save_result['transactions_duplicated']} duplicates skipped)"
                    )
            
            # Update button (for manual save after editing) - only show if user made edits
            st.markdown("---")
            # Use a more unique key that includes the full filename hash to avoid conflicts
            import hashlib
            file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
            button_key = f"update_{file_hash}_{len(parsed.transactions)}"
            
            if st.button(f"💾 Update Transactions", key=button_key, type="secondary", help="Save any edits you made to the transactions"):
                save_parsed_statement(parsed, edited_df, db, current_user, filename)
                # Refresh to show updated status
                st.rerun()
        
        # Parsing notes
        if parsed.parsing_notes:
            st.markdown("#### ⚠️ Notes")
            for note in parsed.parsing_notes:
                st.warning(note)


def render_summary(parsed):
    """Render the statement summary section."""
    summary = parsed.summary
    account_type = parsed.account_info.account_type
    
    st.markdown("#### 📊 Statement Summary")
    
    # Get account type value
    acc_type_val = account_type.value if hasattr(account_type, 'value') else str(account_type)
    
    if acc_type_val == "credit_card":
        # Credit card summary
        cols = st.columns(4)
        if hasattr(summary, 'previous_balance') and summary.previous_balance is not None:
            cols[0].metric("Previous Balance", f"${summary.previous_balance:,.2f}")
        if hasattr(summary, 'new_balance') and summary.new_balance is not None:
            cols[1].metric("New Balance", f"${summary.new_balance:,.2f}")
        if hasattr(summary, 'minimum_payment') and summary.minimum_payment is not None:
            cols[2].metric("Minimum Payment", f"${summary.minimum_payment:,.2f}")
        if hasattr(summary, 'payment_due_date') and summary.payment_due_date:
            cols[3].metric("Due Date", str(summary.payment_due_date))
    else:
        # Checking/savings summary
        cols = st.columns(4)
        if hasattr(summary, 'beginning_balance') and summary.beginning_balance is not None:
            cols[0].metric("Beginning Balance", f"${summary.beginning_balance:,.2f}")
        if hasattr(summary, 'ending_balance') and summary.ending_balance is not None:
            cols[1].metric("Ending Balance", f"${summary.ending_balance:,.2f}")
        if hasattr(summary, 'total_deposits') and summary.total_deposits is not None:
            cols[2].metric("Deposits", f"${summary.total_deposits:,.2f}")
        if hasattr(summary, 'total_withdrawals') and summary.total_withdrawals is not None:
            cols[3].metric("Withdrawals", f"${summary.total_withdrawals:,.2f}")


def get_category_options() -> list:
    """Get list of transaction categories."""
    return [
        "Uncategorized",
        "Groceries",
        "Dining & Restaurants",
        "Transportation",
        "Gas & Fuel",
        "Shopping",
        "Entertainment",
        "Subscriptions",
        "Utilities",
        "Rent & Mortgage",
        "Healthcare",
        "Personal Care",
        "Travel",
        "Education",
        "Income",
        "Transfer",
        "Fees & Charges",
        "Other"
    ]


def save_parsed_statement(parsed, edited_df: pd.DataFrame, db, current_user: Dict, filename: str):
    """Save parsed transactions to the database."""
    
    try:
        user_id = current_user["id"]
        
        # Generate a stable account ID based on account info and filename
        # This ensures same statement creates/reuses same account (matches save_parsed_statement_transactions)
        import hashlib
        account_key = f"{user_id}_{parsed.account_info.account_number_last4}_{parsed.account_info.bank_name}_{filename}"
        account_id = f"pdf_{hashlib.md5(account_key.encode()).hexdigest()[:16]}"
        
        # Check if account already exists
        existing_accounts = db.get_user_accounts(user_id)
        existing_account = None
        
        for acc in existing_accounts:
            if acc.get("account_id") == account_id:
                existing_account = acc
                break
        
        # Create account only if it doesn't exist
        if not existing_account:
            # Generate descriptive account name
            from src.services.statement_transaction_saver import generate_account_name
            account_name = generate_account_name(parsed)
            
            account_data = {
                "account_id": account_id,
                "name": account_name,
                "institution_name": parsed.account_info.bank_name or "PDF Upload",
                "type": parsed.account_info.account_type.value if hasattr(parsed.account_info.account_type, 'value') else str(parsed.account_info.account_type),
                "subtype": "pdf_upload",
                "mask": parsed.account_info.account_number_last4 or "****",
                "source": "pdf_upload",
                "current_balance": parsed.summary.ending_balance if hasattr(parsed.summary, 'ending_balance') else None,
                "available_balance": parsed.summary.ending_balance if hasattr(parsed.summary, 'ending_balance') else None,
                "statement_period": {
                    "start": str(parsed.account_info.statement_start_date) if parsed.account_info.statement_start_date else None,
                    "end": str(parsed.account_info.statement_end_date) if parsed.account_info.statement_end_date else None
                } if parsed.account_info.statement_start_date or parsed.account_info.statement_end_date else None
            }
            
            db.save_bank_account(user_id, account_data)
        
        # Convert edited DataFrame to transactions
        transactions = []
        for i, row in edited_df.iterrows():
            orig_txn = parsed.transactions[i] if i < len(parsed.transactions) else None
            
            # Plaid format: positive = spent, negative = received
            amount = float(row["Amount"])
            if row["Type"] == "credit":
                plaid_amount = -amount  # Money in = negative
            else:
                plaid_amount = amount   # Money out = positive
            
            txn = {
                "transaction_id": orig_txn.transaction_id if orig_txn else f"pdf_{i}_{datetime.now().timestamp()}",
                "account_id": account_id,
                "amount": plaid_amount,
                "date": row["Date"],
                "name": row["Description"],
                "merchant_name": row["Description"].split()[0] if row["Description"] else None,
                "category": [row["Category"]],
                "pending": False,
                "payment_channel": "other",
                "transaction_type": "place" if row["Type"] == "debit" else "credit",
                "source": "pdf_upload"
            }
            transactions.append(txn)
        
        # Save transactions using existing db method
        new_count = db.save_transactions(user_id, account_id, transactions)
        
        st.success(f"✅ Saved {new_count} new transactions!")
        st.balloons()
        
    except Exception as e:
        st.error(f"Failed to save: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


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


def render_history_tab(db, current_user: Dict):
    """Render the upload history tab."""
    
    # Get all accounts that are from PDF uploads
    accounts = db.get_user_accounts(current_user["id"])
    pdf_accounts = [a for a in accounts if a.get("source") == "pdf_upload"]
    
    if not pdf_accounts:
        st.info("No upload history yet. Upload your first statement!")
        return
    
    st.subheader("📋 Upload History")
    
    # Display as table
    data = []
    for acc in pdf_accounts:
        transactions = db.get_transactions(current_user["id"], acc.get("account_id"))
        data.append({
            "Bank": acc.get("institution_name", "Unknown"),
            "Account": acc.get("name", "Unknown"),
            "Transactions": len(transactions),
            "Created": acc.get("created_at", "")[:10] if acc.get("created_at") else "Unknown"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Summary stats
    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.metric("Total Uploads", len(pdf_accounts))
    col2.metric("Total Transactions", sum(d["Transactions"] for d in data))