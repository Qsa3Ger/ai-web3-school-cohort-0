#!/usr/bin/env python3
"""
Transaction Decoder — Minimal Practice from AI × Web3 School Handbook
Demonstrates: LLM interpretation vs on-chain facts
"""

import json
import os
import subprocess

RPC = "https://ethereum-rpc.publicnode.com"

def rpc_call(method, params):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1})
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", RPC,
         "-H", "Content-Type: application/json",
         "-d", payload],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

# 1. Fetch latest block
result = rpc_call("eth_blockNumber", [])
latest_block = int(result["result"], 16)
print(f"Latest block: {latest_block}")

# 2. Get block with full tx data
result = rpc_call("eth_getBlockByNumber", [hex(latest_block), True])
txs = result["result"]["transactions"]
print(f"Block has {len(txs)} transactions\n")

# 3. Find first ERC20 transfer
found = False
for tx in txs:
    inp = tx["input"]
    if inp and inp != "0x" and len(inp) >= 138:
        selector = inp[:10]
        if selector not in ["0xa9059cbb", "0x23b872dd"]:
            continue
        
        found = True
        tx_hash = tx["hash"]
        from_addr = tx["from"]
        to_contract = tx.get("to", "none")
        value_wei = int(tx["value"], 16)
        
        print("=" * 60)
        print("TRANSACTION ANALYSIS")
        print("=" * 60)
        print(f"Hash:    {tx_hash}")
        print(f"From:    {from_addr}")
        print(f"To:      {to_contract}")
        print(f"ETH val: {value_wei / 10**18:.6f} ETH\n")

        # Decode the function call
        if selector == "0xa9059cbb":
            # transfer(address to, uint256 amount)
            dest_addr = "0x" + inp[34:74]
            amount_hex = inp[74:138]
            amount = int(amount_hex, 16)
            print(f"Function: transfer(address,uint256)")
            print(f"  To:      {dest_addr}")
            print(f"  Raw amt: {amount}")
            # Try common decimals
            for decimals, name in [(6, "USDC/USDT"), (18, "ETH/WETH"), (8, "WBTC")]:
                print(f"  ≈ {amount / 10**decimals:.6f} ({name} if {decimals} decimals)")
                
        elif selector == "0x23b872dd":
            # transferFrom(address from, address to, uint256 amount)
            src_addr = "0x" + inp[34:74]
            dest_addr = "0x" + inp[98:138]
            amount_hex = inp[138:202]
            amount = int(amount_hex, 16)
            print(f"Function: transferFrom(address,address,uint256)")
            print(f"  From:    {src_addr}")
            print(f"  To:      {dest_addr}")
            print(f"  Raw amt: {amount}")
            for decimals, name in [(6, "USDC/USDT"), (18, "ETH/WETH"), (8, "WBTC")]:
                print(f"  ≈ {amount / 10**decimals:.6f} ({name} if {decimals} decimals)")

        print(f"\n{'=' * 60}")
        print("SEPARATING: ON-CHAIN FACTS vs MODEL INFERENCE")
        print("=" * 60)
        print("\n  ✓ ON-CHAIN FACT: Transaction exists on block")
        print(f"  ✓ ON-CHAIN FACT: Sender = {from_addr[:10]}...{from_addr[-6:]}")
        print(f"  ✓ ON-CHAIN FACT: Contract = {to_contract[:10]}...{to_contract[-6:]}")
        print(f"  ✓ ON-CHAIN FACT: Method signature = {selector}")
        print(f"  ✓ ON-CHAIN FACT: Receiver addr in calldata = {dest_addr[:10]}...{dest_addr[-6:]}")
        print(f"  ✓ ON-CHAIN FACT: Raw amount in calldata = {amount}")
        
        print(f"\n  ❓ MODEL INFERENCE: This is an ERC20 {selector} call")
        print(f"  ❓ MODEL INFERENCE: It's transferring a token, not native ETH")
        print(f"  ❓ MODEL INFERENCE: The actual token value depends on the contract's decimals")
        
        print(f"\n  ⚠️  WHAT YOU SHOULD VERIFY ON ETHERSCAN:")
        print(f"     1. {to_contract} is the expected token address")
        print(f"     2. The receiver {dest_addr} is correct")
        print(f"     3. The amount matches what you expect")
        print(f"     4. Check: https://etherscan.io/tx/{tx_hash}")
        break

if not found:
    print("No ERC20 transfer found in this block. Try a different block.")
