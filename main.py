# -*- coding: utf-8 -*-
import click
import os
import sys
from dotenv import load_dotenv

# 環境変数をロード
load_dotenv()

# 現在のディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.document_agent import DocumentAgent
from agent.document_storage import DocumentStorage


@click.group()
def cli():
    """ドキュメント管理AI Agent - 契約書生成・管理ツール"""
    pass


@cli.command()
def rental():
    """賃貸契約書を生成します"""
    click.echo("📋 賃貸契約書を生成しています...")
    
    # ユーザー入力
    property_name = click.prompt('物件名')
    address = click.prompt('所在地')
    rent = click.prompt('賃料（円）')
    deposit = click.prompt('敷金（円）')
    key_money = click.prompt('礼金（円）')
    period = click.prompt('契約期間', default='2年')
    landlord_name = click.prompt('貸主氏名')
    tenant_name = click.prompt('借主氏名')
    
    agent = DocumentAgent()
    storage = DocumentStorage()
    
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
    
    try:
        contract = agent.generate_rental_contract(params)
        file_path = storage.save_contract('rental', contract, params)
        
        click.echo(f"\n✅ 賃貸契約書が生成されました！")
        click.echo(f"📁 保存先: {file_path}")
        click.echo(f"\n📄 契約書内容:\n{contract}")
        
    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}")


@cli.command()
def service():
    """業務委託契約書を生成します"""
    click.echo("📋 業務委託契約書を生成しています...")
    
    # ユーザー入力
    service_description = click.prompt('業務内容')
    period = click.prompt('委託期間', default='6ヶ月')
    compensation = click.prompt('報酬')
    payment_terms = click.prompt('支払条件', default='月末締め翌月末支払い')
    client_company = click.prompt('委託者会社名')
    client_representative = click.prompt('委託者代表者名')
    contractor_name = click.prompt('受託者名')
    
    agent = DocumentAgent()
    storage = DocumentStorage()
    
    params = {
        'service_description': service_description,
        'period': period,
        'compensation': compensation,
        'payment_terms': payment_terms,
        'client_company': client_company,
        'client_representative': client_representative,
        'contractor_name': contractor_name
    }
    
    try:
        contract = agent.generate_service_contract(params)
        file_path = storage.save_contract('service', contract, params)
        
        click.echo(f"\n✅ 業務委託契約書が生成されました！")
        click.echo(f"📁 保存先: {file_path}")
        click.echo(f"\n📄 契約書内容:\n{contract}")
        
    except Exception as e:
        click.echo(f"❌ エラーが発生しました: {e}")


@cli.command()
def list_contracts():
    """保存された契約書一覧を表示します"""
    storage = DocumentStorage()
    contracts = storage.list_contracts()
    
    if not contracts:
        click.echo("📭 保存された契約書はありません。")
        return
    
    click.echo(f"📚 保存された契約書一覧 ({len(contracts)}件):")
    click.echo("-" * 60)
    
    for contract in contracts:
        metadata = contract['metadata']
        click.echo(f"種類: {contract['type']}")
        click.echo(f"作成日時: {metadata['created_at']}")
        click.echo(f"ファイル: {contract['file_path']}")
        if contract['type'] == 'rental':
            click.echo(f"物件: {metadata.get('property_name', 'N/A')}")
            click.echo(f"賃料: {metadata.get('rent', 'N/A')}")
        elif contract['type'] == 'service':
            click.echo(f"業務: {metadata.get('service_description', 'N/A')}")
            click.echo(f"報酬: {metadata.get('compensation', 'N/A')}")
        click.echo("-" * 60)


if __name__ == "__main__":
    cli()