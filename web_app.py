#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import sys
from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# 現在のディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.document_agent import DocumentAgent
from agent.document_storage import DocumentStorage
from agent.contract_judge import ContractJudge

# FastAPIアプリケーション作成
app = FastAPI(
    title="ドキュメント管理AI Agent",
    description="OpenAI Agent SDKとLangFuseを使った契約書生成・管理システム",
    version="1.0.0"
)

# テンプレートとスタティックファイルの設定
templates = Jinja2Templates(directory="templates")

# 静的ファイルがある場合
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydanticモデル
class RentalContractRequest(BaseModel):
    property_name: str
    address: str
    rent: str
    deposit: str
    key_money: str
    period: str = "2年"
    landlord_name: str
    tenant_name: str

class ServiceContractRequest(BaseModel):
    service_description: str
    period: str = "6ヶ月"
    compensation: str
    payment_terms: str = "月末締め翌月末支払い"
    client_company: str
    client_representative: str
    contractor_name: str

class ContractResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None
    contract_content: Optional[str] = None
    trace_url: Optional[str] = None

class SearchRequest(BaseModel):
    query: Optional[str] = None
    contract_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None

class EvaluationRequest(BaseModel):
    file_name: str

class EvaluationResponse(BaseModel):
    success: bool
    message: str
    trace_id: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# エージェントとストレージのインスタンス
