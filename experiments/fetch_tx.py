import json, sys, urllib.request

RPC = "https://ethereum-rpc.publicnode.com"

def rpc_call(method, params):
    data = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1}).encode()
    req = urllib.request.Request(RPC, data=data, headers={"Content-Type":"application/json"})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["result"]

# Get latest block
block = rpc_call("eth_blockNumber", [])
print(f"Latest block: {int(block,16)} ({block})")

# Get block with full tx objects
blk = rpc_call("eth_getBlockByNumber", [block, True])
txs = blk["transactions"]
print(f"Transactions in block: {len(txs)}\n")

# Find first interesting tx (with input data)
for tx in txs:
    inp = tx["input"]
    to = tx.get("to")
    if inp and inp != "0x" and len(inp) >= 138:
        print("=== Transaction ===")
        print(f"Hash:  {tx['hash']}")
        print(f"From:  {tx['from']}")
        print(f"To:    {to}")
        print(f"Value: {int(tx['value'],16)} wei")
        print(f"Gas:   {int(tx['gas'],16)}")
        print(f"Input: {inp}")
        
        # Try to decode: first 4 bytes = function selector
        selector = inp[:10]  # 0x + 8 hex chars
        print(f"\nFunction selector: {selector}")
        
        # If it's a transfer to an EOA (no data needed from contract), we got it
        # For ERC20 transfer: 0xa9059cbb + 32 bytes to + 32 bytes amount
        if len(inp) >= 138:  # 0x + 4 + 32 + 32 = 138 hex chars
            to_addr = "0x" + inp[34:74]
            amount_hex = inp[74:138]
            amount = int(amount_hex, 16)
            print(f"\nDecoded as potential ERC20 transfer:")
            print(f"  To:     {to_addr}")
            print(f"  Amount: {amount}")
            print(f"  (Human: {amount / 10**6:.2f} if 6-decimal token like USDC)")
        break
