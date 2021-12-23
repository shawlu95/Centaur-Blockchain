
import os
import shutil
import json
import yaml
from brownie import config


def update_front_end():
    """
    Dump config and build folder to the front-end/src folders
    """

    if config['front_end_src_dir']:
        dst = config['front_end_src_dir']
    else:
        dst = "./front_end/src"

    print(dst)
    copy_folders_to_front_end("./build", os.path.join(dst, "chain-info"))

    with open("brownie-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)

        with open(os.path.join(dst, "brownie-config.json"), "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)


def copy_folders_to_front_end(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main():
    update_front_end()
