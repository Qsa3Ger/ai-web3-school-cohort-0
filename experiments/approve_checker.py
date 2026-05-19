"""
Wallet Approve Checker — Minimal Practice from AI × Web3 Handbook Context chapter

Steps:
1. Fetch real on-chain data for a USDT approve transaction
2. Build a context with clear data source labels
3. Generate the prompt that could be sent to LLM
"""

import json
import os
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
RPC = "https://ethereum-rpc.publicnode.com"

def rpc(method, params):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params,"id":1})
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", RPC,
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

# === STEP 0: constants ===
USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

# === STEP 1: Find a real approve transaction ===
print("=" * 60)
print("STEP 1: Finding a real approve tx on Ethereum")
print("=" * 60)

result = rpc("eth_blockNumber", [])
block_num = int(result["result"], 16)
print(f"Latest block: {block_num}")

found_tx = None
for offset in range(5):
    result = rpc("eth_getBlockByNumber", [hex(block_num - offset), True])
    txs = result["result"]["transactions"]
    for tx in txs:
        inp = tx["input"]
        if inp and inp.startswith("0x095ea7b3") and len(inp) >= 138:
            found_tx = tx
            break
    if found_tx:
        print(f"Found approve tx in block {block_num - offset}")
        break

if not found_tx:
    print("No real approve tx found. Using a simulated one.")
    from_addr = "0xUser000000000000000000000000000000000001"
    spender  = "0xSpender00000000000000000000000000000002"
    amount   = 2**256 - 1  # unlimited
    token_addr = USDT
    tx_hash = "SIMULATED_TX"
else:
    from_addr = found_tx["from"]
    token_addr = found_tx["to"]
    inp = found_tx["input"]
    tx_hash = found_tx["hash"]
    spender = "0x" + inp[34:74]
    amount = int(inp[74:138], 16)
    is_unlimited = amount > 10**30

print(f"From:     {from_addr}")
print(f"Token:    {token_addr}")
print(f"Spender:  {spender}")
print(f"Amount:   {amount}")
print(f"Is unlimited: {amount > 10**30}")

# === STEP 2: Get on-chain state ===
print(f"\n{'=' * 60}")
print("STEP 2: Query on-chain state")
print("=" * 60)

allowance_data = "0xdd62ed3e" + from_addr[2:].zfill(64) + spender[2:].zfill(64)
payload = json.dumps({
    "jsonrpc":"2.0","method":"eth_call",
    "params":[{"to": token_addr, "data": allowance_data}, hex(block_num)],"id":1
})
result = subprocess.run(
    ["curl", "-s", "-X", "POST", RPC,
     "-H", "Content-Type: application/json", "-d", payload],
    capture_output=True, text=True
)
allowance_hex = json.loads(result.stdout).get("result", "0x0")
current_allowance = int(allowance_hex, 16)

balance_data = "0x70a08231" + from_addr[2:].zfill(64)
payload = json.dumps({
    "jsonrpc":"2.0","method":"eth_call",
    "params":[{"to": token_addr, "data": balance_data}, hex(block_num)],"id":1
})
result = subprocess.run(
    ["curl", "-s", "-X", "POST", RPC,
     "-H", "Content-Type: application/json", "-d", payload],
    capture_output=True, text=True
)
balance = int(json.loads(result.stdout).get("result", "0x0"), 16)

print(f"Allowance: {current_allowance}")
print(f"Balance:   {balance}")

# Human readable values (USDT has 6 decimals)
allowance_readable = f"{current_allowance / 10**6:.2f} USDT" if current_allowance < 10**20 else f"UNLIMITED"
balance_readable  = f"{balance / 10**6:.2f} USDT"
amount_readable   = f"{amount / 10**6:.2f} USDT" if amount < 10**20 else "UNLIMITED"

# === STEP 3: Build labeled context ===
print(f"\n{'=' * 60}")
print("STEP 3: Data with source labels")
print("=" * 60)

labeled_context = {
    "[ON-CHAIN FACT] chain_id": 1,
    "[ON-CHAIN FACT] current_block": block_num,
    "[ON-CHAIN FACT] token_contract": token_addr,
    "[KNOWN TOKEN] token_name": "Tether USD (USDT)",
    "[KNOWN TOKEN] token_decimals": 6,
    "[ON-CHAIN FACT] from": from_addr,
    "[ON-CHAIN FACT] spender": spender,
    "[ON-CHAIN FACT] approve_amount_raw": amount,
    "[ON-CHAIN FACT] is_unlimited": amount > 10**30,
    "[ON-CHAIN FACT - real-time] current_allowance": current_allowance,
    "[ON-CHAIN FACT - real-time] balance": balance,
    "[UNTRUSTED - from dApp] dapp_claim": "This dApp says 'Grant approval to trade tokens'",
    "[UNTRUSTED - from user] user_intent": "User says they want to swap tokens"
}

for k, v in labeled_context.items():
    print(f"  {k}: {v}")

# === STEP 4: Build the LLM prompt ===
print(f"\n{'=' * 60}")
print("STEP 4: LLM Prompt (ready to send to AI)")
print("=" * 60)

prompt = f"""You are a wallet security assistant.

## Rules
1. Distinguish on-chain facts from user claims and dApp descriptions
2. If the approve amount is UNLIMITED (>10^30), flag HIGH risk
3. Include uncertainties in your output
4. Recommend human approval for any high-risk action

## Context (with source labels)
Chain ID: 1  [ON-CHAIN FACT]
Block: {block_num}  [ON-CHAIN FACT]
Token: Tether USD (USDT, 6 decimals)  [KNOWN TOKEN]
Contract: {token_addr}  [ON-CHAIN FACT]
From: {from_addr}  [ON-CHAIN FACT]
Spender: {spender}  [ON-CHAIN FACT]
Approve amount: {amount_readable}  [ON-CHAIN FACT]
Current allowance: {allowance_readable}  [ON-CHAIN FACT - real-time]
User's balance: {balance_readable}  [ON-CHAIN FACT - real-time]
dApp claim: "Grant approval to trade tokens"  [UNTRUSTED]
User intent: Swap tokens  [UNTRUSTED]

## Output JSON format
{{
  "summary": "brief analysis",
  "risk_level": "low|medium|high",
  "risk_factors": ["list of risks"],
  "requires_human_approval": true|false,
  "recommendation": "what user should do",
  "uncertainties": ["what we don't know"],
  "user_checks": ["things user should verify"]
}}

Now analyze this approve request:"""

print(prompt)

# === STEP 5: Verification questions ===
print(f"\n{'=' * 60}")
print("STEP 5: Self-check — did the LLM get these right?")
print("=" * 60)

print("""
Questions to verify:
1. Did it flag UNLIMITED approval as HIGH risk?
2. Did it separate on-chain facts from [UNTRUSTED] sources?
3. Did it mention uncertainties?
4. Did it require human approval?
5. Did it give user checks to verify independently?
""")

# Save
output = {
    "context": labeled_context,
    "prompt": prompt,
    "verification_questions": [
        "Flag unlimited as high risk?",
        "Separate on-chain facts from untrusted?",
        "Include uncertainties?",
        "Require human approval?",
        "Give user checks?"
    ]
}

out_path = os.path.join(script_dir, "approve_prompt.json")
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"Saved to: {out_path}")
print("=" * 60)
print("DONE! Context spec + prompt ready for LLM testing.")
