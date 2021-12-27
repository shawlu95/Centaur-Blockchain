from scripts.util import (
    get_account, get_contract, get_proxy, upgrade,
    wrap_account, wrap_transaction,
    AccountType,
    Account, Entry, Transaction,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from scripts.deploy_centaur import deploy_centaur, deploy_proxy_and_admin
from scripts.upgrade_centaur import upgrade_centaur
from brownie import network, config
import pickle
import pytest


def test_injest_accounts():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_accounts")

    account = get_account(index=0)
    deploy_centaur()
    deploy_proxy_and_admin()
    centaur = upgrade_centaur()

    account_cache = pickle.load(open("tests/data/account_cache.obj", 'rb'))
    for i, (_, val) in enumerate(account_cache.items()):
        _, _, accountType, accountName, _, _, _, _ = val['account']
        centaur.addLedgerAccount(accountName, accountType, {"from": account})
        assert centaur.getUserAccountCount(account.address) == (i + 1)

        actual = Account(centaur.getAccountByIds([i])[0])
        expected = Account(wrap_account(
            owner=account.address, id=i, account_type=AccountType(accountType),
            account_name=accountName, transaction_count=0, debit=0, credit=0, deleted=0
        ))
        assert actual == expected, \
            f"Expected:{str(expected.__dict__)} != Actual:{actual.__dict__}"


def test_injest_transactions():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_transactions")

    limit_txn = 100
    test_injest_accounts()
    account = get_account(index=0)
    centaur = get_proxy(config["networks"][network.show_active()]["latest"])

    txn_cache = pickle.load(open("tests/data/transaction_cache.obj", 'rb'))
    entry_cache = pickle.load(open("tests/data/entry_cache.obj", 'rb'))

    entry_id_offset = 0
    for txn_id, (_, val) in enumerate(txn_cache.items()):
        _, date, _, memo, entries, _ = val['ledger_transaction']
        ledger_entries = [entry_cache[entry_id]['ledger_entry']
                          for entry_id in entries]
        centaur.addLedgerTransaction(
            date, memo, ledger_entries, {"from": account})

        actual_txn = Transaction(
            centaur.getTransactionByIds([txn_id])[0][0])
        expected_txn = Transaction(wrap_transaction(
            owner=account.address, date=date, id=txn_id, memo=memo, deleted=0, entry_ids=entries))
        assert actual_txn == expected_txn, \
            f"Expected:{str(expected_txn.__dict__)} != Actual:{actual_txn.__dict__}"

        for i, entry_id in enumerate(actual_txn.entry_ids):
            actual_entry = Entry(centaur.getEntryByIds([entry_id])[0])
            expected_entry = Entry(entry_cache[entry_id]['ledger_entry'])
            expected_entry.id = entry_id_offset + i
            assert actual_entry == expected_entry, \
                f"Expected:{str(expected_entry.__dict__)} != Actual:{actual_entry.__dict__}"
        entry_id_offset += len(actual_txn.entry_ids)

        if txn_id >= limit_txn:
            break


def test_get_recent_transactions():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_transactions")

    test_injest_transactions()

    account = get_account(index=0)
    centaur = get_proxy(
        version=config["networks"][network.show_active()]["latest"])

    txns, ents = centaur.getRecentTransaction(account.address, 10)
    print(txns)
    print(ents)
    assert len(txns) == 10
