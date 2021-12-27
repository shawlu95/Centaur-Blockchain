from scripts.util import (
    get_account, get_contract, get_proxy,
    wrap_entry, wrap_account, wrap_transaction,
    Action, AccountType,
    Account, Entry, Transaction,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from brownie import network, exceptions, config
import pytest
import pickle


def test_ingest_account():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_ingest_account")

    account = get_account()
    centaur = get_proxy(
        version=config["networks"][network.show_active()]["latest"])

    account_cache = pickle.load(open("tests/data/account_cache.obj", 'rb'))
    for i, (_, val) in enumerate(account_cache.items()):
        try:
            centaur.getAccountByIds([i])
            continue
        except:
            _, _, accountType, accountName, _, _, _, _ = val['account']
            centaur.addLedgerAccount(
                accountName, accountType, {"from": account})

            actual = Account(centaur.getAccountByIds([i])[0])
            expected = Account(wrap_account(
                owner=account.address, id=i, account_type=AccountType(
                    accountType),
                account_name=accountName, transaction_count=0, debit=0, credit=0, deleted=0
            ))
            assert actual == expected, \
                f"Expected:{str(expected.__dict__)} != Actual:{actual.__dict__}"


def test_injest_transactions_batch():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_transactions")

    limit_txn = 50
    account = get_account()
    centaur = get_proxy(config["networks"][network.show_active()]["latest"])

    txn_cache = pickle.load(open("tests/data/transaction_cache.obj", 'rb'))
    entry_cache = pickle.load(open("tests/data/entry_cache.obj", 'rb'))

    exist_txn = centaur.getUserTransactionIds(account.address)

    txn_id_offset = len(exist_txn)
    entry_id_offset = centaur.getEntriesCount()

    txn_sizes = []
    dates = []
    ledger_entries = []
    memos = []

    for txn_id, val in txn_cache.items():
        if len(txn_sizes) >= limit_txn:
            break
        if txn_id not in exist_txn:
            _, date, _, memo, entries, _ = val['ledger_transaction']

            txn_sizes.append(len(entries))
            dates.append(date)
            memos.append(memo)
            ledger_entries += [entry_cache[entry_id]['ledger_entry']
                               for entry_id in entries]
    centaur.addLedgerTransactions(
        txn_sizes, dates, memos, ledger_entries, {"from": account})

    assert centaur.getUserTransactionCount(
        account.address) == txn_id_offset + limit_txn
    assert centaur.getEntriesCount() == entry_id_offset + len(ledger_entries)


def test_injest_transactions_loop_batch():
    for i in range(16):
        test_injest_transactions_batch()


def test_update_ledger_account():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_transactions")

    account = get_account()
    centaur = get_proxy(config["networks"][network.show_active()]["latest"])

    new_name = "Checking"
    centaur.updateLedgerAccount(0, new_name, {"from": account})
    actual = Account(centaur.getAccountByIds([0])[0])
    expected = Account(wrap_account(
        owner=account.address, id=0, account_type=AccountType(
            0),
        account_name=new_name, transaction_count=0, debit=0, credit=0, deleted=0
    ))
    assert actual.account_name == expected.account_name
