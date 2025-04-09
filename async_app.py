import asyncio
import random

from async_api import AsyncKlok
import config
from loguru import logger


async def process_account(private_key: str, proxy: str, questions: list):
    """处理单个账户的并发任务"""
    try:
        klok = AsyncKlok(
            private_key=private_key,
            referral_code=config.referral_code,
            proxy=proxy
        )

        # 验证账户
        await klok.verify()

        # 检查并执行推特任务
        if not await klok.twitter_klok_completed():
            await klok.track()
            await klok.follow_klok()
        if not await klok.twitter_mira_completed():
            await klok.track()
            await klok.follow_mira()

        # 检查并加入Discord
        if not await klok.discord_completed():
            await klok.track()
            await klok.join_discord()

        await klok.track()
        models = await klok.get_models()

        # 聊天会话
        messages = []
        while True:
            rate_limit = await klok.rate_limit()
            if rate_limit['remaining'] <= 0:
                logger.warning(f"Rate limit exceeded for {private_key[:6]}...")
                break
            question = random.choice(questions).strip()
            messages.append({"role": "user", "content": question})
            response = await klok.chat(messages, random.choice(models))
            messages.append({"role": "assistant", "content": response})
            await asyncio.sleep(random.uniform(10, 20))  # 使用异步sleep
        await klok.close()
    except Exception as e:
        logger.error(f"Error processing {private_key[:6]}...: {str(e)}")


async def main():
    # 并发读取文件
    with open("private_keys.txt") as f:
        private_keys = [line.strip() for line in f if line.strip()]

    with open("questions.txt") as f:
        questions = [line.strip() for line in f if line.strip()]

    with open('proxies.txt') as f:
        proxies = [line.strip() for line in f if line.strip()]

    # 确保代理足够（循环使用）
    proxies = proxies * (len(private_keys) // len(proxies) + 1)
    semaphore = asyncio.Semaphore(config.semaphore)
    # 创建并发任务
    tasks = [
        process_account(private_key, proxy, questions)
        for private_key, proxy in zip(private_keys, proxies)
    ]

    async def limited_task(task):
        async with semaphore:
            return await task

    # 分批运行任务（避免内存爆炸）
    batch_size = config.semaphore
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        await asyncio.gather(*[limited_task(t) for t in batch])
        logger.info(f"Completed batch {i // batch_size + 1}/{(len(tasks) - 1) // batch_size + 1}")

    logger.success("All tasks completed")

if __name__ == '__main__':
    asyncio.run(main())

