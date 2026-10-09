import asyncio
from app.config import Config
from app.services.ai import AIService
import logging
logging.basicConfig(level=logging.DEBUG)

async def main():
    config = Config.from_env()
    print("Groq key:", config.groq_api_key)
    print("Gemini key:", config.gemini_api_key)
    ai = AIService(config)
    try:
        res = await ai._complete("System msg", "User msg", json_mode=False)
        print("Success:", res)
    except Exception as e:
        print("Failed:", type(e), e)

asyncio.run(main())
