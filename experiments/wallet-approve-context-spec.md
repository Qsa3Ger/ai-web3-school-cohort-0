# Context Spec: 钱包授权检查 Agent

## 场景

用户问：**"这个 dApp 要我 approve，可以签吗？"**

Agent 需要帮用户判断这笔 approve 是否安全。

---

## 1. 必须实时查询的字段 🔴

| 字段 | 说明 | 查询方式 |
|------|------|----------|
| `chain_id` | 当前链 ID | RPC：`eth_chainId` |
| `current_block` | 当前区块号 | RPC：`eth_blockNumber` |
| `token_contract` | 要 approve 的代币合约地址 | 用户请求中提取 |
| `spender` | 被授权方地址 | 用户请求中提取 |
| `approve_amount` | 授权数量 | 解析 calldata |
| `user_allowance` | 用户当前已授权额度 | RPC：调用 `allowance(owner, spender)` |
| `user_balance` | 用户当前代币余额 | RPC：调用 `balanceOf(owner)` |
| `spender_code` | spender 是否有合约代码 | RPC：`eth_getCode` |
| `simulation` | 模拟执行结果 | 本地 simulation 或 Tenderly API |

> **原因**：这些字段每一秒都可能变化，必须实时从链上获取。
> 用户当前的 allowance 可能已经很高了，不能拿昨天的数据判断。

---

## 2. 可以缓存但需要定期刷新的字段 🟡

| 字段 | 说明 | 刷新策略 |
|------|------|----------|
| `spender_reputation` | spender 是否在可信列表 | 每天同步一次社区维护的列表 |
| `token_info` | 代币名称、符号、小数位数 | 缓存 24 小时 |
| `known_scams` | 已知欺骗合约黑名单 | 每小时更新一次 |
| `user_frequent_addresses` | 用户常用地址列表 | 每会话开始刷新 |

> **原因**：这些信息不会每秒变化，但不能太久不更新。
> 比如一个合约昨天还是安全的，今天可能被标记为恶意。

---

## 3. 不能被模型当成事实的字段 ⚠️

| 字段 | 说明 | 处理方式 |
|------|------|----------|
| `dapp_website_description` | dApp 自己的说明文字 | 标注为 **"不可信外部内容"** |
| `user_stated_intent` | 用户说的"我就想买这个 NFT" | 标注为 **"用户意图参考，需验证"** |
| `community_rumors` | 社区里的讨论/传言 | 标注为 **"未经证实的信息"** |
| `model_inferred_purpose` | 模型推断的授权目的 | 标注为 **"AI 推测，请用户自行确认"** |

> **原因**：
> - dApp 的说明可能是假的（钓鱼网站）
> - 用户说想买 NFT，但 approve 的是无限额度
> - 社区传言不可靠
> - 模型推断不能替代链上事实

---

## 4. Agent 回答前必须获取的完整上下文

```
┌─────────────────────────────────────────────┐
│               上下文输入                        │
├─────────────────────────────────────────────┤
│ chain_id: 1                                  │
│ current_block: 21048293                      │
│ token_contract: 0xA0b86991...                │  ← USDC
│ spender: 0x68b34658...                       │
│ approve_amount: 1157920892373161954235709...  │  ← ∞ (无限授权!)
│ user_allowance: 0                            │  ← 目前还没授权过
│ user_balance: 5000000000                     │  ← 5000 USDC
│ spender_has_code: true                       │  ← 有合约
│ spender_risk: HIGH                           │  ← 不在可信列表
│ simulation: OK (但授权额度为无限)               │
│ dapp_statement [UNTRUSTED]: "授权以购买 NFT"    │
│ user_intent: "想买一个 NFT"                     │
└─────────────────────────────────────────────┘
```

## 5. Agent 输出格式 (JSON)

```json
{
  "summary": "该 dApp 要求无限授权 USDC",
  "risk_level": "high",
  "risk_factors": [
    "授权额度为无限 (type(uint256).max)",
    "spender 不在已知可信列表"
  ],
  "requires_human_approval": true,
  "recommendation": "不建议签署。建议使用有限授权或取消授权后离开",
  "uncertainties": [
    "spender 的实际用途无法从链上确认",
    "dApp 自称用于购买 NFT，但该声明不可验证"
  ],
  "user_checks": [
    "在 Etherscan 确认 spender 地址是否匹配 dApp 官网",
    "如需授权，使用有限额度代替无限授权",
    "完成后及时 revoke 授权"
  ]
}
```

---

## 6. 层级分类

| 层级 | 内容 |
|------|------|
| 🏛️ **指令层** | 规则：必须区分可信/不可信数据、无限授权标记为高风险 |
| 🎯 **任务层** | 用户意图："这个 approve 安全吗？" |
| 🔗 **事实层** | chain_id、合约地址、allowance、余额、simulation |
| 📚 **知识层** | 可信列表、代币信息、黑名单 |
| 💭 **记忆层** | 用户常用地址、之前 revoke 过哪些合约 |
