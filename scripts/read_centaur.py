from scripts.util import AccountType, Entry, get_account, encode_function_data, get_proxy, wrap_account, wrap_transaction, Transaction, Account
from brownie import Centaur, CentaurV0, CentaurAdmin, config, network, Contract
import os
import pickle


def read_cache(path):
    if os.path.isfile(path):
        return pickle.load(open(path, 'rb'))
    return []


def read_all_txns():
    account = get_account()
    centaur = get_proxy(
        version=config["networks"][network.show_active()]["latest"])

    txn_count = centaur.getUserTransactionCount(account.address)
    txn_ids = centaur.getUserTransactionIds(account.address)

    print(f"User {account.address} has transaction: {txn_count}")

    on_chain_txns = list(map(lambda x: Transaction(
        x), centaur.getTransactionByIds(txn_ids)))
    for txn in on_chain_txns:
        print(txn.__dict__)


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

    txn_count = centaur.getUserTransactionCount(account.address)
    txn_ids = centaur.getUserTransactionIds(account.address)
    txn_ids_from_chain = [
        id for id in transaction_cache_ids if id not in set(txn_ids)]

    print(f"User {account.address} has transaction: {txn_count}")
    txns, entries = centaur.getUserTransactionEntries(account.address)
    print(len(txns), len(entries))

    account_cache = list(map(lambda x: Account(
        x), centaur.getUserAccounts(account.address)))

    print(txn_ids_from_chain)
    on_chain_txns = list(map(lambda x: Transaction(
        x), centaur.getTransactionByIds(txn_ids_from_chain)))
    print(on_chain_txns)
    transaction_cache += on_chain_txns

    entry_ids_from_chain = []
    for txn in txns:
        txn = Transaction(txn)
        entry_ids_from_chain += txn.entry_ids
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
        owner, id, account_type, account_name, _, _, _, _ = local_copy[
            item.id]['account']
        ref = Account(wrap_account(owner=owner, id=id, account_type=AccountType(
            account_type), account_name=account_name, transaction_count=item.transaction_count,
            deleted=item.deleted, debit=item.debit, credit=item.credit))
        item.owner = ''
        assert item == ref, f"{item.__dict__} != {ref.__dict__}"

    cache = "transaction_cache.obj"
    remote_copy = pickle.load(
        open(os.path.join(remote_cache_dir, cache), 'rb'))
    local_copy = pickle.load(open(os.path.join(local_cache_dir, cache), 'rb'))
    for item in remote_copy:
        print(item.__dict__)
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
    read_all_txns()
    read_centaur()
    check_same()
