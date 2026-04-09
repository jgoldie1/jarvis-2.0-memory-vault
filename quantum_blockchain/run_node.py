from __future__ import annotations

from quantum_blockchain.contracts.ternary_contract import Contract
from quantum_blockchain.core.blockchain import Blockchain
from quantum_blockchain.core.crypto_utils import generate_keys, sign_transaction
from quantum_blockchain.core.transaction import Transaction


def main() -> None:
    print("STARTING NODE")

    alice_private, _ = generate_keys()
    bob_private, _ = generate_keys()
    carol_private, _ = generate_keys()

    chain = Blockchain(difficulty=2, reward=50.0)

    print("=== QUANTUM TERNARY BLOCKCHAIN NODE ===")
    print("Chain length:", len(chain.chain))
    print("Chain valid:", chain.is_valid())

    tx1 = Transaction(
        sender="AliceWallet",
        receiver="BobWallet",
        amount=15.0,
        memo="Marketplace Payment",
    )
    sign_transaction(alice_private, tx1)
    chain.add_transaction(tx1)

    tx2 = Transaction(
        sender="BobWallet",
        receiver="CarolWallet",
        amount=4.0,
        memo="Service Fee",
    )
    sign_transaction(bob_private, tx2)
    chain.add_transaction(tx2)

    tx3 = Transaction(
        sender="CarolWallet",
        receiver="LogisticsWallet",
        amount=2.0,
        memo="Delivery Charge",
    )
    sign_transaction(carol_private, tx3)
    chain.add_transaction(tx3)

    print("Pending transactions:", len(chain.pending_transactions))

    block = chain.mine_pending_transactions("MinerWallet")

    print("Mined block index:", block.index)
    print("Mined block hash:", block.calculate_hash())
    print("AliceWallet:", chain.get_balance("AliceWallet"))
    print("BobWallet:", chain.get_balance("BobWallet"))
    print("CarolWallet:", chain.get_balance("CarolWallet"))
    print("LogisticsWallet:", chain.get_balance("LogisticsWallet"))
    print("MinerWallet:", chain.get_balance("MinerWallet"))

    contract = Contract("LogisticsDeliveryContract")
    print("Contract state before:", contract.status())
    contract.approve()
    print("Contract state after:", contract.status())
    print("Saved chain file: data/chain.json")


if __name__ == "__main__":
    main()
