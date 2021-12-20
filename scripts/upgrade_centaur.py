from scripts.util import get_account, get_contract, upgrade, contract_to_mock
from brownie import config, network, Contract


def upgrade_centaur():
    verify = config["networks"][network.show_active()]["verify"]
    latest_version = config["networks"][network.show_active()]["latest"]
    CentaurNew = contract_to_mock[latest_version]
    account = get_account()
    centaur_new = CentaurNew.deploy(
        {"from": account},
        publish_source=verify
    )
    # centaur_new = get_contract(latest_version)

    centaur = get_contract("Centaur")
    centaur_admin = get_contract("CentaurAdmin")
    upgrade(account, centaur, centaur_new.address, centaur_admin)

    client = Contract.from_abi(latest_version, centaur.address, CentaurNew.abi)
    return client


def main():
    upgrade_centaur()
