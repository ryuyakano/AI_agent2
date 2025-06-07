# -*- coding: utf-8 -*-
import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List
from openai import OpenAI

class ContractJudge:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.langfuse_base_url = "http://localhost:3000"
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-1234567890abcdef")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-1234567890abcdef")
        
    def evaluate_contract_quality(self, contract_content: str, contract_type: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        LLM-as-a-Judgeによる契約書品質評価
        """
        trace_id = f"judge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # LangFuseトレース開始
        self._start_trace(trace_id, "contract_quality_evaluation")
        
        try:
            # 評価プロンプトの構築
            evaluation_prompt = self._build_evaluation_prompt(contract_content, contract_type, metadata)
            
            # LLM評価実行
            evaluation_result = self._execute_llm_evaluation(evaluation_prompt, trace_id)
            
            # 評価結果の解析
            parsed_result = self._parse_evaluation_result(evaluation_result)
            
            # LangFuseに評価結果を記録
            self._log_evaluation_to_langfuse(trace_id, evaluation_prompt, evaluation_result, parsed_result)
            
            return {
                "success": True,
                "trace_id": trace_id,
                "evaluation": parsed_result,
                "raw_response": evaluation_result
            }
            
        except Exception as e:
            self._log_error_to_langfuse(trace_id, str(e))
            return {
                "success": False,
                "error": str(e),
                "trace_id": trace_id
            }
    
    def _build_evaluation_prompt(self, contract_content: str, contract_type: str, metadata: Dict[str, Any]) -> str:
        """評価用プロンプトの構築"""
        
        if contract_type == "rental":
            criteria = """
            【賃貸契約書評価基準】
            1. 法的適合性 (1-10点): 日本の借地借家法・民法への準拠度
            2. 情報完整性 (1-10点): 必要な契約条項の網羅性
            3. 明瞭性 (1-10点): 条文の明確性・理解しやすさ
            4. リスク管理 (1-10点): 貸主・借主双方のリスク配慮
            5. 実用性 (1-10点): 実際の運用における有効性
            """
            specific_items = """
            - 物件詳細情報の記載
            - 賃料・敷金・礼金の明記
            - 契約期間と更新条件
            - 修繕責任の明確化
            - 解約条件の適切性
            """
        else:  # service
            criteria = """
            【業務委託契約書評価基準】
            1. 法的適合性 (1-10点): 日本の民法・労働法への準拠度
            2. 業務範囲明確性 (1-10点): 委託業務の具体性・明確性
            3. 報酬・支払条件 (1-10点): 報酬体系の明確性
            4. 責任・リスク分担 (1-10点): 責任範囲の適切な分担
            5. 契約管理 (1-10点): 契約変更・終了条件の適切性
            """
            specific_items = """
            - 業務内容の具体的記載
            - 成果物・納期の明確化
            - 報酬額と支払方法
            - 知的財産権の取扱い
            - 秘密保持義務
            """
        
        prompt = f"""
あなたは法務の専門家として、以下の{contract_type}契約書の品質を客観的に評価してください。

【契約書内容】
{contract_content}

【メタデータ】
{json.dumps(metadata, ensure_ascii=False, indent=2)}

{criteria}

【評価項目】
{specific_items}

【評価形式】
以下のJSON形式で評価結果を出力してください：

{{
    "overall_score": <総合点数 1-100>,
    "scores": {{
        "legal_compliance": <法的適合性点数 1-10>,
        "completeness": <完整性点数 1-10>,
        "clarity": <明瞭性点数 1-10>,
        "risk_management": <リスク管理点数 1-10>,
        "practicality": <実用性点数 1-10>
    }},
    "strengths": [
        "<強み1>",
        "<強み2>"
    ],
    "weaknesses": [
        "<弱点1>",
        "<弱点2>"
    ],
    "recommendations": [
        "<改善提案1>",
        "<改善提案2>"
    ],
    "legal_issues": [
        "<法的懸念点1>",
        "<法的懸念点2>"
    ],
    "grade": "<A/B/C/D/F>",
    "summary": "<100文字程度の総評>"
}}

必ず上記JSON形式でのみ回答してください。
"""
        return prompt
    
    def _execute_llm_evaluation(self, prompt: str, trace_id: str) -> str:
        """LLM評価の実行"""
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは法務専門家として契約書の品質を客観的に評価します。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def _parse_evaluation_result(self, result: str) -> Dict[str, Any]:
        """評価結果の解析"""
        try:
            # JSON部分を抽出
            start_idx = result.find('{')
            end_idx = result.rfind('}') + 1
            json_str = result[start_idx:end_idx]
            
            parsed = json.loads(json_str)
            
            # スコアの妥当性チェック
            if parsed.get("overall_score", 0) < 1 or parsed.get("overall_score", 0) > 100:
                parsed["overall_score"] = max(1, min(100, parsed.get("overall_score", 50)))
            
            return parsed
            
        except (json.JSONDecodeError, ValueError) as e:
            # パースに失敗した場合のフォールバック
            return {
                "overall_score": 50,
                "scores": {
                    "legal_compliance": 5,
                    "completeness": 5,
                    "clarity": 5,
                    "risk_management": 5,
                    "practicality": 5
                },
                "strengths": ["評価結果の解析に失敗しました"],
                "weaknesses": ["詳細な評価ができませんでした"],
                "recommendations": ["再評価を実行してください"],
                "legal_issues": [],
                "grade": "C",
                "summary": "評価処理中にエラーが発生しました",
                "parse_error": str(e)
            }
    
    def _start_trace(self, trace_id: str, name: str):
        """LangFuseトレース開始"""
        try:
            trace_data = {
                "id": trace_id,
                "name": name,
                "metadata": {
                    "type": "contract_evaluation",
                    "timestamp": datetime.now().isoformat()
                },
                "tags": ["llm-as-a-judge", "contract-quality"]
            }
            
            response = requests.post(
                f"{self.langfuse_base_url}/api/public/traces",
                json=trace_data,
                headers={"Content-Type": "application/json"},
                auth=(self.langfuse_public_key, self.langfuse_secret_key)
            )
            
        except Exception as e:
            print(f"LangFuse trace start error: {e}")
    
    def _log_evaluation_to_langfuse(self, trace_id: str, prompt: str, response: str, parsed_result: Dict[str, Any]):
        """評価結果をLangFuseに記録"""
        try:
            generation_data = {
                "id": f"{trace_id}_evaluation",
                "traceId": trace_id,
                "name": "contract_quality_evaluation",
                "startTime": datetime.now().isoformat(),
                "endTime": datetime.now().isoformat(),
                "model": "gpt-4o",
                "modelParameters": {
                    "temperature": 0.1,
                    "maxTokens": 2000
                },
                "input": prompt,
                "output": response,
                "metadata": {
                    "evaluation_scores": parsed_result.get("scores", {}),
                    "overall_score": parsed_result.get("overall_score", 0),
                    "grade": parsed_result.get("grade", "N/A")
                },
                "tags": ["evaluation", "llm-judge"]
            }
            
            response = requests.post(
                f"{self.langfuse_base_url}/api/public/generations",
                json=generation_data,
                headers={"Content-Type": "application/json"},
                auth=(self.langfuse_public_key, self.langfuse_secret_key)
            )
            
        except Exception as e:
            print(f"LangFuse logging error: {e}")
    
    def _log_error_to_langfuse(self, trace_id: str, error_message: str):
        """エラーをLangFuseに記録"""
        try:
            error_data = {
                "id": f"{trace_id}_error",
                "traceId": trace_id,
                "name": "evaluation_error",
                "startTime": datetime.now().isoformat(),
                "endTime": datetime.now().isoformat(),
                "level": "ERROR",
                "message": error_message,
                "metadata": {
                    "type": "contract_evaluation_error"
                }
            }
            
            requests.post(
                f"{self.langfuse_base_url}/api/public/events",
                json=error_data,
                headers={"Content-Type": "application/json"},
                auth=(self.langfuse_public_key, self.langfuse_secret_key)
            )
            
        except Exception as e:
            print(f"LangFuse error logging failed: {e}")
    
    def batch_evaluate_contracts(self, contract_files: List[str]) -> List[Dict[str, Any]]:
        """複数契約書の一括評価"""
        results = []
        
        for file_path in contract_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # メタデータファイルを読み込み
                metadata_path = f"{file_path}.metadata.json"
                metadata = {}
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                
                # 契約書タイプを判定
                contract_type = "rental" if "rental" in file_path else "service"
                
                # 評価実行
                evaluation = self.evaluate_contract_quality(content, contract_type, metadata)
                evaluation["file_path"] = file_path
                
                results.append(evaluation)
                
            except Exception as e:
                results.append({
                    "success": False,
                    "error": str(e),
                    "file_path": file_path
                })
        
        return results