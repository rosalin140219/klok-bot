import base64
import time
import uuid
from datetime import datetime, timezone

from urllib.parse import urlparse

from eth_account import Account
from eth_account.messages import encode_defunct
import secrets
from web3 import Web3
from web3.eth import AsyncEth
from web3.providers.async_rpc import AsyncHTTPProvider
from loguru import logger
from config import infura_url
from curl_cffi.requests import AsyncSession
import aiohttp
from aiohttp import BasicAuth


class AsyncKlok:
    def __init__(self, private_key=None, referral_code=None, proxy=None):
        self.private_key = private_key
        self.referral_code = referral_code
        self.address = None
        self.session_token = None
        self.proxies = {"http": proxy, "https": proxy}
        self.session = AsyncSession(impersonate="chrome124", verify=False)  # 创建一次，重复使用
        if proxy:
            parsed = urlparse(proxy)
            # 提取认证信息
            if parsed.username and parsed.password:
                self.proxy_auth = BasicAuth(login=parsed.username, password=parsed.password)
            else:
                self.proxy_auth = None

            # 构建代理地址 (去除认证信息)
            proxy_host = f"{parsed.hostname}:{parsed.port}"

            self.aio_proxies = {
                "http": f"{parsed.scheme}://{proxy_host}",
                "https": f"{parsed.scheme}://{proxy_host}"  # 注意保持scheme一致
            }
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

    async def verify(self):
        # # Initialize async Web3
        # w3 = Web3(
        #     AsyncHTTPProvider(infura_url),
        #     modules={'eth': (AsyncEth,)},
        #     middlewares=[]
        # )
        #
        # # Check connection
        # if not await w3.is_connected():
        #     raise Exception("Failed to connect to Ethereum node")

        # Load account
        account = Account.from_key(self.private_key)
        self.address = account.address

        # Generate random Nonce
        random_nonce = secrets.token_hex(48)
        current_time = datetime.now(timezone.utc)
        formatted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        message = f"""klokapp.ai wants you to sign in with your Ethereum account:
{account.address}


URI: https://klokapp.ai/
Version: 1
Chain ID: 1
Nonce: {random_nonce}
Issued At: {formatted_time}"""

        # Sign message
        encoded_message = encode_defunct(text=message)
        signed_message = account.sign_message(encoded_message)

        payload = {
            "signedMessage": signed_message.signature.hex(),
            "message": message,
            "referral_code": self.referral_code
        }
        # request_kwargs = self._prepare_proxy()

        # session = AsyncSession(impersonate="chrome124", verify=False)

        response = await self.session.post(
            "https://api1-pp.klokapp.ai/v1/verify",
            json=payload,
            headers=self.headers,
            proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to register: {response.text}")
            return False

        data = response.json()
        logger.info(f"Successfully registered: {data}")
        self.session_token = data.get("session_token")
        return self.session_token

    async def track(self):
        current_time = datetime.now(timezone.utc)
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

        headers = self.headers.copy()
        headers["Anonymousid"] = base64.b64encode(anonymousId.encode('utf-8')).decode('utf-8')
        headers["Authorization"] = "Basic MnQ5eFZ0RXVRalJneU9tQThMM0M5NU9odEhHOg=="
        # request_kwargs = self._prepare_proxy()
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.post(
                "https://arohalabssxygl.dataplane.rudderstack.com/v1/track",
                json=payload,
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to track: {response.text}")
            return False
        logger.info(f"Successfully tracked: {response.text}")
        return True

    async def get_user_info(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/me",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.text}")
            return False
        data = response.json()
        logger.info(f"Successfully get user info: {data}")
        return data

    async def get_models(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/models",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get models: {response.text}")
            return False
        models = response.json()
        active_models = [item["name"] for item in models if item["active"]]
        logger.info(f"Successfully get models: {active_models}")
        return active_models

    async def get_points(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/points",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get points: {response.text}")
            return False
        data = response.json()
        logger.info(f"Successfully get points: {data}")
        return data

    async def referral_stats(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/referral/stats",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get referral stats: {response.text}")
            return False
        data = response.json()
        logger.info(f"Successfully get referral stats: {data}")
        return data

    async def rate_limit(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/rate-limit",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get rate limit: {response.text}")
            return False
        data = response.json()
        logger.info(f"Successfully get rate limit: {data}")
        return data

    async def twitter_klok_completed(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/points/action/twitter_klok",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get twitter klok completed: {response.text}")
            return False
        data = response.json()
        has_completed = data.get("has_completed")
        logger.info(f"Successfully get twitter klok completed: {has_completed}")
        return has_completed

    async def twitter_mira_completed(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/points/action/twitter_mira",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get twitter mira completed: {response.text}")
            return False
        data = response.json()
        has_completed = data.get("has_completed")
        logger.info(f"Successfully get twitter mira completed: {has_completed}")
        return has_completed

    async def discord_completed(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.get(
                "https://api1-pp.klokapp.ai/v1/points/action/discord",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to get discord completed: {response.text}")
            return False
        data = response.json()
        has_completed = data.get("has_completed")
        logger.info(f"Successfully get discord completed: {has_completed}")
        return has_completed

    async def follow_klok(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.post(
                "https://api1-pp.klokapp.ai/v1/points/action/twitter_klok",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to follow twitter klok: {response.text}")
            return False
        logger.info(f"Successfully follow twitter klok: {response.text}")
        return True

    async def follow_mira(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.post(
                "https://api1-pp.klokapp.ai/v1/points/action/twitter_mira",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to follow twitter mira: {response.text}")
            return False
        logger.info(f"Successfully follow twitter mira: {response.text}")
        return True

    async def join_discord(self):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token
        # session = AsyncSession(impersonate="chrome124", verify=False)
        response = await self.session.post(
                "https://api1-pp.klokapp.ai/v1/points/action/discord",
                headers=headers,
                proxies=self.proxies
        )
        if response.status_code != 200:
            logger.error(f"Failed to join discord: {response.text}")
            return False
        logger.info(f"Successfully join discord: {response.text}")
        return True

    async def chat(self, messages: list, chat_id: str, model: str = "llama-3.3-70b-instruct"):
        if not self.session_token:
            logger.error("Session token is missing, try to verify first")
            await self.verify()

        headers = self.headers.copy()
        headers["x-session-token"] = self.session_token

        chat_data = {
            "id": chat_id,
            "title": "",
            "messages": messages,
            "sources": [],
            "model": model,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "language": "english"
        }
        full_response = ""
        timeout = aiohttp.ClientTimeout(total=240)  # 4 minutes timeout
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        'https://api1-pp.klokapp.ai/v1/chat',
                        json=chat_data,
                        headers=headers,
                        timeout=timeout,
                        proxy=self.aio_proxies["https"],  # 使用https代理配置
                        proxy_auth=self.proxy_auth  # 添加代理认证
                ) as response:
                    if response.status != 200:
                        logger.error(f'Chat request failed: {response.status}')
                        return False

                    logger.info('Starting to receive stream response')
                    async for line in response.content:  # 真正的异步流
                        line = line.decode('utf-8').strip()
                        if line.startswith('data:'):
                            data = line[5:].strip()
                            if data == '[DONE]':
                                break
                            # 处理数据
                        full_response += line + "\n"
                return full_response
        except Exception as e:
            logger.error(f'Error: {e}')
            return full_response
