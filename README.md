# 多号版本：
1. 安装依赖
    ``` 
    pip install -r requirements.txt
    ```
2. 邀请码
在config.py中配置邀请码，变量referral_code
3. 以太坊主网网络rpc地址
infura_url = "https://mainnet.infura.io/v3/****"
可以去https://developer.metamask.io/申请
4. 配置私钥
在private_keys.txt中配置钱包私钥，一行一个
5. 配置代理
在proxies.txt中配置代理，一行一个，保证代理数量大于等于私钥数量
6. 设置脚本的并发度
在config.py中配置config.semaphore，设置脚本的并发度，默认为10个，可以不改。
7. 运行脚本
    ``` 
    python3 async_app.py
    ```
8. 修改问题
可以自己在questions.txt中修改问题，一行一个


# 单号版本：
1. 安装依赖
    ``` 
    pip install -r requirements.txt
    ```
2. 邀请码
在config.py中配置邀请码，变量referral_code
3. 以太坊主网网络rpc地址
infura_url = "https://mainnet.infura.io/v3/****"
可以去https://developer.metamask.io/申请
4. 配置私钥
在private_keys.txt中配置钱包私钥，一行一个
5. 运行脚本
    ``` 
    python3 app.py
    ```
6. 修改问题
可以自己在questions.txt中修改问题，一行一个