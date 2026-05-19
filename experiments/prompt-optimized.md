# Prompt 练习成果

## 用户原始版本

> 自称是 OpenSea 的网站让我 approve USDT，无限额度。合约地址是 0x8a5e2cFf... 我余额有 5000 USDT。请你帮我完成以下内容：
> 1. 区分哪些是链上事实，哪些是不可信内容
> 2. 判断风险等级
> 3. 输出给用户的建议

## 优化版本

> 我是用户。一个自称 OpenSea 的网站让我 approve USDT，无限额度。
> 合约地址是 `0x8a5e2cFf1B2f9c1b3d5e7f9a0b2c4d6e8f0a1b3c`。
>
> ＝＝请执行以下操作＝＝
>
> **Step 1：链上验证**
> - 去 Etherscan 查询这个合约地址：是否已验证？代码是否公开？交易量和持有者？创建时间？
> - 去 OpenSea 官网确认官方合约地址
> - 对比两份地址是否一致
>
> **Step 2：风险分析**
> - 基于查询结果判断安全性
> - 无限额度意味着什么？spender 是谁？
>
> **Step 3：输出 JSON**
> - `risk_level`
> - `on_chain_facts`
> - `untrusted_claims`
> - `recommendation`
> - `user_checks`
> - `etherscan_link`
>
> 请先查再分析，不要凭空猜测。
