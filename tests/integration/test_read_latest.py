from scripts.util import (
    get_account, get_contract,
    wrap_entry, wrap_account, wrap_transaction,
    Action, AccountType,
    Account, Entry, Transaction,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from scripts.deploy_centaur import deploy
from brownie import network, exceptions
import pytest


def test_get_account_by_id():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_add_ledger_account")

    account = get_account()
    centaur = get_contract(contract_name="CentaurV0")

    asset_account_name = "cash"
    account_0 = Account(centaur.getAccountById(0, {"from": account}))
    expected_0 = Account(wrap_account(
        owner=account.address, id=0, account_type=AccountType.ASSET,
        account_name=asset_account_name, deleted=0
    ))
    assert account_0 == expected_0, \
        f"Expected:{str(expected_0.__dict__)} != Actual:{account_0.__dict__}"
