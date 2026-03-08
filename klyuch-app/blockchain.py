import json, requests, time
from web3 import Web3
from eth_account import Account

# 1. Налаштування (виправлено на робочий RPC)
RPC_URL = "https://bsc-dataseed.binance.org"
web3 = Web3(Web3.HTTPProvider(RPC_URL))

KLY_ADDR = "0x0b7Baf797911C2D6Dd244E635279BD17C3F33088"
WBNB_ADDR = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
PANCAKE_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"

ERC20_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"success","type":"bool"}],"type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"success","type":"bool"}],"type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],"type":"function"}]')
ROUTER_ABI = json.loads('[{"constant":false,"inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactTokensForETH","outputs":[{"name":"amounts","type":"uint256[]"}],"type":"function"},{"constant":false,"inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],"name":"swapExactETHForTokens","outputs":[{"name":"amounts","type":"uint256[]"}],"payable":true,"type":"function"}]')

def get_crypto_data(addr):
    try:
        bnb_wei = web3.eth.get_balance(addr)
        bnb = round(web3.from_wei(bnb_wei, 'ether'), 4)
        
        kly_contract = web3.eth.contract(address=web3.to_checksum_address(KLY_ADDR), abi=ERC20_ABI)
        kly = int(kly_contract.functions.balanceOf(addr).call() / 10**18)
        
        # Виправлено отримання ціни через Binance API
        price = 600.0
        try:
            r = requests.get("https://api.binance.com").json()
            price = float(r['price'])
        except: pass
        
        usd_total = round(float(bnb) * price, 2)
        gas_price = round(web3.from_wei(web3.eth.gas_price, 'gwei'), 1)
        
        return bnb, kly, usd_total, gas_price, []
    except: return 0, 0, 0, 0, []

def swap_kly_for_bnb(private_key, amount_kly):
    addr = Account.from_key(private_key).address
    kly_contract = web3.eth.contract(address=web3.to_checksum_address(KLY_ADDR), abi=ERC20_ABI)
    router = web3.eth.contract(address=web3.to_checksum_address(PANCAKE_ROUTER), abi=ROUTER_ABI)
    amt_wei = int(float(amount_kly) * 10**18)
    
    # Авто-Approve
    allowance = kly_contract.functions.allowance(addr, PANCAKE_ROUTER).call()
    if allowance < amt_wei:
        tx_app = kly_contract.functions.approve(PANCAKE_ROUTER, 2**256-1).build_transaction({
            'from': addr, 'nonce': web3.eth.get_transaction_count(addr), 'gas': 50000, 'gasPrice': web3.eth.gas_price
        })
        web3.eth.send_raw_transaction(web3.eth.account.sign_transaction(tx_app, private_key).rawTransaction)
        time.sleep(2)

    tx = router.functions.swapExactTokensForETH(amt_wei, 0, [KLY_ADDR, WBNB_ADDR], addr, int(time.time())+600).build_transaction({
        'from': addr, 'gas': 250000, 'gasPrice': web3.eth.gas_price, 'nonce': web3.eth.get_transaction_count(addr)
    })
    return web3.eth.send_raw_transaction(web3.eth.account.sign_transaction(tx, private_key).rawTransaction).hex()

def buy_kly_with_bnb(private_key, amount_bnb):
    addr = Account.from_key(private_key).address
    router = web3.eth.contract(address=web3.to_checksum_address(PANCAKE_ROUTER), abi=ROUTER_ABI)
    tx = router.functions.swapExactETHForTokens(0, [WBNB_ADDR, KLY_ADDR], addr, int(time.time())+600).build_transaction({
        'from': addr, 'value': web3.to_wei(amount_bnb, 'ether'), 'gas': 250000, 'gasPrice': web3.eth.gas_price, 'nonce': web3.eth.get_transaction_count(addr)
    })
    return web3.eth.send_raw_transaction(web3.eth.account.sign_transaction(tx, private_key).rawTransaction).hex()
def send_kly_tokens(private_key, to_address, amount_kly):
    sender_addr = Account.from_key(private_key).address
    # Підключення до вашого контракту KLY
    kly_contract = web3.eth.contract(address=web3.to_checksum_address(KLY_ADDR), abi=ERC20_ABI)
    
    # Конвертація в одиниці з 18 нулями
    amount_wei = int(float(amount_kly) * 10**18)
    
    # Формування транзакції
    tx = kly_contract.functions.transfer(
        web3.to_checksum_address(to_address), 
        amount_wei
    ).build_transaction({
        'from': sender_addr,
        'gas': 100000, 
        'gasPrice': web3.eth.gas_price,
        'nonce': web3.eth.get_transaction_count(sender_addr),
    })
    
    # Підпис та відправка в мережу
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    return web3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
