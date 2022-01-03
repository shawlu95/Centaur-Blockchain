from scripts.util import get_account, get_contract, upgrade, contract_to_mock
from brownie import config, network, Contract


def upgrade_centaur():
    latest_version = config["networks"][network.show_active()]["latest"]
    print("latest_version", latest_version)
    account = get_account()
    centaur_implementation = get_contract(latest_version)
    centaur_proxy = get_contract("Centaur")
    centaur_admin = get_contract("CentaurAdmin")
    upgrade(account, centaur_proxy,
            centaur_implementation.address, centaur_admin)

    client = Contract.from_abi(
        latest_version, centaur_proxy.address, centaur_implementation.abi)
    return client


def main():
    upgrade_centaur()
