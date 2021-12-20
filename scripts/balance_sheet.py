import pickle
import os
from brownie import config, network
from collections import defaultdict
from scripts.util import Account, Transaction, Entry, AccountType
# import pandas as pd

ACCOUNT_NAME_LENGTH = 35
DIVIDER = "_" * 50


def main():
    cache_dir = os.path.join('.', 'data', network.show_active())

    account_cache = pickle.load(
        open(os.path.join(cache_dir, "account_cache.obj"), 'rb'))
    transaction_cache = pickle.load(
        open(os.path.join(cache_dir, "transaction_cache.obj"), 'rb'))
    entry_cache = pickle.load(
        open(os.path.join(cache_dir, "entry_cache.obj"), 'rb'))

    account_map = {account.id: account for account in account_cache}
    transaction_map = {txn.id: txn for txn in transaction_cache}
    entry_map = {entry.id: entry for entry in entry_cache}

    for _, txn in transaction_map.items():
        if txn.deleted == 1:
            continue
        entry_ids = txn.entry_ids
        for entry_id in entry_ids:
            entry = entry_map[entry_id]
            account_map[entry.ledger_account_id].process_entry(entry)

    account_group = defaultdict(list)
    owner = None
    for account in account_cache:
        print(account.__dict__)

        if not owner:
            owner = account.owner
        else:
            assert owner == account.owner

        account_group[account.account_type].append(account)

    print(DIVIDER)
    print("\n" * 3)
    print("BALANCE SHEET")
    print(f"address: {owner}")
    print("\n")

    for account_type, accounts in account_group.items():
        print(account_type)

        cache = []
        for account in accounts:
            padding = " " * (ACCOUNT_NAME_LENGTH - len(account.account_name))
            print(account.account_name, padding, account.formatted_str())
            cache.append({
                "Acount": account.account_name,
                "Balance": account.formatted_str()
            })
        # print(pd.DataFrame(cache))

        print(DIVIDER)
