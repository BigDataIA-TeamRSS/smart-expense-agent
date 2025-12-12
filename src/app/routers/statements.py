"""PDF statement upload endpoints"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List
from src.app.dependencies import get_current_user, get_db
from src.config import Config
import hashlib

router = APIRouter()


@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload and parse bank statement PDF"""
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Validate file size
    contents = await file.read()
    if len(contents) > Config.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {Config.MAX_FILE_SIZE_MB}MB limit"
        )
    
    # Parse statement
    try:
        from src.services.statement_parser import StatementParser
        
        # Check if API key is configured
        if not Config.GEMINI_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is not configured. Please set it in your environment variables."
            )
        
        parser = StatementParser(gemini_api_key=Config.GEMINI_API_KEY)
        parsed = parser.parse_with_retry(contents, file.filename)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[STATEMENTS] Error parsing statement: {str(e)}")
        print(f"[STATEMENTS] Traceback: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse statement: {str(e)}"
        )
    
    # Auto-save transactions
    try:
        from src.services.statement_transaction_saver import save_parsed_statement_transactions
        save_result = save_parsed_statement_transactions(
            parsed, db, current_user["id"], file.filename, auto_create_account=True
        )
    except Exception as save_error:
        # Log error but don't fail the parsing
        import traceback
        error_trace = traceback.format_exc()
        print(f"[STATEMENTS] Error saving transactions: {str(save_error)}")
        print(f"[STATEMENTS] Save error traceback: {error_trace}")
        save_result = {
            "transactions_saved": 0,
            "transactions_duplicated": 0,
            "error": str(save_error)
        }
    
    # Prepare response
    account_info = parsed.account_info
    return {
        "message": "Statement parsed successfully",
        "filename": file.filename,
        "bank_name": account_info.bank_name or "Unknown",
        "account_type": account_info.account_type.value if hasattr(account_info.account_type, 'value') else str(account_info.account_type),
        "statement_period": {
            "start": str(account_info.statement_start_date) if account_info.statement_start_date else None,
            "end": str(account_info.statement_end_date) if account_info.statement_end_date else None
        },
        "transactions_count": len(parsed.transactions),
        "parsing_confidence": parsed.parsing_confidence,
        "transactions": [
            {
                "date": str(t.date),
                "description": t.description,
                "amount": float(t.amount),
                "type": t.transaction_type.value if hasattr(t.transaction_type, 'value') else str(t.transaction_type),
                "category": t.category
            }
            for t in parsed.transactions
        ],
        "save_result": save_result
    }


@router.get("/history")
async def get_upload_history(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get PDF upload history"""
    accounts = db.get_user_accounts(current_user["id"])
    pdf_accounts = [a for a in accounts if a.get("source") == "pdf_upload"]
    
    history = []
    for acc in pdf_accounts:
        transactions = db.get_transactions(current_user["id"], acc.get("account_id"))
        history.append({
            "bank": acc.get("institution_name", "Unknown"),
            "account": acc.get("name", "Unknown"),
            "transactions": len(transactions),
            "created": acc.get("created_at", "")[:10] if acc.get("created_at") else "Unknown"
        })
    
    return {"history": history}
