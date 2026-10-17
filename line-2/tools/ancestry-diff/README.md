# Ancestry Diff

Verify **two Ethereum account/storage states and the parent links between their
headers using one caller-supplied tip hash**. The older header is authenticated
backward through the chain; both endpoint witnesses are checked against their
respective state roots before any difference is reported. This combines the
unchanged sibling Header Chain and State Diff tools.

Run the offline real ZTO/IMD pool trial from the repository root with Python
3.9+ and only the standard library:

```sh
python3 -B line-2/tools/ancestry-diff/ancestry_diff.py demo
```

No installation or network is needed to run the demo. Keep sibling
`header-chain/`, `state-diff/`, `header-anchor/` and `state-witness/` folders
beside this tool. It reads bounded files within the working directory and
prints JSON. It does not read environment variables, keys or wallets; write
files; sign; send transactions; pay; post; or deploy.

## What happened when tried

On 2026-10-17, the demo verified the real ZTO/IMD Uniswap v4 PoolManager
account and its requested pool slot at mainnet blocks **26,212,390** and
**26,212,393**. The three consecutive parent links span **36 seconds**. Both
account and storage proofs verified against the roots in the linked headers.
The requested raw pool slot stayed at
`0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41`, while the
PoolManager account's overall storage root changed. Its native ETH balance
increased by `537420754348019737` wei. That is the PoolManager's whole-account
ETH balance change, not a ZTO transfer or this pool's balance. A changed
storage root with an equal sampled slot means some *other* storage may have
changed; it does not identify which slot.

The oldest real witness and the four real headers were inherited unchanged.
The new `examples/pool-tip.json` is an ordinary offline fixture captured with
read-only `eth_chainId`, `eth_getBlockByNumber` and `eth_getProof` from
<https://eth.drpc.org>, using the inherited custom
`Pepeolithic-StateWitness/1.0` User-Agent. The publicnode endpoint did not
return a usable response during this round. Capture verified the tip proof
against the RPC header's root before it was saved; this checks consistency,
**not** that the RPC header is a trusted checkpoint. The fixed demo tip hash is
an RPC observation, not independently authenticated consensus data.

All **10 new integration tests passed**, including real data, a one-header
identity comparison, altered parent links, corrupted proofs at either endpoint,
wrong caller address/slot, wrong tip hash and clean CLI rejections without
partial success output:

```sh
python3 -B -m unittest discover -s line-2/tools/ancestry-diff -p 'test_*.py' -v
```

## Your own comparison

The chain file uses `header-chain/1`: complete execution headers in oldest-first
order. The two witness files use `state-witness/1`, one for the oldest header and
one for the tip. Supply **one independently authenticated tip block hash**, the
actual account address and the exact set of requested storage slots. Repeat
`--slot` for more slots, or omit it for an account-only comparison. For example:

```sh
python3 -B line-2/tools/ancestry-diff/ancestry_diff.py compare \
  line-2/tools/header-chain/examples/zto-header-chain.json \
  line-2/tools/state-witness/examples/zto-pool-mainnet.json \
  line-2/tools/ancestry-diff/examples/pool-tip.json \
  --tip-hash 0xead51f4e385140de3b2010a5b4c96106e8bf27fdb836246e57e18ad5df545a33 \
  --address 0x000000000004444c5dc75cB358380D2e3dE08A90 \
  --slot 0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b
```

Successful output is `ancestry-diff/1` JSON with the verified chain and the
State Diff endpoint report. Exit 1 prints error JSON on stderr and no partial
success output; argument errors exit 2. Header Chain bounds the input to 1–64
headers and 256 KiB; State Witness bounds each proof file to 1 MB and the
requested set to 64 slots. Strict JSON, supported header schemas, RLP/MPT
proof checks, workspace path boundaries and slot matching come from the
sibling tools. File labels and embedded block hashes are never trust anchors.

## Trust and limits

You must authenticate the tip hash, chain, canonicality, execution validity
and finality independently. This tool checks linked header hashes, consecutive
numbers and increasing timestamps, not Ethereum consensus. A one-header chain
is supported for an identity comparison. It cannot authenticate a later block
from an older hash. The result concerns only two endpoints: equal values can
hide intermediate changes, and a changed storage root does not enumerate
changed slots. Raw slot values have no inferred ABI, ERC-20 meaning, token
decimals, price, swap quote or transfer history. No new coin is needed.
