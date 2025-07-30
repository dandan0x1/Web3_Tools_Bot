import requests
import time
import os
import json
from http.cookies import SimpleCookie

# Config
CONFIG = {
    'FAUCET_URL': 'https://faucet.xion.burnt.com/api/credit',
    'CHAIN_ID': 'xion-testnet-2',
    'DENOM': 'uxion',
    'DELAY_BETWEEN_REQUESTS': 5,  # seconds
    'MAX_RETRIES': 3,
    'CAPSOLVER_API_URL': 'https://api.capsolver.com'
}

class CFBot:
    def __init__(self, config_file='config/xion_cf_config.json'):
        self.config_file = config_file
        self.config = None
        self.urls = []
        self.data = {}
        self.headers = {"Content-Type": "application/json"}
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            self.urls = self.config['urls']
            self.data = {
                'type': self.config['type'],
                'websiteUrl': self.config['websiteUrl'],
                'websiteKey': self.config['websiteKey']
            }
            print("配置加载成功")
            return True
        except Exception as e:
            print(f"配置加载失败: {e}")
            return False
    
    def send_request(self, url):
        """发送单个请求，返回token字符串"""
        try:
            response = requests.post(url, json=self.data, headers=self.headers, timeout=10)
            print(f"URL: {url} | 状态码: {response.status_code}")
            print(response.text)
            if response.status_code == 200 and response.text.strip():
                # 尝试解析token
                try:
                    data = response.json()
                    token = data.get('token')
                    if token:
                        print(f"成功获取 {url} 的token")
                        return token
                except Exception:
                    # 兼容返回不是json的情况
                    import re
                    match = re.search(r'"token"\s*:\s*"([^"]+)"', response.text)
                    if match:
                        token = match.group(1)
                        print(f"成功获取 {url} 的token")
                        return token
                print(f"{url} 响应无有效token，尝试下一个...")
                return None
            else:
                print(f"{url} 无有效响应，尝试下一个...")
                return None
        except Exception as e:
            print(f"{url} 请求出错: {e}，尝试下一个...")
            return None
    
    def run(self):
        """运行轮询逻辑，返回第一个获取到的token"""
        if not self.load_config():
            return None
        for url in self.urls:
            token = self.send_request(url)
            if token:
                return token  # 找到有效token，退出循环
        return None

def load_env(env_path='config/capsolver_api.txt'):
    env = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    env[k.strip()] = v.strip()
    except Exception as e:
        print(f'❌ 读取env文件出错: {e}')
    return env

