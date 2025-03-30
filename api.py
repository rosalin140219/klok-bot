import asyncio
import base64
import time
import uuid

import aiohttp
import requests
from eth_account import Account
from web3 import Web3
from eth_account.messages import encode_defunct
import secrets
from datetime import datetime, timezone
from config import infura_url
from loguru import logger


class Klok(object):

    def __init__(self, private_key=None, referral_code=None):
        self.private_key = private_key
        self.referral_code = referral_code
        self.address = None
        self.session_token = None

        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "content-type": "application/json",
            "origin": "https://klokapp.ai",
            "priority": "u=1, i",
            "referer": "https://klokapp.ai/",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }

    # 登录验证
    def verify(self):
        # # 1. 连接到以太坊节点（这里使用 Infura 作为示例）
        # w3 = Web3(Web3.HTTPProvider(infura_url))
        #
        # # 检查是否连接成功
        # if not w3.is_connected():
        #     raise Exception("Failed to connect to Ethereum node")

        # 2. 加载钱包私钥
        account = Account.from_key(self.private_key)
        self.address = account.address

        # 3. 生成随机 Nonce
        random_nonce = secrets.token_hex(48)

        # 获取当前时间（UTC 时间）
        current_time = datetime.now(timezone.utc)

        # 格式化为 ISO 8601 格式，带毫秒和时区
        formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


        message = f"""klokapp.ai wants you to sign in with your Ethereum account:
{account.address}


URI: https://klokapp.ai/
Version: 1
Chain ID: 1
Nonce: {random_nonce}
Issued At: {formatted_time}"""
        # 4. 将消息编码为以太坊签名格式
        encoded_message = encode_defunct(text=message)
        # 5. 对消息进行签名
        signed_message = account.sign_message(encoded_message)

        # 6. 组装request对象
        payload = {
            "signedMessage": signed_message.signature.hex(),
            "message": message,
            "referral_code": self.referral_code
        }
        # https://api1-pp.klokapp.ai/v1/verify
        # 发送post请求
        response = requests.post("https://api1-pp.klokapp.ai/v1/verify", json=payload, headers=self.headers)
        if response.status_code != 200:
            logger.error(f"Failed to register: {response.text}")
            return False
        logger.info(f"Successfully registered: {response.text}")
        # 解析response.txt中的session_token
        # 返回的内容为json格式，包含session_token字段:{
        #     "message": "Verification successful",
        #     "session_token": "cVEgp44lCIjyrXhvRjFvg_tPGJ0Kiv13LLTx65CYBS8",
        #     "user_exists": false,
        #     "referral_processed": false
        # }
        session_token = response.json().get("session_token")
        self.session_token = session_token
        return session_token

    # 追踪用户行为
    def track(self):
        # 获取当前时间（UTC 时间）
        current_time = datetime.now(timezone.utc)
        # 格式化为 ISO 8601 格式，带毫秒和时区
        formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        anonymousId = str(uuid.uuid4())
        payload = {
            "properties": {},
            "event": "widget 1 clicked",
            "type": "track",
            "channel": "web",
            "context": {
                "traits": {
                    "user_id": self.address,
                    "display_text": self.address,
                    "auth_provider": "wallet",
                    "user_exists": True,
                    "tier": "free",
                    "language": "en"
                },
                "sessionId": int(time.time()),
                "app": {
                    "name": "RudderLabs JavaScript SDK",
                    "namespace": "com.rudderlabs.javascript",
                    "version": "3.7.7",
                    "installType": "npm"
                },
                "library": {
                    "name": "RudderLabs JavaScript SDK",
                    "version": "3.7.7"
                },
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                "os": {
                    "name": "",
                    "version": ""
                },
                "locale": "zh-CN",
                "screen": {
                    "width": 1728,
                    "height": 1117,
                    "density": 2,
                    "innerWidth": 1728,
                    "innerHeight": 473
                },
                "campaign": {},
                "page": {
                    "path": "/app",
                    "referrer": "https://klokapp.ai/app",
                    "referring_domain": "klokapp.ai",
                    "search": "",
                    "title": "Klok - Trustless verified intelligence on command",
                    "url": "https://klokapp.ai/app",
                    "tab_url": "https://klokapp.ai/app",
                    "initial_referrer": "$direct",
                    "initial_referring_domain": ""
                },
                "timezone": "GMT+0800"
            },
            "originalTimestamp": formatted_time,
            "integrations": {
                "All": True
            },
            "messageId": str(uuid.uuid4()),
            "userId": self.address,
            "anonymousId": anonymousId,
            "sentAt": formatted_time
        }
        headers = self.headers
        headers["Anonymousid"] = base64.b64encode(anonymousId.encode('utf-8')).decode('utf-8')
        headers["Authorization"] = "Basic MnQ5eFZ0RXVRalJneU9tQThMM0M5NU9odEhHOg=="
        response = requests.post("https://arohalabssxygl.dataplane.rudderstack.com/v1/track", json=payload,
                                 headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to track: {response.text}")
            return False
        logger.info(f"Successfully tracked: {response.text}")
        return True

    # 获取用户信息
    def get_user_info(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/me", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.text}")
            return False
        logger.info(f"Successfully get user info: {response.text}")
        return response.json()

    # 获取模型列表
    def get_models(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/models", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get models: {response.text}")
            return False
        logger.info(f"Successfully get models: {response.text}")
        models = response.json()
        active_models = [item["name"] for item in models if item["active"]]
        logger.info(f"Successfully get models: {active_models}")
        return active_models

    # 获取分数详情
    def get_points(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/points", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get points: {response.text}")
            return False
        logger.info(f"Successfully get points: {response.text}")
        return response.json()

    # 获取推荐统计
    def referral_stats(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/referral/stats", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get referral stats: {response.text}")
            return False
        logger.info(f"Successfully get referral stats: {response.text}")
        return response.json()

    def rate_limit(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/rate-limit", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get rate limit: {response.text}")
            return False
        logger.info(f"Successfully get rate limit: {response.text}")
        return response.json()

    # klok 推特是否完成
    def twitter_klok_completed(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/points/action/twitter_klok", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get twitter klok completed: {response.text}")
            return False
        logger.info(f"Successfully get twitter klok completed: {response.text}")
        data = response.json()
        has_completed = data.get("has_completed")
        return has_completed

    # mira 推特是否完成
    def twitter_mira_completed(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/points/action/twitter_mira", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get twitter mira completed: {response.text}")
            return False
        logger.info(f"Successfully get twitter mira completed: {response.text}")
        data = response.json()
        has_completed = data.get("has_completed")
        return has_completed

    # discord 是否完成
    def discord_completed(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.get("https://api1-pp.klokapp.ai/v1/points/action/discord", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to get twitter mira completed: {response.text}")
            return False
        logger.info(f"Successfully get twitter mira completed: {response.text}")
        data = response.json()
        has_completed = data.get("has_completed")
        return has_completed

    # follow klok
    def follow_klok(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.post("https://api1-pp.klokapp.ai/v1/points/action/twitter_klok", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to follow twitter klok: {response.text}")
            return False
        logger.info(f"Successfully follow twitter klok completed: {response.text}")
        return True

        # mira 推特是否完成
    def follow_mira(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.post("https://api1-pp.klokapp.ai/v1/points/action/twitter_mira", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to follow twitter mira: {response.text}")
            return False
        logger.info(f"Successfully follow mira : {response.text}")
        return True

    # join discord
    def join_discord(self):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token
        response = requests.post("https://api1-pp.klokapp.ai/v1/points/action/discord", headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to join discord: {response.text}")
            return False
        logger.info(f"Successfully join discord: {response.text}")
        return True

    # 聊天
    def chat(self, messages: list, chat_id: str, model: str = "llama-3.3-70b-instruct"):
        headers = self.headers
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            self.verify()
        headers["x-session-token"] = self.session_token

        """发送聊天请求"""
        try:
            chat_data = {
                "id": chat_id,
                "title": "",
                "messages": messages,
                "sources": [],
                "model": model,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "language": "english"
            }

            # 设置超时（单位：秒）
            timeout = 240  # 4分钟超时
            full_response = ""
            # 发送 POST 请求
            start_time = datetime.now()
            try:
                response = requests.post(
                    'https://api1-pp.klokapp.ai/v1/chat',
                    json=chat_data,
                    headers=headers,
                    verify=False,  # 忽略 SSL 验证
                    timeout=timeout
                )
                if response.status_code != 200:
                    logger.error(f'聊天请求失败: {response.status_code}')
                    return False
                # 处理流式响应
                logger.info(f'开始接收流式响应')
                for line in response.iter_lines():
                    # 检查是否超过4分钟
                    current_time = datetime.now()
                    if (current_time - start_time).total_seconds() > timeout:
                        logger.warning(f'聊天超过4分钟，断开连接')
                        return True
                    # 可选：处理 event-stream 数据
                    if line:
                        try:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data:'):
                                data = decoded_line[5:].strip()
                                if data == '[DONE]':
                                    break
                            full_response += decoded_line + "\n"
                        except Exception as e:
                            pass  # 忽略解析错误，继续接收数据
                logger.success(f'聊天完成')
                return full_response
            except requests.Timeout:
                logger.error(f'聊天请求超时')
                return full_response
            except Exception as e:
                logger.error(f'处理聊天流式响应异常: {e}')
                return full_response
        except Exception as e:
            logger.error(f'发送聊天请求异常: {e}')
            return ""
