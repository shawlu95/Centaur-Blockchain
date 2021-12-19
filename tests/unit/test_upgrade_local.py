from scripts.util import (
    get_account, encode_function_data, upgrade,
    AccountType,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS)
from brownie import network, CentaurV0, CentaurV1, CentaurAdmin, Centaur, Contract, exceptions
import pytest


def test_proxy_delegates_call():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_proxy_delegates_call")

    account = get_account(index=0)
    proxy_admin = CentaurAdmin.deploy({"from": account})
    centaur_v0 = CentaurV0.deploy({"from": account})

    proxy = Centaur.deploy(
        centaur_v0.address,
        proxy_admin.address,
        encode_function_data(),
        {"from": account, "gas_limit": 1000000},
    )
    proxy_centaur = Contract.from_abi(
        "CentaurV0", proxy.address, centaur_v0.abi)

    assert proxy_centaur.getTransactionCount() == 0
    assert proxy_centaur.getAccountCount() == 0
    assert proxy_centaur.getEntriesCount() == 0

    proxy_centaur.addLedgerAccount(
        "cash", AccountType.ASSET.value, {"from": account})
    assert proxy_centaur.getAccountCount() == 1

    with pytest.raises(exceptions.VirtualMachineError):
        proxy_centaur.addLedgerAccount(
            "expense", AccountType.TEMPORARY.value, {"from": account})
    assert proxy_centaur.getAccountCount() == 1
    return proxy_centaur


def test_proxy_upgrade():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skip: test_proxy_delegates_call")

    proxy_centaur = test_proxy_delegates_call()
    assert proxy_centaur.getAccountCount() == 1

    account = get_account(index=0)
    centaurV1 = CentaurV1.deploy({"from": account})

    proxy = Centaur[-1]
    proxy_admin = CentaurAdmin[-1]

    upgrade(account, proxy, centaurV1, proxy_admin_contract=proxy_admin)

    proxy_centaur = Contract.from_abi(
        "CentaurV1", proxy.address, CentaurV1.abi)

    assert proxy_centaur.getAccountCount() == 1
    proxy_centaur.addLedgerAccount(
        "expense", AccountType.TEMPORARY.value, {"from": account})
    assert proxy_centaur.getAccountCount() == 2
