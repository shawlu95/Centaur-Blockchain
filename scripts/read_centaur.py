from scripts.util import Entry, get_account, encode_function_data, get_proxy, wrap_transaction, Transaction, Account
from brownie import Centaur, CentaurV0, CentaurAdmin, config, network, Contract
import os
import pickle


def read_cache(path):
    if os.path.isfile(path):
        return pickle.load(open(path, 'rb'))
    return []


def read_centaur():
    account = get_account()
    centaur = get_proxy(
        version=config["networks"][network.show_active()]["latest"])

    cache_dir = os.path.join('.', 'data', network.show_active())
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    account_cache_path = os.path.join(cache_dir, 'account_cache.obj')
    transaction_cache_path = os.path.join(cache_dir, 'transaction_cache.obj')
    entry_cache_path = os.path.join(cache_dir, 'entry_cache.obj')

    account_cache = read_cache(account_cache_path)
    transaction_cache = read_cache(transaction_cache_path)
    entry_cache = read_cache(entry_cache_path)

    account_cache_ids = set({item.id for item in account_cache})
    transaction_cache_ids = set({item.id for item in transaction_cache})
    entry_cache_ids = set({item.id for item in entry_cache})

    txn_count = centaur.getUserTransactionCount({"from": account})
    txn_ids = centaur.getUserTransactionIds({"from": account})
    txn_ids_from_chain = [
        id for id in transaction_cache_ids if id not in set(txn_ids)]

    print(f"User {account.address} has transaction: {txn_count}")
    print(centaur.getUserTransactionEntries())
    txns, entries = centaur.getUserTransactionEntries()
    print(len(txns), len(entries))

    account_ids = centaur.getUserAccounts({"from": account})
    for account_id in account_ids:
        if account_id in account_cache_ids:
            continue
        account_cache.append(Account(centaur.getAccountById(account_id)))

    print(txn_ids_from_chain)
    print(centaur.getTransactionByIds(txn_ids_from_chain))
    on_chain_txns = list(map(lambda x: Transaction(
        x), centaur.getTransactionByIds(txn_ids_from_chain)))
    print(on_chain_txns)
    transaction_cache += on_chain_txns

    entry_ids_from_chain = []
    for txn in txns:
        entry_ids_from_chain += txn.entries
    on_chain_entries = list(
        map(lambda x: Entry(x), centaur.getEntryByIds(entry_ids_from_chain)))
    print(on_chain_entries)
    entry_cache += on_chain_entries

    pickle.dump(account_cache, open(account_cache_path, 'wb'))
    pickle.dump(transaction_cache, open(transaction_cache_path, 'wb'))
    pickle.dump(entry_cache, open(entry_cache_path, 'wb'))


def check_same():

    remote_cache_dir = os.path.join('.', 'data', network.show_active())
    local_cache_dir = os.path.join('.', 'tests', 'data')

    cache = "account_cache.obj"
    remote_copy = pickle.load(
        open(os.path.join(remote_cache_dir, cache), 'rb'))
    local_copy = pickle.load(open(os.path.join(local_cache_dir, cache), 'rb'))
    for item in remote_copy:
        ref = Account(local_copy[item.id]['account'])
        item.owner = ''
        assert item == ref

    cache = "transaction_cache.obj"
    remote_copy = pickle.load(
        open(os.path.join(remote_cache_dir, cache), 'rb'))
    local_copy = pickle.load(open(os.path.join(local_cache_dir, cache), 'rb'))
    for item in remote_copy:
        ref = Transaction(local_copy[item.id]['ledger_transaction'])
        item.owner = ''
        assert item == ref, f"{item.__dict__} != {ref.__dict__}"

    cache = "entry_cache.obj"
    remote_copy = pickle.load(
        open(os.path.join(remote_cache_dir, cache), 'rb'))
    local_copy = pickle.load(open(os.path.join(local_cache_dir, cache), 'rb'))
    for item in remote_copy:
        ref = Entry(local_copy[item.id]['ledger_entry'])
        item.owner = ''
        assert item == ref, f"{item.__dict__} != {ref.__dict__}"


def main():
    read_centaur()
    check_same()
