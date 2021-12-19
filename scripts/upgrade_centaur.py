from scripts.util import get_account, get_contract, encode_function_data, upgrade
from brownie import Centaur, CentaurV0, CentaurV1, CentaurAdmin, config, network, Contract


def upgrade_centaur():
    verify = config["networks"][network.show_active()]["verify"]
    account = get_account()
    centaur_v1 = CentaurV1.deploy(
        {"from": account},
        publish_source=verify
    )

    centaur = get_contract("Centaur")
    centaur_admin = get_contract("CentaurAdmin")
    upgrade(account, centaur, centaur_v1.address, centaur_admin)

    client = Contract.from_abi("CentaurV1", centaur.address, centaur_v1.abi)
    return client


def main():
    upgrade_centaur()
