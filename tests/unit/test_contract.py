from scripts.util import (
    get_account, get_proxy,
    wrap_entry, wrap_account, wrap_transaction,
    Action, AccountType,
    Account, Entry, Transaction,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from scripts.deploy_centaur import deploy_centaur
from scripts.upgrade_centaur import upgrade_centaur
from brownie import network, exceptions, config
import pytest


def test_add_ledger_account():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_ledger_account")

    account = get_account(index=0)
    deploy_centaur()
    centaur = upgrade_centaur()

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
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_duplicate_ledger_account")

    test_add_ledger_account()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    liability_account_name = "debt"
    with pytest.raises(exceptions.VirtualMachineError):
        # try adding duplicate account
        centaur.addLedgerAccount(
            liability_account_name, AccountType.LIABILITY.value, {"from": account})


def test_add_transaction():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_transaction")

    test_add_ledger_account()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

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


def test_add_multi_entry_transaction():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_multi_entry_transaction")

    test_add_ledger_account()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    centaur.addLedgerTransaction(0, [
        wrap_entry(id=0, ledger_account_id=0,
                   action=Action.DEBIT, amount=50),
        wrap_entry(id=1, ledger_account_id=1,
                   action=Action.CREDIT, amount=25),
        wrap_entry(id=2, ledger_account_id=1,
                   action=Action.CREDIT, amount=25),
    ], {"from": account})
    assert centaur.getUserTransaction({"from": account}) == (0, )
    assert centaur.getUserTransactionCount({"from": account}) == 1
    txn = Transaction(centaur.getTransactionById(0, {"from": account}))
    expected_txn = Transaction(wrap_transaction(
        owner=account.address, date=0, id=0, deleted=0, entry_ids=(0, 1, 2)))
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
        id=1, ledger_account_id=1, action=Action.CREDIT, amount=25
    ))
    assert entry_1 == expected_entry_1, \
        f"Expected:{str(expected_entry_1.__dict__)} != Actual:{entry_1.__dict__}"

    entry_2 = Entry(centaur.getEntryById(2, {"from": account}))
    expected_entry_2 = Entry(wrap_entry(
        id=2, ledger_account_id=1, action=Action.CREDIT, amount=25
    ))
    assert entry_2 == expected_entry_2, \
        f"Expected:{str(expected_entry_2.__dict__)} != Actual:{entry_2.__dict__}"


def test_add_transaction_unbalanced():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_transaction_unbalanced")

    test_add_ledger_account()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    with pytest.raises(exceptions.VirtualMachineError):
        centaur.addLedgerTransaction(365, [
            wrap_entry(id=0, ledger_account_id=0,
                       action=Action.DEBIT, amount=50),
            wrap_entry(id=1, ledger_account_id=1,
                       action=Action.CREDIT, amount=10),
        ], {"from": account})


def test_delete_ledger_account():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_delete_ledger_account")

    test_add_ledger_account()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    assert centaur.getAccountReferenceCount(0, {"from": account}) == 0

    centaur.deleteAccountById(0, {"from": account})
    account_0 = Account(centaur.getAccountById(0, {"from": account}))
    expected_account_0 = Account(wrap_account(
        owner=account.address, id=0, account_type=AccountType.ASSET,
        account_name="cash", deleted=1))
    assert account_0 == expected_account_0, \
        f"Expected:{str(expected_account_0.__dict__)} != Actual:{account_0.__dict__}"


def test_delete_ledger_account_with_reference():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_delete_ledger_account_with_reference")

    test_add_transaction()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    with pytest.raises(exceptions.VirtualMachineError):
        assert centaur.getAccountReferenceCount(0, {"from": account}) == 1
        centaur.deleteAccountById(0, {"from": account})


def test_delete_transaction_not_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_delete_transaction_not_owner")

    test_add_transaction()
    centaur = get_proxy(config["version"]["latest"])
    bad_account = get_account(index=1)

    with pytest.raises(exceptions.VirtualMachineError):
        centaur.deleteTransactionById(0, {"from": bad_account})


