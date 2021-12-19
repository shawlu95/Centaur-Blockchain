from scripts.util import get_account, get_contract, encode_function_data, upgrade
from brownie import Centaur, CentaurV0, CentaurV1, CentaurAdmin, config, network, Contract


def deploy():
    verify = config["networks"][network.show_active()]["verify"]
    account = get_account()
    centaur_v0 = CentaurV0.deploy(
        {"from": account},
        publish_source=verify
    )

    centaur_admin = CentaurAdmin.deploy(
        {"from": account}, publish_source=verify)

    centaur = Centaur.deploy(
        centaur_v0.address, centaur_admin.address, encode_function_data(),
        {"from": account}, publish_source=verify)

    client = Contract.from_abi("CentaurV0", centaur.address, centaur_v0.abi)
    return client


def main():
    deploy()
