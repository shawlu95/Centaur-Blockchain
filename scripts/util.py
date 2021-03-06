from brownie import (
    accounts,
    config,
    network,
    Centaur,
    CentaurAdmin,
    CentaurV11,
    Contract)
from enum import Enum
import eth_utils

DECIMAL = 9

LOCAL_BLOCKCHAIN_DEV = ["development", "ganache-local"]
FORKED_LOCAL_ENV = ['mainnet-fork', 'mainnet-fork-dev']
LOCAL_BLOCKCHAIN_ENVIRONMENTS = LOCAL_BLOCKCHAIN_DEV + FORKED_LOCAL_ENV


class Action(Enum):
    DEBIT = 0
    CREDIT = 1


class AccountType(Enum):
    ASSET = 0
    LIABILITY = 1
    SHAREHOLDER_EQUITY = 2
    TEMPORARY = 3


class Entry:
    def __init__(self, data):
        self.id = data[0]
        self.ledger_account_id = data[1]
        self.action = Action(data[2])
        self.amount = data[3]

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.ledger_account_id == other.ledger_account_id
            and self.action == other.action
            and self.amount == other.amount
        )


class Account:
    def __init__(self, data):
        self.owner = data[0]
        self.id = data[1]
        self.account_type = AccountType(data[2])
        self.account_name = data[3]
        self.debit = data[4]
        self.credit = data[5]
        self.transaction_count = data[6]
        self.deleted = data[7]

    def __eq__(self, other):
        return (
            self.owner == other.owner
            and self.id == other.id
            and self.account_type == other.account_type
            and self.account_name == other.account_name
            and self.deleted == other.deleted
            and self.debit == other.debit
            and self.credit == other.credit
        )

    def process_entry(self, entry: Entry):
        assert entry.ledger_account_id == self.id, "Ledger Account ID not matched!"
        if entry.action == Action.DEBIT:
            self.debit += entry.amount
        elif entry.action == Action.CREDIT:
            self.credit += entry.amount
        else:
            raise ValueError("Unknown Action")

    def usd_balance(self):
        if self.account_type == AccountType.ASSET:
            balance = self.debit - self.credit
        else:
            balance = - self.debit + self.credit

        return balance / 10 ** DECIMAL

    def formatted_str(self):
        balance = self.usd_balance()
        if balance >= 0:
            return "$ {:,.2f}".format(balance)
        return "($ {:,.2f})".format(- balance)


class Transaction:
    def __init__(self, data):
        self.owner = data[0]
        self.date = data[1]
        self.id = data[2]
        self.memo = data[3]
        self.entry_ids = data[4]
        self.deleted = data[5]

    def __eq__(self, other):
        return (
            self.owner == other.owner
            and self.date == other.date
            and self.id == other.id
            and self.memo == other.memo
            and self.entry_ids == other.entry_ids
            and self.deleted == other.deleted
        )


def wrap_entry(id, ledger_account_id, action: Action, amount):
    return (id, ledger_account_id, action.value, amount)


def wrap_account(owner, id, account_type: AccountType, account_name, debit, credit, transaction_count, deleted):
    return (owner, id, account_type.value, account_name, debit, credit, transaction_count, deleted)


def wrap_transaction(owner, date, id, memo, entry_ids, deleted):
    return (owner, date, id, memo, entry_ids, deleted)


def get_account(index=None, id=None):
    if index:
        # a local account
        return accounts[index]
    if id:
        # brownie accounts list
        return accounts.load(id)
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return accounts[0]
    return accounts.add(config['wallets']['private_key'])


contract_to_mock = {
    "Centaur": Centaur,
    "CentaurV11": CentaurV11,
    "CentaurAdmin": CentaurAdmin
}


def deploy_mocks(contract_name):
    account = get_account()
    if contract_name == "Centaur":
        Centaur.deploy({"from": account})


def get_proxy(version="CentaurV11"):
    centaur = get_contract("Centaur")
    client = Contract.from_abi(
        version, centaur.address, contract_to_mock[version].abi)
    return client


def get_contract(contract_name):
    """
    This function will either:
        - Get an address from the config
        - Or deploy a Mock to use for a network that doesn't have the contract
    Args:
        contract_name (string): This is the name of the contract that we will get
        from the config or deploy
    Returns:
        brownie.network.contract.ProjectContract: This is the most recently deployed
        Contract of the type specified by a dictionary. This could either be a mock
        or a 'real' contract on a live network.
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks(contract_name)
        contract = contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active(
        )][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


def encode_function_data(initializer=None, *args):
    if len(args) == 0 or not initializer:
        # return emptu hex string
        return eth_utils.to_bytes(hexstr="0x")
    return initializer.encode_input(*args)


def upgrade(
        account, proxy,
        new_implementation_address,
        proxy_admin_contract=None,
        initializer=None,
        *args):
    transaction = None
    if proxy_admin_contract:
        if initializer:
            encoded_function_call = encode_function_data(initializer, *args)
            transaction = proxy_admin_contract.upgradeAndCall(
                proxy.address,
                proxy_admin_contract,
                encoded_function_call,
                {"from": account}
            )
        else:
            transaction = proxy_admin_contract.upgrade(
                proxy.address,
                new_implementation_address,
                {"from": account}
            )
    else:
        if initializer:
            encoded_function_call = encode_function_data(initializer, *args)
            transaction = proxy.upgradeToAndCall(
                new_implementation_address, encoded_function_call, {
                    "from": account}
            )
        else:
            transaction = proxy.upgradeTo(
                new_implementation_address, {"from": account})
    return transaction
