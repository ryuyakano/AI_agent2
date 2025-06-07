# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

class DocumentStorage:
    def __init__(self, base_dir: str = "contracts"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.rental_dir = self.base_dir / "rental"
        self.service_dir = self.base_dir / "service"
        self.rental_dir.mkdir(exist_ok=True)
        self.service_dir.mkdir(exist_ok=True)
        
    def save_contract(self, contract_type: str, content: str, metadata: Dict[str, Any]) -> str:
        """契約書を保存し、ファイルパスを返す"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if contract_type == "rental":
            directory = self.rental_dir
            filename = f"rental_contract_{timestamp}.txt"
        elif contract_type == "service":
            directory = self.service_dir
            filename = f"service_contract_{timestamp}.txt"
        else:
            raise ValueError(f"Unknown contract type: {contract_type}")
            
        file_path = directory / filename
        metadata_path = directory / f"{filename}.metadata.json"
        
        # 契約書本文を保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # メタデータを保存
        metadata['created_at'] = datetime.now().isoformat()
        metadata['file_path'] = str(file_path)
        metadata['contract_type'] = contract_type
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        return str(file_path)
    
    def list_contracts(self, contract_type: str = None) -> list:
        """保存された契約書一覧を取得"""
        contracts = []
        
        directories = []
        if contract_type == "rental" or contract_type is None:
            directories.append(("rental", self.rental_dir))
        if contract_type == "service" or contract_type is None:
            directories.append(("service", self.service_dir))
            
        for ctype, directory in directories:
            for file_path in directory.glob("*.txt"):
                metadata_path = file_path.with_suffix(".txt.metadata.json")
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    contracts.append({
                        'type': ctype,
                        'file_path': str(file_path),
                        'metadata': metadata
                    })
                    
        return sorted(contracts, key=lambda x: x['metadata']['created_at'], reverse=True)