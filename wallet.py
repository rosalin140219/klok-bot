from eth_account import Account


if __name__ == '__main__':

    for i in range(1000):
        account = Account.create()
        # 将私钥保存到文件
        with open("all_private_keys.txt", "a") as f:
            f.write(account.key.hex() + "\n")
