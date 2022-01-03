from scripts.util import AccountType, Action, Entry, get_account, encode_function_data, get_proxy, wrap_account, wrap_transaction, Transaction, Account
from brownie import Centaur, CentaurV0, CentaurAdmin, config, network, Contract
import os
import pickle
import math


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

    acc_count = centaur.getAccountCount()
    txn_count = centaur.getTransactionCount()

    txn_ids_from_chain = list(range(txn_count))

    print(f"User {account.address} has transaction: {txn_count}")
    acc_ids = list(range(acc_count))
    all_accounts = centaur.getAccountByIds(acc_ids)
    account_cache = list(map(lambda x: Account(x), all_accounts))
    for account in account_cache:
        print(account.__dict__)

    on_chain_txns = []
    on_chain_entries = []

    page_size = 1000
    for page in range(math.ceil(txn_count / page_size)):
        print("Page:", page * page_size, min(txn_count, (page + 1) * page_size))
        on_chain_txns_page, on_chain_entries_page = centaur.getTransactionByIds(
            txn_ids_from_chain[page * page_size:min(txn_count, (page + 1) * page_size)])
        on_chain_txns += on_chain_txns_page
        on_chain_entries += on_chain_entries_page
    for txn in on_chain_txns[-100:]:
        print(txn)
    on_chain_txns = list(map(lambda x: Transaction(x), on_chain_txns))
    on_chain_entries = list(map(lambda x: Entry(x), on_chain_entries))

    pickle.dump(account_cache, open(account_cache_path, 'wb'))
    pickle.dump(on_chain_txns, open(transaction_cache_path, 'wb'))
    pickle.dump(on_chain_entries, open(entry_cache_path, 'wb'))


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


def dump_sql():
    """
    Process on-chain tranasction into a single SQL table (for analytics purpose)
    | entry_id | transaction id | ledger account id (index) | action | amount | date | deleted |
    """

    cache_dir = os.path.join('.', 'data', network.show_active())
    on_chain_txn = pickle.load(
        open(os.path.join(cache_dir, 'transaction_cache.obj'), "rb"))
    on_chain_entry = pickle.load(
        open(os.path.join(cache_dir, 'entry_cache.obj'), "rb"))
    on_chain_account = pickle.load(
        open(os.path.join(cache_dir, 'account_cache.obj'), "rb"))
    for acc in on_chain_account:
        print(acc.__dict__)
    on_chain_entry_map = {entry.id: entry for entry in on_chain_entry}
    on_chain_account_map = {acc.id: acc for acc in on_chain_account}

    rows = []
    for txn in on_chain_txn:
        for ent_id in txn.entry_ids:
            entry = on_chain_entry_map[ent_id]
            account = on_chain_account_map[entry.ledger_account_id]
            rows.append([entry.id, txn.id, entry.ledger_account_id, account.account_type.value,
                         entry.action.value, entry.amount, txn.date, txn.owner, txn.deleted])
    with open(os.path.join(cache_dir, "entry_sql.csv"), "w") as o:
        for row in rows:
            o.write(",".join(list(map(str, row))) + "\n")

    cache = []
    for acc in on_chain_account:
        fields = [acc.owner, acc.id, acc.account_type.value, acc.account_name,
                  acc.debit, acc.credit, acc.transaction_count, acc.deleted]
        cache.append(list(map(str, fields)))
    with open(os.path.join(cache_dir, "LedgerAccount.csv"), "w") as o:
        cache = list(map(lambda x: ",".join(x), cache))
        o.write("\n".join(cache))

    txn_cache = []
    ent_cache = []
    link_cache = []
    for txn in on_chain_txn:
        txn_cache.append(
            list(map(str, [txn.owner, txn.date, txn.id, f'"{txn.memo}"', txn.deleted])))
        for ent_id in txn.entry_ids:
            link_cache.append(list(map(str, [txn.id, ent_id])))
            entry = on_chain_entry_map[ent_id]
            ent_cache.append(list(
                map(str, [ent_id, entry.ledger_account_id, entry.action.value, entry.amount])))
    with open(os.path.join(cache_dir, "TransactionEntryLink.csv"), "w") as o:
        o.write("\n".join(list(map(lambda x: ",".join(x), link_cache))))
    with open(os.path.join(cache_dir, "LedgerTransaction.csv"), "w") as o:
        o.write("\n".join(list(map(lambda x: ",".join(x), txn_cache))))
    with open(os.path.join(cache_dir, "LedgerEntry.csv"), "w") as o:
        o.write("\n".join(list(map(lambda x: ",".join(x), ent_cache))))


def main():
    # read_balance_sheet()
    read_centaur()
    # serialize()
    dump_sql()
