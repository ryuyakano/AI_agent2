# ai_agent.py
from dotenv import load_dotenv
load_dotenv()

from agent.builder import build_agent


def main():
    print("💼 契約書生成エージェントへようこそ！")
    print("🔹 指示を入力してください（例: 業務委託契約書を作成してください）")

    while True:
        try:
            instruction = input("\n📝 指示 > ").strip()
            if instruction.lower() in ["exit", "quit", "q"]:
                print("👋 終了します。")
                break

            agent = build_agent()
            response = agent.run(instruction)

            print("\n📄 生成された契約書:\n")
            print(response)

        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
