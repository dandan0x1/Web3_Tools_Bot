import os
from cryptography.fernet import Fernet

# 加密主密钥（用于加解密，请勿与密文混淆）
KEY_FILE = "secret.key"
# 加密后的密文保存位置
CIPHER_FILE = "encrypted.txt"

def is_valid_fernet_key(key: bytes) -> bool:
    try:
        Fernet(key)
        return True
    except Exception:
        return False

def load_or_create_key():
    """加载现有主密钥，如果没有或无效则创建一个新的"""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            key = f.read().strip()
            if len(key) == 0 or not is_valid_fernet_key(key):
                print(f"[!] 警告：{KEY_FILE} 内容无效（可能误存了密文），正在重新生成主密钥...")
                return create_new_key()
            return key
    else:
        return create_new_key()

def create_new_key():
    """生成并保存新密钥"""
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    print(f"[*] 已生成并保存加密主密钥至: {KEY_FILE}")
    print(f"[*] 注意：{KEY_FILE} 存的是主密钥，密文会保存到 {CIPHER_FILE}")
    return key

def main():
    try:
        key = load_or_create_key()
        cipher_suite = Fernet(key)
    except Exception as e:
        print(f"\n[!] 密钥错误: {e}")
        print(f"[!] 请尝试删除当前目录下的 {KEY_FILE} 文件后重试。")
        return

    while True:
        print("\n=== 安全加密助手 ===")
        print("1. 加密文本 (Encrypt)")
        print("2. 还原文本 (Decrypt)")
        print("3. 退出 (Exit)")
        
        choice = input("\n请选择操作序号: ").strip()

        if choice == '1':
            text = input("请输入要加密的原始文本: ").strip()
            if text:
                encrypted_text = cipher_suite.encrypt(text.encode())
                ciphertext = encrypted_text.decode()
                with open(CIPHER_FILE, "w", encoding="utf-8") as f:
                    f.write(ciphertext)
                print(f"\n[+] 加密成功！密文如下：\n{ciphertext}")
                print(f"[+] 密文已保存至: {CIPHER_FILE}")
            else:
                print("[-] 输入不能为空")

        elif choice == '2':
            if os.path.exists(CIPHER_FILE):
                use_file = input(f"检测到 {CIPHER_FILE}，直接读取？(Y/n): ").strip().lower()
                if use_file in ("", "y", "yes"):
                    with open(CIPHER_FILE, "r", encoding="utf-8") as f:
                        token = f.read().strip()
                    print(f"[*] 已从 {CIPHER_FILE} 读取密文")
                else:
                    token = input("请输入要还原的密文: ").strip()
            else:
                token = input("请输入要还原的密文: ").strip()
            if token:
                try:
                    decrypted_text = cipher_suite.decrypt(token.encode()).decode()
                    print(f"\n[+] 还原成功！原始文本为：\n{decrypted_text}")
                except Exception:
                    print("\n[!] 还原失败：密文无效、已损坏或密钥不匹配！")
            else:
                print("[-] 输入不能为空")

        elif choice == '3':
            print("程序已退出。")
            break
        else:
            print("[-] 无效选择。")

if __name__ == "__main__":
    main()