agent = DocumentAgent()
storage = DocumentStorage()
judge = ContractJudge()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """ホームページ"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/rental", response_class=HTMLResponse)
async def rental_form(request: Request):
    """賃貸契約書作成フォーム"""
    return templates.TemplateResponse("rental_form.html", {"request": request})

@app.get("/service", response_class=HTMLResponse)
async def service_form(request: Request):
    """業務委託契約書作成フォーム"""
    return templates.TemplateResponse("service_form.html", {"request": request})

@app.get("/contracts", response_class=HTMLResponse)
async def contracts_list(request: Request):
    """契約書一覧ページ"""
    contracts = storage.list_contracts()
    return templates.TemplateResponse("contracts_list.html", {
        "request": request, 
        "contracts": contracts
    })

@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """検索ページ"""
    return templates.TemplateResponse("search.html", {"request": request})

@app.post("/search", response_class=HTMLResponse)
async def search_contracts_web(
    request: Request,
    query: str = Form(None),
    contract_type: str = Form(None),
    date_from: str = Form(None),
    date_to: str = Form(None)
):
    """検索結果表示"""
    try:
        contracts = storage.search_contracts(
            query=query if query else None,
            contract_type=contract_type if contract_type != "all" else None,
            date_from=date_from if date_from else None,
            date_to=date_to if date_to else None
        )
        
        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "contracts": contracts,
            "search_query": query,
            "contract_type": contract_type,
            "date_from": date_from,
            "date_to": date_to,
            "total_count": len(contracts)
        })
        
    except Exception as e:
        return templates.TemplateResponse("search_results.html", {
            "request": request,
            "error": str(e),
            "contracts": [],
            "search_query": query,
            "total_count": 0
        })

# REST API エンドポイント

@app.post("/api/rental", response_model=ContractResponse)
async def create_rental_contract(contract_request: RentalContractRequest):
    """賃貸契約書生成API"""
    try:
        params = contract_request.dict()
        
        # 契約書生成
        contract_content = agent.generate_rental_contract(params)
        
        # ファイル保存
        file_path = storage.save_contract('rental', contract_content, params)
        
        return ContractResponse(
            success=True,
            message="賃貸契約書が正常に生成されました",
            file_path=file_path,
            contract_content=contract_content
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"契約書生成エラー: {str(e)}")

@app.post("/api/service", response_model=ContractResponse)
async def create_service_contract(contract_request: ServiceContractRequest):
    """業務委託契約書生成API"""
    try:
        params = contract_request.dict()
        
        # 契約書生成
        contract_content = agent.generate_service_contract(params)
        
        # ファイル保存
        file_path = storage.save_contract('service', contract_content, params)
        
        return ContractResponse(
            success=True,
            message="業務委託契約書が正常に生成されました",
            file_path=file_path,
            contract_content=contract_content
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"契約書生成エラー: {str(e)}")

@app.get("/api/contracts")
async def get_contracts(contract_type: Optional[str] = None):
    """契約書一覧取得API"""
    try:
        contracts = storage.list_contracts(contract_type)
        return {
            "success": True,
            "contracts": contracts,
            "count": len(contracts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"契約書一覧取得エラー: {str(e)}")

@app.get("/api/contracts/{file_name}")
async def get_contract_content(file_name: str):
    """契約書内容取得API"""
    try:
        # ファイルパスを構築
        for contract_type in ['rental', 'service']:
            file_path = f"contracts/{contract_type}/{file_name}"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # メタデータも取得
                metadata_path = f"{file_path}.metadata.json"
                metadata = {}
                if os.path.exists(metadata_path):
                    import json
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                
                return {
                    "success": True,
                    "content": content,
                    "metadata": metadata
                }
        
        raise HTTPException(status_code=404, detail="契約書が見つかりません")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"契約書取得エラー: {str(e)}")

@app.post("/api/search")
async def search_contracts(search_request: SearchRequest):
    """契約書検索API"""
    try:
        contracts = storage.search_contracts(
            query=search_request.query,
            contract_type=search_request.contract_type,
            date_from=search_request.date_from,
            date_to=search_request.date_to
        )
        return {
            "success": True,
            "contracts": contracts,
            "count": len(contracts),
            "query": search_request.query,
            "filters": {
                "contract_type": search_request.contract_type,
                "date_from": search_request.date_from,
                "date_to": search_request.date_to
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")

@app.get("/api/search")
async def search_contracts_get(
    query: Optional[str] = None,
    contract_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
):
    """契約書検索API (GET版)"""
    try:
        contracts = storage.search_contracts(
            query=query,
            contract_type=contract_type,
            date_from=date_from,
            date_to=date_to
        )
        return {
            "success": True,
            "contracts": contracts,
            "count": len(contracts),
            "query": query,
            "filters": {
                "contract_type": contract_type,
                "date_from": date_from,
                "date_to": date_to
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"検索エラー: {str(e)}")

@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate_contract(evaluation_request: EvaluationRequest):
    """契約書品質評価API"""
    try:
        # ファイルを探して読み込み
        file_name = evaluation_request.file_name
        contract_content = None
        metadata = {}
        contract_type = None
        
        for ctype in ['rental', 'service']:
            file_path = f"contracts/{ctype}/{file_name}"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    contract_content = f.read()
                
                # メタデータを読み込み
                metadata_path = f"{file_path}.metadata.json"
                if os.path.exists(metadata_path):
                    import json
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                
                contract_type = ctype
                break
        
        if not contract_content:
            raise HTTPException(status_code=404, detail="契約書が見つかりません")
        
        # LLM-as-a-Judgeで評価実行
        result = judge.evaluate_contract_quality(contract_content, contract_type, metadata)
        
        if result["success"]:
            return EvaluationResponse(
                success=True,
                message="契約書の品質評価が完了しました",
                trace_id=result["trace_id"],
                evaluation=result["evaluation"]
            )
        else:
            return EvaluationResponse(
                success=False,
                message="評価中にエラーが発生しました",
                error=result["error"],
                trace_id=result.get("trace_id")
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"評価エラー: {str(e)}")

@app.post("/api/batch-evaluate")
async def batch_evaluate_contracts(contract_type: Optional[str] = None):
    """一括評価API"""
    try:
        # 契約書一覧を取得
        contracts = storage.list_contracts(contract_type)
        file_paths = [contract["file_path"] for contract in contracts]
        
        # 一括評価実行
        results = judge.batch_evaluate_contracts(file_paths)
        
        return {
            "success": True,
            "message": f"{len(results)}件の契約書評価が完了しました",
            "evaluations": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"一括評価エラー: {str(e)}")

# Web フォーム処理エンドポイント

@app.post("/rental", response_class=HTMLResponse)
async def create_rental_web(
    request: Request,
    property_name: str = Form(...),
    address: str = Form(...),
    rent: str = Form(...),
    deposit: str = Form(...),
    key_money: str = Form(...),
    period: str = Form("2年"),
    landlord_name: str = Form(...),
    tenant_name: str = Form(...)
):
    """Webフォームからの賃貸契約書生成"""
    try:
        params = {
            'property_name': property_name,
            'address': address,
            'rent': rent,
            'deposit': deposit,
            'key_money': key_money,
            'period': period,
            'landlord_name': landlord_name,
            'tenant_name': tenant_name
        }
        
        contract_content = agent.generate_rental_contract(params)
        file_path = storage.save_contract('rental', contract_content, params)
        
        return templates.TemplateResponse("contract_result.html", {
            "request": request,
            "success": True,
            "contract_type": "賃貸契約書",
            "file_path": file_path,
            "contract_content": contract_content
        })
        
    except Exception as e:
        return templates.TemplateResponse("contract_result.html", {
            "request": request,
            "success": False,
            "error": str(e)
        })

@app.post("/service", response_class=HTMLResponse)
async def create_service_web(
    request: Request,
    service_description: str = Form(...),
    period: str = Form("6ヶ月"),
    compensation: str = Form(...),
    payment_terms: str = Form("月末締め翌月末支払い"),
    client_company: str = Form(...),
    client_representative: str = Form(...),
    contractor_name: str = Form(...)
):
    """Webフォームからの業務委託契約書生成"""
    try:
        params = {
            'service_description': service_description,
            'period': period,
            'compensation': compensation,
            'payment_terms': payment_terms,
            'client_company': client_company,
            'client_representative': client_representative,
            'contractor_name': contractor_name
        }
        
        contract_content = agent.generate_service_contract(params)
        file_path = storage.save_contract('service', contract_content, params)
        
        return templates.TemplateResponse("contract_result.html", {
            "request": request,
            "success": True,
            "contract_type": "業務委託契約書",
            "file_path": file_path,
            "contract_content": contract_content
        })
        
    except Exception as e:
        return templates.TemplateResponse("contract_result.html", {
            "request": request,
            "success": False,
            "error": str(e)
        })

@app.get("/evaluate", response_class=HTMLResponse)
async def evaluation_page(request: Request, file: Optional[str] = None):
    """評価ページ"""
    contracts = storage.list_contracts()
    return templates.TemplateResponse("evaluation.html", {
        "request": request,
        "contracts": contracts,
        "preselected_file": file
    })

@app.post("/evaluate", response_class=HTMLResponse)
async def evaluate_contract_web(
    request: Request,
    file_name: str = Form(...)
):
    """契約書評価実行"""
    try:
        # APIを呼び出し
        eval_request = EvaluationRequest(file_name=file_name)
        result = await evaluate_contract(eval_request)
        
        return templates.TemplateResponse("evaluation_result.html", {
            "request": request,
            "success": result.success,
            "evaluation": result.evaluation,
            "trace_id": result.trace_id,
            "file_name": file_name,
            "error": result.error
        })
        
    except Exception as e:
        return templates.TemplateResponse("evaluation_result.html", {
            "request": request,
            "success": False,
            "error": str(e),
            "file_name": file_name
        })

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {"status": "healthy", "message": "ドキュメント管理AI Agent is running"}

if __name__ == "__main__":
    import uvicorn
    import socket
    
    # 利用可能なポートを見つける
    def find_free_port():
        for port in [8081, 8082, 8083, 8084, 8085, 9000, 9001, 9002]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return None
    
    port = find_free_port()
    if port:
        print("🌐 Webサーバーを起動しています...")
        print("📍 アクセスURL:")
        print(f"   http://localhost:{port}")
        print(f"   http://127.0.0.1:{port}")
        print("🔄 サーバーを停止するには Ctrl+C を押してください")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        print("❌ 利用可能なポートが見つかりません")
        print("💡 他のアプリケーションを終了してから再試行してください")