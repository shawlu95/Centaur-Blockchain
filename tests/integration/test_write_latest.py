from scripts.util import (
    get_account, get_contract,
    wrap_entry, wrap_account, wrap_transaction,
    Action, AccountType,
    Account, Entry, Transaction,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from scripts.deploy_centaur import deploy
from brownie import network, exceptions
import pytest


def test_add_ledger_account_bsc():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_ledger_account")

    account = get_account()
    centaur = get_contract(contract_name="Centaur")

    asset_account_name = "cash"
    centaur.addLedgerAccount(
        asset_account_name, AccountType.ASSET.value, {"from": account})
    assert centaur.getUserAccountCount({"from": account}) == 1

    account_0 = Account(centaur.getAccountById(0, {"from": account}))
    expected_0 = Account(wrap_account(
        owner=account.address, id=0, account_type=AccountType.ASSET,
        account_name=asset_account_name, deleted=0
    ))
    assert account_0 == expected_0, \
        f"Expected:{str(expected_0.__dict__)} != Actual:{account_0.__dict__}"

    liability_account_name = "debt"
    centaur.addLedgerAccount(
        liability_account_name, AccountType.LIABILITY.value, {"from": account})
    assert centaur.getUserAccountCount({"from": account}) == 2

    account_1 = Account(centaur.getAccountById(1, {"from": account}))
    expected_1 = Account(wrap_account(
        owner=account.address, id=1, account_type=AccountType.LIABILITY,
        account_name=liability_account_name, deleted=0
    ))
    assert account_1 == expected_1, \
        f"Expected:{str(expected_1.__dict__)} != Actual:{account_1.__dict__}"

    assert centaur.getUserAccounts({"from": account}) == (0, 1)


def test_add_duplicate_ledger_account():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_duplicate_ledger_account")

    account = get_account(index=0)
    centaur = get_contract(contract_name="Centaur")

    liability_account_name = "debt"
    with pytest.raises(exceptions.VirtualMachineError):
        # try adding duplicate account
        centaur.addLedgerAccount(
            liability_account_name, AccountType.LIABILITY.value, {"from": account})


def test_add_transaction():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_transaction")

    account = get_account()
    centaur = get_contract("Centaur")

    centaur.addLedgerTransaction(365, [
        wrap_entry(id=0, ledger_account_id=0,
                   action=Action.DEBIT, amount=50),
        wrap_entry(id=1, ledger_account_id=1,
                   action=Action.CREDIT, amount=50),
    ], {"from": account})
    assert centaur.getUserTransaction({"from": account}) == (0, )
    assert centaur.getUserTransactionCount({"from": account}) == 1

    txn = Transaction(centaur.getTransactionById(0, {"from": account}))
    expected_txn = Transaction(wrap_transaction(
        owner=account.address, date=365, id=0, deleted=0, entry_ids=(0, 1)))
    assert txn == expected_txn, \
        f"Expected:{str(expected_txn.__dict__)} != Actual:{txn.__dict__}"

    entry_0 = Entry(centaur.getEntryById(0, {"from": account}))
    expected_entry_0 = Entry(wrap_entry(
        id=0, ledger_account_id=0, action=Action.DEBIT, amount=50
    ))
    assert entry_0 == expected_entry_0, \
        f"Expected:{str(expected_entry_0.__dict__)} != Actual:{entry_0.__dict__}"

    entry_1 = Entry(centaur.getEntryById(1, {"from": account}))
    expected_entry_1 = Entry(wrap_entry(
        id=1, ledger_account_id=1, action=Action.CREDIT, amount=50
    ))
    assert entry_1 == expected_entry_1, \
        f"Expected:{str(expected_entry_1.__dict__)} != Actual:{entry_1.__dict__}"


def test_delete_transaction_not_owner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_delete_transaction_not_owner")

    bad_account = get_account(id='Candy')
    centaur = get_contract("Centaur")

    try:
        centaur.deleteTransactionById(0, {"from": bad_account})
    except ValueError:
        pass
