
import os
import shutil
import json
import yaml


def update_front_end():
    """
    Dump config and build folder to the front-end/src folders
    """
    copy_folders_to_front_end("./build", "./front_end/src/chain-info")

    with open("brownie-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open("./front_end/src/brownie-config.json", "w") as brownie_config_json:
            json.dump(config_dict, brownie_config_json)


def copy_folders_to_front_end(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main():
    update_front_end()
