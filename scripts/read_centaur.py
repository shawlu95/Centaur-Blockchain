from scripts.util import AccountType, Action, Entry, get_account, encode_function_data, get_proxy, wrap_account, wrap_transaction, Transaction, Account
from brownie import Centaur, CentaurV0, CentaurAdmin, config, network, Contract
import os
import pickle


def read_cache(path):
    if os.path.isfile(path):
        return pickle.load(open(path, 'rb'))
    return []


def read_balance_sheet():
    account = get_account()
    centaur = get_proxy(
        version=config["networks"][network.show_active()]["latest"])

    asset, liability, equity, temp = centaur.getBalanceSheet(account.address)
    assert asset == liability + equity + temp

    snapshot = centaur.getBalanceSheetSnapshot(account.address, 100, 10, 10)
    print(snapshot)


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

    transaction_cache = read_cache(transaction_cache_path)
    entry_cache = read_cache(entry_cache_path)

    transaction_cache_ids = set({item.id for item in transaction_cache})

    txn_count = centaur.getUserTransactionCount(account.address)
    txn_ids = centaur.getUserTransactionIds(account.address)
    txn_ids_from_chain = [
        id for id in txn_ids if id not in set(transaction_cache_ids)]

    print(f"User {account.address} has transaction: {txn_count}")
    account_cache = list(map(lambda x: Account(
        x), centaur.getUserAccounts(account.address)))
    for account in account_cache:
        print(account.__dict__)
    on_chain_txns, on_chain_entries = centaur.getTransactionByIds(
        txn_ids_from_chain)
    on_chain_txns = list(map(lambda x: Transaction(x), on_chain_txns))
    on_chain_entries = list(map(lambda x: Entry(x), on_chain_entries))

    transaction_cache += on_chain_txns
    entry_cache += on_chain_entries

    pickle.dump(account_cache, open(account_cache_path, 'wb'))
    pickle.dump(transaction_cache, open(transaction_cache_path, 'wb'))
    pickle.dump(entry_cache, open(entry_cache_path, 'wb'))

    print(serialize(account_cache))


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


def serialize():
    def convert(arr): return list(map(lambda x: x.__dict__, arr))

    cache_dir = os.path.join('.', 'data', network.show_active())
    account_cache_path = os.path.join(cache_dir, 'account_cache.obj')
    transaction_cache_path = os.path.join(cache_dir, 'transaction_cache.obj')
    entry_cache_path = os.path.join(cache_dir, 'entry_cache.obj')

    transaction_cache = read_cache(transaction_cache_path)
    entry_cache = read_cache(entry_cache_path)
    account_cache = read_cache(account_cache_path)

    print(convert(transaction_cache)[0])
    print(convert(entry_cache)[0])
    print(convert(account_cache)[0])

    snapshot = {"asset": 0, "liability": 0, "equity": 0}
    for account in account_cache:
        if account.account_type == AccountType.ASSET:
            snapshot['asset'] += (account.debit - account.credit) / 10 ** 9
        elif account.account_type == AccountType.LIABILITY:
            snapshot['liability'] -= (account.debit - account.credit) / 10 ** 9
        elif account.account_type == AccountType.SHAREHOLDER_EQUITY:
            snapshot['equity'] -= (account.debit - account.credit) / 10 ** 9
    print(snapshot)

    history = []
    for txn in transaction_cache[::-1]:
        for ent_id in txn.entry_ids:
            ent = entry_cache[ent_id]
            account = account_cache[ent.ledger_account_id]
            amount = ent.amount / 10 ** 9
            if account.account_type == AccountType.ASSET:
                if ent.action == Action.DEBIT:
                    snapshot['asset'] -= amount
                elif ent.action == Action.CREDIT:
                    snapshot['asset'] += amount
            elif account.account_type == AccountType.LIABILITY:
                if ent.action == Action.DEBIT:
                    snapshot['liability'] += amount
                elif ent.action == Action.CREDIT:
                    snapshot['liability'] -= amount
            elif account.account_type == AccountType.SHAREHOLDER_EQUITY:
                if ent.action == Action.DEBIT:
                    snapshot['equity'] += amount
                elif ent.action == Action.CREDIT:
                    snapshot['equity'] -= amount
        snapshot["date"] = txn.date
        history.append(snapshot.copy())

    pickle.dump(history, open(os.path.join(cache_dir, 'history.obj'), 'wb'))
    with open(os.path.join(cache_dir, 'history.csv'), "w") as f:
        for line in history:
            f.write(
                f"{line['date']},{line['asset']},{line['liability']},{line['equity']}\n")


def main():
    read_balance_sheet()
    # read_all_txns()
    # read_centaur()
    # check_same()
    # serialize()