def load_wallets():
    try:
        with open('config/xion_wall.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f'❌ 读取钱包文件出错: {e}')
        return []

def load_proxies():
    try:
        with open('config/proxy.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f'❌ 读取代理文件出错: {e}')
        return []

def create_capsolver_task(api_key):
    print('🔄 正在创建Capsolver任务...')
    url = f"{CONFIG['CAPSOLVER_API_URL']}/createTask"
    payload = {
        'clientKey': api_key,
        'task': {
            'type': 'AntiTurnstileTaskProxyLess',
            'websiteURL': 'https://faucet.xion.burnt.com/',
            'websiteKey': '0x4AAAAAAA5DeCW7T-bO0I0V',
            'metadata': {
                'action': 'managed',
                'cdata': 'blob'
            }
        }
    }
    r = requests.post(url, json=payload)
    data = r.json()
    if data.get('errorId') == 0:
        print('✅ 任务创建成功:', data['taskId'])
        return data['taskId']
    else:
        raise Exception(f"Capsolver错误: {data.get('errorDescription')}")

def get_capsolver_result(api_key, task_id):
    print('⏳ 等待验证码结果...')
    url = f"{CONFIG['CAPSOLVER_API_URL']}/getTaskResult"
    attempts = 0
    max_attempts = 60
    while attempts < max_attempts:
        payload = {'clientKey': api_key, 'taskId': task_id}
        r = requests.post(url, json=payload)
        data = r.json()
        if data.get('errorId') == 0:
            if data.get('status') == 'ready':
                print('✅ 验证码已解决!')
                return data['solution']['token']
            elif data.get('status') == 'processing':
                attempts += 1
                time.sleep(2)
            else:
                raise Exception(f"未知状态: {data.get('status')}")
        else:
            raise Exception(f"Capsolver错误: {data.get('errorDescription')}")
    raise Exception('等待验证码超时')

def solve_captcha(api_key):
    task_id = create_capsolver_task(api_key)
    token = get_capsolver_result(api_key, task_id)
    print('📝 获取到Token:', token[:30] + '...')
    return token

def get_session_cookies(proxy=None):
    session = requests.Session()
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }
    r = session.get('https://faucet.xion.burnt.com/', headers=headers, allow_redirects=True, timeout=30, verify=False)
    cookies = r.cookies.get_dict()
    cookie_string = '; '.join([f'{k}={v}' for k, v in cookies.items()])
    print('🍪 获取到Cookies:', ', '.join(cookies.keys()))
    return cookie_string

def claim_faucet(wallet, proxy, cookie_string, captcha_token):
    session = requests.Session()
    if proxy:
        session.proxies = {'http': proxy, 'https': proxy}
    payload = {
        'address': wallet,
        'chainId': CONFIG['CHAIN_ID'],
        'denom': CONFIG['DENOM'],
        'token': captcha_token
    }
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://faucet.xion.burnt.com',
        'Referer': 'https://faucet.xion.burnt.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Sec-CH-UA': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cookie': cookie_string
    }
    print('📤 正在发送领取请求...')
    r = session.post(CONFIG['FAUCET_URL'], json=payload, headers=headers, timeout=30, verify=False)
    print('📥 返回状态码:', r.status_code)
    if r.status_code == 200:
        return r.json()
    else:
        # 友好错误提示
        try:
            data = r.json()
            msg = data.get('message', '')
            if 'Too many requests' in msg:
                print(f'⚠️  该钱包领取过于频繁，请稍后再试！\n详细信息: {msg}')
            else:
                print(f'❌ 领取失败，服务器返回: {msg or r.text}')
        except Exception:
            print(f'❌ 领取失败，服务器返回未知错误，状态码: {r.status_code}')
        raise Exception(f"领取失败，HTTP {r.status_code}")

def process_wallet(wallet, proxy, api_key, index):
    print(f"\n{'='*60}")
    print(f"🔄 正在处理第{index+1}个钱包: {wallet}")
    print(f"📡 使用代理: {proxy or '无代理'}")
    retries = 0
    while retries < CONFIG['MAX_RETRIES']:
        try:
            print('\n1️⃣ 获取会话...')
            cookie_string = get_session_cookies(proxy)
            print('\n2️⃣ 解决验证码...')
            captcha_token = solve_captcha(api_key)
            print('\n3️⃣ 领取水龙头...')
            result = claim_faucet(wallet, proxy, cookie_string, captcha_token)
            print(f"\n✅ 成功! 钱包 {wallet}:")
            amount = result.get('convertedAmount', result.get('amount', {})).get('amount')
            denom = result.get('convertedAmount', result.get('amount', {})).get('denom')
            print(f"   💰 数量: {amount} {denom}")
            print(f"   📊 交易哈希: {result.get('transactionHash')}")
            print(f"   📏 区块高度: {result.get('height')}")
            return True
        except Exception as e:
            retries += 1
            print(f"\n❌ 第{retries}次出错: {e}")
            if retries < CONFIG['MAX_RETRIES']:
                print('⏳ 10秒后重试...')
                time.sleep(10)
            else:
                print(f"❌ 钱包 {wallet} 连续{CONFIG['MAX_RETRIES']}次失败，跳过")
    return False

def check_capsolver_balance(api_key):
    url = f"{CONFIG['CAPSOLVER_API_URL']}/getBalance"
    payload = {'clientKey': api_key}
    try:
        r = requests.post(url, json=payload)
        data = r.json()
        if data.get('errorId') == 0:
            print(f"💳 Capsolver余额: ${data['balance']}")
            if data['balance'] < 1:
                print('⚠️  警告: Capsolver余额不足!')
        else:
            print('❌ 查询余额失败:', data.get('errorDescription'))
    except Exception as e:
        print(f'❌ 查询余额出错: {e}')

