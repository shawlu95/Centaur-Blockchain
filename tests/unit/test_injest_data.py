from scripts.util import (
    get_account, get_contract, get_proxy, upgrade,
    wrap_account, wrap_transaction,
    AccountType,
    Account, Entry, Transaction,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from scripts.deploy_centaur import deploy_centaur
from scripts.upgrade_centaur import upgrade_centaur
from brownie import network, config
import pickle
import pytest


def test_injest_accounts():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_accounts")

    account = get_account(index=0)
    deploy_centaur()
    centaur = upgrade_centaur()

    account_cache = pickle.load(open("tests/data/account_cache.obj", 'rb'))
    for i, (_, val) in enumerate(account_cache.items()):
        _, _, accountType, accountName, _ = val['account']
        centaur.addLedgerAccount(accountName, accountType, {"from": account})
        assert centaur.getUserAccountCount({"from": account}) == (i + 1)

        actual = Account(centaur.getAccountById(i, {"from": account}))
        expected = Account(wrap_account(
            owner=account.address, id=i, account_type=AccountType(accountType),
            account_name=accountName, deleted=0
        ))
        assert actual == expected, \
            f"Expected:{str(expected.__dict__)} != Actual:{actual.__dict__}"


def test_injest_transactions():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_transactions")

    limit_txn = 100
    test_injest_accounts()
    account = get_account(index=0)
    centaur = get_proxy(config["version"]["latest"])

    txn_cache = pickle.load(open("tests/data/trans_cache.obj", 'rb'))
    entry_cache = pickle.load(open("tests/data/entry_cache.obj", 'rb'))

    entry_id_offset = 0
    for txn_id, (_, val) in enumerate(txn_cache.items()):
        _, date, _, entries, _ = val['ledger_transaction']
        ledger_entries = [entry_cache[entry_id]['ledger_entry']
                          for entry_id in entries]
        centaur.addLedgerTransaction(date, ledger_entries, {"from": account})

        actual_txn = Transaction(
            centaur.getTransactionById(txn_id, {"from": account}))
        expected_txn = Transaction(wrap_transaction(
            owner=account.address, date=date, id=txn_id, deleted=0, entry_ids=entries))
        assert actual_txn == expected_txn, \
            f"Expected:{str(expected_txn.__dict__)} != Actual:{actual_txn.__dict__}"

        for i, entry_id in enumerate(actual_txn.entry_ids):
            actual_entry = Entry(centaur.getEntryById(
                entry_id, {"from": account}))
            expected_entry = Entry(entry_cache[entry_id]['ledger_entry'])
            expected_entry.id = entry_id_offset + i
            assert actual_entry == expected_entry, \
                f"Expected:{str(expected_entry.__dict__)} != Actual:{actual_entry.__dict__}"
        entry_id_offset += len(actual_txn.entry_ids)

        if txn_id >= limit_txn:
            break
