# -*- coding: utf-8 -*-
import os
from openai import OpenAI
from typing import Dict, Any
import requests
import json
from datetime import datetime
import uuid
import base64

class DocumentAgent:
    def __init__(self):
        # OpenAI APIキーの確認
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY環境変数を設定してください。")
        
        self.client = OpenAI(api_key=api_key)
        
        # LangFuse設定
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
        
        # プロジェクトIDを取得
        self.project_id = None
        
        if self.langfuse_public_key and self.langfuse_secret_key:
            try:
                # 認証ヘッダー作成
                auth_string = f"{self.langfuse_public_key}:{self.langfuse_secret_key}"
                auth_bytes = auth_string.encode('ascii')
                auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
                self.auth_header = f"Basic {auth_b64}"
                
                # プロジェクト情報を取得
                headers = {
                    "Authorization": self.auth_header,
                    "Content-Type": "application/json"
                }
                
                response = requests.get(f"{self.langfuse_host}/api/public/projects", headers=headers)
                
                if response.status_code == 200:
                    projects = response.json()
                    if projects.get("data") and len(projects["data"]) > 0:
                        self.project_id = projects["data"][0]["id"]
                        project_name = projects["data"][0]["name"]
                        
                        print(f"✅ LangFuse接続成功")
                        print(f"📊 プロジェクト: {project_name} (ID: {self.project_id})")
                        
                        self.langfuse_enabled = True
                    else:
                        print("⚠️ プロジェクトが見つかりません")
                        self.langfuse_enabled = False
                else:
                    print(f"⚠️ LangFuse認証失敗: {response.status_code}")
                    self.langfuse_enabled = False
                    
            except Exception as e:
                print(f"⚠️ LangFuse初期化エラー: {e}")
                self.langfuse_enabled = False
        else:
            print("⚠️ LangFuse設定不完全")
            self.langfuse_enabled = False
    
    def _create_langfuse_trace(self, name: str, metadata: Dict):
        """LangFuseにトレースを作成"""
        if not self.langfuse_enabled:
            return None
            
        trace_id = str(uuid.uuid4())
        
        try:
            headers = {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
            
            # LangFuse 2.95の正確なAPI形式
            trace_data = {
                "id": trace_id,
                "name": name,
                "userId": "system",
                "metadata": metadata,
                "public": False,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            response = requests.post(
                f"{self.langfuse_host}/api/public/traces",
                headers=headers,
                json=trace_data
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ トレース作成成功: {trace_id}")
                return trace_id
            else:
                print(f"⚠️ トレース作成失敗: {response.status_code}")
                print(f"📥 エラー詳細: {response.text}")
                return None
                
        except Exception as e:
            print(f"⚠️ トレース作成エラー: {e}")
            return None
    
    def _create_langfuse_generation(self, trace_id: str, name: str, model: str, input_data: str, output_data: str, usage: Dict):
        """LangFuseにgenerationを作成"""
        if not self.langfuse_enabled or not trace_id:
            return None
            
        generation_id = str(uuid.uuid4())
        
        try:
            headers = {
                "Authorization": self.auth_header,
                "Content-Type": "application/json"
            }
            
            # LangFuseのgeneration API形式
            generation_data = {
                "id": generation_id,
                "traceId": trace_id,
                "name": name,
                "startTime": datetime.utcnow().isoformat() + "Z",
                "endTime": datetime.utcnow().isoformat() + "Z",
                "model": model,
                "input": input_data,
                "output": output_data,
                "usage": {
                    "promptTokens": usage.get("promptTokens", 0),
                    "completionTokens": usage.get("completionTokens", 0),
                    "totalTokens": usage.get("totalTokens", 0)
                },
                "metadata": {}
            }
            
            response = requests.post(
                f"{self.langfuse_host}/api/public/generations",
                headers=headers,
                json=generation_data
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Generation作成成功: {generation_id}")
                print(f"🔗 トレースURL: {self.langfuse_host}/trace/{trace_id}")
                return generation_id
            else:
                print(f"⚠️ Generation作成失敗: {response.status_code}")
                print(f"📥 エラー詳細: {response.text}")
                return None
                
        except Exception as e:
            print(f"⚠️ Generation作成エラー: {e}")
            return None
    
    def generate_rental_contract(self, params: Dict[str, Any]) -> str:
        """賃貸契約書を生成"""
        
        print("📊 賃貸契約書生成開始")
        
        # LangFuseトレース作成
        trace_id = self._create_langfuse_trace(
            "rental_contract_generation",
            {
                "contract_type": "rental",
                "params": params
            }
        )
        
        prompt = f"""
        以下の条件で賃貸契約書を作成してください：
        
        物件情報：
        - 物件名: {params.get('property_name', '未指定')}
        - 所在地: {params.get('address', '未指定')}
        - 賃料: {params.get('rent', '未指定')}
        - 敷金: {params.get('deposit', '未指定')}
        - 礼金: {params.get('key_money', '未指定')}
        - 契約期間: {params.get('period', '2年')}
        
        貸主情報：
        - 氏名: {params.get('landlord_name', '田中太郎')}
        
        借主情報：
        - 氏名: {params.get('tenant_name', '佐藤花子')}
        
        日本の法律に準拠した正式な賃貸契約書として作成してください。
        """
        
        # OpenAI API呼び出し
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは日本の不動産法に精通した法務専門家です。正確で法的に有効な賃貸契約書を作成してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = response.choices[0].message.content
        
        # LangFuseにgeneration記録
        if trace_id:
            self._create_langfuse_generation(
                trace_id,
                "openai_rental_contract",
                "gpt-3.5-turbo",
                prompt,
                result,
                {
                    "promptTokens": response.usage.prompt_tokens if response.usage else 0,
                    "completionTokens": response.usage.completion_tokens if response.usage else 0,
                    "totalTokens": response.usage.total_tokens if response.usage else 0
                }
            )
        
        print("✅ 賃貸契約書生成完了")
        return result
    
    def generate_service_contract(self, params: Dict[str, Any]) -> str:
        """業務委託契約書を生成"""
        
        print("📊 業務委託契約書生成開始")
        
        # LangFuseトレース作成
        trace_id = self._create_langfuse_trace(
            "service_contract_generation",
            {
                "contract_type": "service",
                "params": params
            }
        )
        
        prompt = f"""
        以下の条件で業務委託契約書を作成してください：
        
        委託業務：
        - 業務内容: {params.get('service_description', '未指定')}
        - 委託期間: {params.get('period', '6ヶ月')}
        - 報酬: {params.get('compensation', '未指定')}
        - 支払条件: {params.get('payment_terms', '月末締め翌月末支払い')}
        
        委託者情報：
        - 会社名: {params.get('client_company', '株式会社サンプル')}
        - 代表者: {params.get('client_representative', '山田一郎')}
        
        受託者情報：
        - 氏名/会社名: {params.get('contractor_name', '鈴木二郎')}
        
        日本の法律に準拠した正式な業務委託契約書として作成してください。
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは日本の契約法に精通した法務専門家です。正確で法的に有効な業務委託契約書を作成してください。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = response.choices[0].message.content
        
        # LangFuseにgeneration記録
        if trace_id:
            self._create_langfuse_generation(
                trace_id,
                "openai_service_contract",
                "gpt-3.5-turbo",
                prompt,
                result,
                {
                    "promptTokens": response.usage.prompt_tokens if response.usage else 0,
                    "completionTokens": response.usage.completion_tokens if response.usage else 0,
                    "totalTokens": response.usage.total_tokens if response.usage else 0
                }
            )
        
        print("✅ 業務委託契約書生成完了")
        return result