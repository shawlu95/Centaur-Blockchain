from scripts.util import (
    get_account, get_proxy,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from brownie import network, exceptions, config
import pytest


def test_get_recent_transactions():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_ingest_account")

    account = get_account()
    centaur = get_proxy(
        version=config["networks"][network.show_active()]["latest"])

    txns, ents = centaur.getRecentTransaction(account.address, 10)
    print(txns)
    print(ents)
    assert len(txns) == 10


def test_get_transaction_by_page():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_ingest_account")

    account = get_account()
    centaur = get_proxy(
        version=config["networks"][network.show_active()]["latest"])

    txns, ents = centaur.getTransactionByPage(account.address, 0, 10)
    assert len(txns) == 10
