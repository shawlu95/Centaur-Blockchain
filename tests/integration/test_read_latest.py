from scripts.util import (
    get_account, get_contract, get_proxy,
    wrap_account, wrap_transaction,
    AccountType,
    Account, Transaction, Entry,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from brownie import network, config
import pytest
import pickle


def test_get_proxy():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_get_proxy")

    centaur = get_proxy(version=config['version']['latest'])
    assert centaur.address == config[network.show_active()]['Centaur']


def test_read_account():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_ingest_account")

    account = get_account()
    centaur = get_proxy(version=config['version']['latest'])

    account_cache = pickle.load(open("tests/data/account_cache.obj", 'rb'))
    for i, (_, val) in enumerate(account_cache.items()):
        _, _, accountType, accountName, _ = val['account']
        actual = Account(centaur.getAccountByIds([i])[0])
        expected = Account(wrap_account(
            owner=account.address, id=i, account_type=AccountType(accountType),
            account_name=accountName, deleted=0
        ))
        assert actual == expected, \
            f"Expected:{str(expected.__dict__)} != Actual:{actual.__dict__}"


def test_read_nonexist_account():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_read_nonexist_account")

    account = get_account()
    centaur = get_proxy(version=config['version']['latest'])

    with pytest.raises(ValueError):
        Account(centaur.getAccountByIds([10**18])[0])


def test_read_transactions():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_injest_transactions")

    limit_txn = 10
    account = get_account()
    centaur = get_proxy(config["version"]["latest"])

    txn_cache = pickle.load(open("tests/data/trans_cache.obj", 'rb'))
    entry_cache = pickle.load(open("tests/data/entry_cache.obj", 'rb'))

    entry_id_offset = 0
    for txn_id, (_, val) in enumerate(txn_cache.items()):
        try:
            actual_txn = Transaction(
                centaur.getTransactionById([txn_id], {"from": account})[0])
        except:
            raise ValueError("Transaction does not exist!")

        _, date, _, entries, _ = val['ledger_transaction']
        expected_txn = Transaction(wrap_transaction(
            owner=account.address, date=date, id=txn_id, deleted=0, entry_ids=entries))
        assert actual_txn == expected_txn, \
            f"Expected:{str(expected_txn.__dict__)} != Actual:{actual_txn.__dict__}"

        for i, entry_id in enumerate(actual_txn.entry_ids):
            actual_entry = Entry(centaur.getEntryById([entry_id])[0])
            expected_entry = Entry(entry_cache[entry_id]['ledger_entry'])
            expected_entry.id = entry_id_offset + i
            assert actual_entry == expected_entry, \
                f"Expected:{str(expected_entry.__dict__)} != Actual:{actual_entry.__dict__}"

        entry_id_offset += len(actual_txn.entry_ids)
        if txn_id >= limit_txn:
            break


def test_read_nonexist_transaction():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_read_nonexist_transaction")

    account = get_account()
    centaur = get_proxy(version=config['version']['latest'])

    with pytest.raises(ValueError):
        Account(centaur.getTransactionByIds([10**18], {"from": account})[0])


def test_get_account_by_id():
    pytest.skip("Skip: test_add_ledger_account")

    account = get_account()
    centaur = get_contract(contract_name="CentaurV0")

    asset_account_name = "cash"
    account_0 = Account(centaur.getAccountByIds([0])[0])
    expected_0 = Account(wrap_account(
        owner=account.address, id=0, account_type=AccountType.ASSET,
        account_name=asset_account_name, deleted=0
    ))
    assert account_0 == expected_0, \
        f"Expected:{str(expected_0.__dict__)} != Actual:{account_0.__dict__}"
