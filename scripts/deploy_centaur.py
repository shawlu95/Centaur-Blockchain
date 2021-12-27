from scripts.util import get_account, encode_function_data, get_contract, contract_to_mock
from brownie import Centaur, CentaurV6, CentaurAdmin, config, network, Contract


def deploy_centaur():
    current_network = network.show_active()
    verify = config["networks"][current_network]["verify"]
    latest = config["networks"][current_network]["latest"]
    account = get_account()
    centaur_implementation = contract_to_mock[latest].deploy(
        {"from": account},
        publish_source=verify
    )


def deploy_proxy_and_admin():
    current_network = network.show_active()
    verify = config["networks"][current_network]["verify"]
    latest = config["networks"][current_network]["latest"]
    account = get_account()
    centaur_implementation = get_contract(latest)
    centaur_admin = CentaurAdmin.deploy(
        {"from": account}, publish_source=verify)

    centaur_proxy = Centaur.deploy(
        centaur_implementation.address, centaur_admin.address, encode_function_data(),
        {"from": account}, publish_source=verify)


def main():
    deploy_centaur()
