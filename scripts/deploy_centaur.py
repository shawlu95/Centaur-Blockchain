from scripts.util import get_account, encode_function_data, get_contract
from brownie import Centaur, CentaurV5, CentaurAdmin, config, network, Contract


def deploy_centaur():
    verify = config["networks"][network.show_active()]["verify"]
    account = get_account()
    centaur_v5 = CentaurV5.deploy(
        {"from": account},
        publish_source=verify
    )

    centaur_admin = CentaurAdmin.deploy(
        {"from": account}, publish_source=verify)

    centaur = Centaur.deploy(
        centaur_v5.address, centaur_admin.address, encode_function_data(),
        {"from": account}, publish_source=verify)

    client = Contract.from_abi("CentaurV3", centaur.address, centaur_v5.abi)
    return client


def main():
    deploy_centaur()
