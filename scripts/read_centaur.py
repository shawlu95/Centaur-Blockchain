from scripts.util import Entry, get_account, encode_function_data, get_proxy, wrap_transaction, Transaction
from brownie import Centaur, CentaurV0, CentaurAdmin, config, network, Contract


def read_centaur():
    account = get_account()
    centaur = get_proxy(version=config['version']['latest'])

    txn_count = centaur.getUserTransactionCount({"from": account})
    txn_ids = centaur.getUserTransaction({"from": account})

    print(f"User {account.address} has transaction: {txn_count}")
    print("Transaction ID:", txn_ids)

    for id in txn_ids:
        txn = Transaction(centaur.getTransactionById(id, {"from": account}))
        print(txn.__dict__)

        entry_ids = txn.entry_ids
        for enttry_id in entry_ids:
            entry = Entry(centaur.getEntryById(enttry_id, {"from": account}))
            print(entry.__dict__)


def main():
    read_centaur()
