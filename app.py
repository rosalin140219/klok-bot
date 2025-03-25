import random
import time

from api import Klok
import config
from loguru import logger

if __name__ == '__main__':
    private_keys = []
    with open("private_keys.txt") as f:
        for line in f:
            line = line.strip()
            private_keys.append(line)

    # 读取questions.txt文件中的问题
    with open("questions.txt") as f:
        questions = f.readlines()

    klok = Klok(private_key=private_keys[0], referral_code=config.referral_code)
    # 校验klok推特
    twitter_klok_completed = klok.twitter_klok_completed()
    if not twitter_klok_completed:
        klok.follow_klok()
    # 校验mira推特
    twitter_mira_completed = klok.twitter_mira_completed()
    if not twitter_mira_completed:
        klok.follow_mira()
    # 校验discord
    discord = klok.discord_completed()
    if not discord:
        klok.join_discord()
    messages = []
    # 选择模型
    klok.track()
    models = klok.get_models()
    # 随机选择一个模型
    model = random.choice(models)
    while True:
        rate_limit = klok.rate_limit()
        remaining = rate_limit['remaining']
        # 如果剩余次数为0，则等待rate_limit['reset']秒后再次请求
        if remaining <= 0:
            logger.warning("Rate limit exceeded, please try again later.")
            break
        # 随机选择问题
        question = random.choice(questions).strip()
        # 回复问题
        messages.append({"role": "user", "content": question})
        response = klok.chat(messages, model)
        messages.append({"role": "assistant", "content": response})
        # 休眠1-10秒
        time.sleep(random.randint(1, 10))
