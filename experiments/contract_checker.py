import json, os, subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
RPC = "https://ethereum-rpc.publicnode.com"

def rpc(method, params):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1})
    r = subprocess.run(["curl","-s","-X","POST",RPC,"-H","Content-Type: application/json","-d",payload],
                       capture_output=True,text=True)
    return json.loads(r.stdout)

contracts = {
    "USDT (已知安全)": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "前面找到的未知合约": "0x32f223e5c09878823934a8116f289bae2b657b8e"
}

for name, addr in contracts.items():
    print(f"\n{'='*60}")
    print(f"🔍 {name}")
    print(f"地址: {addr}")
    print("="*60)
    
    # 1. Transaction count (nonce)
    r = rpc("eth_getTransactionCount", [addr, "latest"])
    tx_count = int(r["result"], 16)
    print(f"交易数(nonce): {tx_count}")
    
    # 2. Code size (EOA vs Contract)
    r = rpc("eth_getCode", [addr, "latest"])
    code = r["result"]
    has_code = code != "0x"
    print(f"有合约代码: {'✅ 是合约' if has_code else '❌ 是普通地址(EOA)'}")
    print(f"代码长度: {len(code)//2 - 1 if has_code else 0} bytes")
    
    # 3. Balance
    r = rpc("eth_getBalance", [addr, "latest"])
    balance = int(r["result"], 16)
    print(f"ETH余额: {balance / 10**18:.6f} ETH")
    
    # 4. Check if the contract itself has transactions (age)
    r = rpc("eth_getBlockByNumber", ["0x0", False])
    # simple age check: compare creation block via first tx
    # Get the nonce at genesis
    r = rpc("eth_getTransactionCount", [addr, "0x0"])
    genesis_nonce = int(r.get("result","0x0"), 16)
    r = rpc("eth_getTransactionCount", [addr, "latest"])
    latest_nonce = int(r.get("result","0x0"), 16)
    print(f"起源nonce: {genesis_nonce}, 当前nonce: {latest_nonce}")
    
    # Simple heuristic: old contracts have lots of history
    # Let's check if it's been used recently by looking at some recent blocks
    
    print()
