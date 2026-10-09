import asyncio
from app.config import Config
from app.services.ai import AIService

async def main():
    config = Config.from_env()
    ai = AIService(config)
    print("Testing analyze_company...")
    try:
        res = await ai.analyze_company("OpenAI makes ChatGPT.")
        print(res)
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