def test_delete_transaction_and_account():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_delete_transaction_and_account")

    test_add_multi_entry_transaction()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    assert centaur.getAccountReferenceCount(0, {"from": account}) == 1
    assert centaur.getAccountReferenceCount(1, {"from": account}) == 2
    centaur.deleteTransactionById(0, {"from": account})

    assert centaur.getAccountReferenceCount(0, {"from": account}) == 0
    assert centaur.getAccountReferenceCount(1, {"from": account}) == 0
    txn = Transaction(centaur.getTransactionById(0, {"from": account}))
    expected_txn = Transaction(wrap_transaction(
        owner=account.address, date=0, id=0, deleted=1, entry_ids=(0, 1, 2)))
    assert txn == expected_txn, \
        f"Expected:{expected_txn.__dict__} != Actual:{str(txn.__dict__)}"

    centaur.deleteAccountById(0, {"from": account})
    account_0 = Account(centaur.getAccountById(0, {"from": account}))
    expected_account_0 = Account(wrap_account(
        owner=account.address, id=0, account_type=AccountType.ASSET,
        account_name="cash", deleted=1))
    assert account_0 == expected_account_0, \
        f"Expected:{str(expected_account_0.__dict__)} != Actual:{account_0.__dict__}"

    centaur.deleteAccountById(1, {"from": account})
    account_1 = Account(centaur.getAccountById(1, {"from": account}))
    expected_account_1 = Account(wrap_account(
        owner=account.address, id=1, account_type=AccountType.LIABILITY,
        account_name="debt", deleted=1))
    assert account_1 == expected_account_1, \
        f"Expected:{str(expected_account_1.__dict__)} != Actual:{account_1.__dict__}"

    # deleted stuff should not be removed
    assert centaur.getUserAccountCount({"from": account}) == 2
    assert centaur.getUserTransactionCount({"from": account}) == 1


def test_add_transaction_unknown_ledger_account():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_transaction_unknown_ledger_account")

    test_add_ledger_account()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    with pytest.raises(exceptions.VirtualMachineError):
        centaur.addLedgerTransaction(365, [
            wrap_entry(id=0, ledger_account_id=0,
                       action=Action.DEBIT, amount=50),
            wrap_entry(id=1, ledger_account_id=3,
                       action=Action.CREDIT, amount=50),
        ], {"from": account})


def test_add_transaction_not_ledger_account_owner():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_transaction_not_ledger_account_owner")

    test_add_ledger_account()
    centaur = get_proxy(config["version"]["latest"])
    bad_account = get_account(index=1)

    with pytest.raises(exceptions.VirtualMachineError):
        centaur.addLedgerTransaction(0, [
            wrap_entry(id=2, ledger_account_id=0,
                       action=Action.DEBIT, amount=50),
            wrap_entry(id=3, ledger_account_id=1,
                       action=Action.CREDIT, amount=50)
        ], {"from": bad_account})


def test_get_entry_by_id():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_get_entry_by_id")

    test_add_transaction()
    centaur = get_proxy(config["version"]["latest"])
    other_account = get_account(index=1)

    entry = Entry(centaur.getEntryById(0, {"from": other_account}))
    expected_entry = Entry(wrap_entry(
        id=0, ledger_account_id=0, action=Action.DEBIT, amount=50
    ))
    assert entry == expected_entry, \
        f"Expected:{str(ex[expected_entry].__dict__)} != Actual:{entry.__dict__}"


def test_get_entries_by_transaction_id():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_get_entries_by_transaction_id")

    test_add_multi_entry_transaction()
    centaur = get_proxy(config["version"]["latest"])
    account = get_account(index=0)

    raw_entries = centaur.getUserEntriesForTransaction(0, {"from": account})
    assert(len(raw_entries)) == 3

    entries = [Entry(raw) for raw in raw_entries]

    expected = [
        Entry(wrap_entry(
            id=0, ledger_account_id=0, action=Action.DEBIT, amount=50
        )),
        Entry(wrap_entry(
            id=1, ledger_account_id=1, action=Action.CREDIT, amount=25
        )),
        Entry(wrap_entry(
            id=2, ledger_account_id=1, action=Action.CREDIT, amount=25
        )),
    ]

    for exp, actual in zip(expected, entries):
        assert exp == actual, \
            f"Expected:{str(exp.__dict__)} != Actual:{actual.__dict__}"


def test_get_user_accounts():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_get_user_accounts")

    account = get_account()
    deploy_centaur()
    centaur = upgrade_centaur()

    centaur.addLedgerAccount("Cash", 0, {"from": account})
    centaur.addLedgerAccount("Debt", 1, {"from": account})
    ledger_accounts_ids = centaur.getUserAccounts({"from": account})

    assert len(ledger_accounts_ids) == 2
    assert ledger_accounts_ids == (0, 1)

    account1 = get_account(index=1)
    centaur.addLedgerAccount("Receivable", 0, {"from": account1})
    ledger_accounts_ids = centaur.getUserAccounts({"from": account1})
    print(ledger_accounts_ids)
    assert len(ledger_accounts_ids) == 1
    assert ledger_accounts_ids[0] == 2