def main():
    # 优先判断CFBot配置文件是否存在
    cf_config_path = 'config/xion_cf_config.json'
    if os.path.exists(cf_config_path):
        print('检测到config/xion_cf_config.json，优先使用CFBot验证...')
        cf_bot = CFBot(cf_config_path)
        token = cf_bot.run()
        if not token:
            print('❌ 未能通过CFBot获取到有效token，无法继续领水！')
            return
        wallets = load_wallets()
        proxies = load_proxies()
        if not wallets:
            print('❌ config/xion_wall.txt文件中未找到钱包!')
            return
        print(f"\n📊 钱包总数: {len(wallets)}")
        print(f"📊 代理总数: {len(proxies)}")
        success_count = 0
        fail_count = 0
        start_time = time.time()
        for i, wallet in enumerate(wallets):
            proxy = proxies[i % len(proxies)] if proxies else None
            print(f"\n{'='*60}")
            print(f"🔄 正在处理第{i+1}个钱包: {wallet}")
            print(f"📡 使用代理: {proxy or '无代理'}")
            try:
                print('\n1️⃣ 获取会话...')
                cookie_string = get_session_cookies(proxy)
                print('\n2️⃣ 使用CFBot获取的token领取水龙头...')
                result = claim_faucet(wallet, proxy, cookie_string, token)
                print(f"\n✅ 成功! 钱包 {wallet}:")
                amount = result.get('convertedAmount', result.get('amount', {})).get('amount')
                denom = result.get('convertedAmount', result.get('amount', {})).get('denom')
                print(f"   💰 数量: {amount} {denom}")
                print(f"   📊 交易哈希: {result.get('transactionHash')}")
                print(f"   📏 区块高度: {result.get('height')}")
                success_count += 1
            except Exception as e:
                print(f"\n❌ 领取失败: {e}")
                fail_count += 1
            progress = ((i+1)/len(wallets))*100
            print(f"\n📈 进度: {i+1}/{len(wallets)} ({progress:.1f}%)")
            if i < len(wallets) - 1:
                print(f"⏳ 等待 {CONFIG['DELAY_BETWEEN_REQUESTS']} 秒后继续...")
                time.sleep(CONFIG['DELAY_BETWEEN_REQUESTS'])
        duration = (time.time() - start_time) / 60
        print('\n' + '='*60)
        print('📊 最终统计:')
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失败: {fail_count}")
        print(f"⏱️  总耗时: {duration:.2f} 分钟")
        print(f"💰 成功率: {(success_count/len(wallets))*100:.1f}%")
        print('🏁 机器人运行结束!')
        return
    else:
        print('未检测到config/xion_cf_config.json，使用Capsolver验证...')
    # 以下为原有Capsolver流程
    print('🚀 启动XION水龙头机器人...\n')
    print(f"⏰ 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    env = load_env('config/capsolver_api.txt')
    api_key = env.get('CAPSOLVER_API_KEY')
    if not api_key:
        print('❌ 错误: config/capsolver_api.txt文件未找到CAPSOLVER_API_KEY!')
        exit(1)
    check_capsolver_balance(api_key)
    wallets = load_wallets()
    proxies = load_proxies()
    if not wallets:
        print('❌ config/xion_wall.txt文件中未找到钱包!')
        exit(1)
    print(f"\n📊 钱包总数: {len(wallets)}")
    print(f"📊 代理总数: {len(proxies)}")
    success_count = 0
    fail_count = 0
    start_time = time.time()
    for i, wallet in enumerate(wallets):
        proxy = proxies[i % len(proxies)] if proxies else None
        if wallet:
            success = process_wallet(wallet, proxy, api_key, i)
            if success:
                success_count += 1
            else:
                fail_count += 1
            progress = ((i+1)/len(wallets))*100
            print(f"\n📈 进度: {i+1}/{len(wallets)} ({progress:.1f}%)")
            if i < len(wallets) - 1:
                print(f"⏳ 等待 {CONFIG['DELAY_BETWEEN_REQUESTS']} 秒后继续...")
                time.sleep(CONFIG['DELAY_BETWEEN_REQUESTS'])
    duration = (time.time() - start_time) / 60
    print('\n' + '='*60)
    print('📊 最终统计:')
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"⏱️  总耗时: {duration:.2f} 分钟")
    print(f"💰 成功率: {(success_count/len(wallets))*100:.1f}%")
    print('🏁 机器人运行结束!')

if __name__ == '__main__':
    main() 
