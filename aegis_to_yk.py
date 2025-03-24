import json
import subprocess
import sys
import argparse
from typing import List, Dict, Any


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

        if not isinstance(data, dict) or "entries" not in data:
            raise ValueError("JSON file must contain an 'entries' array")

        entries = data.get("entries", [])
        if not isinstance(entries, list):
            raise ValueError("The 'entries' field must be an array")

        return entries
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{file_path}': {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def get_existing_accounts() -> List[str]:
    try:
        result = subprocess.run(
            "ykman oath accounts list",
            shell=True,
            check=True,
            text=True,
            capture_output=True,
        )

        # Parse the output and return a list of accounts
        accounts = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return accounts

    except subprocess.CalledProcessError as e:
        print(f"Error listing existing accounts: {e}")
        print(f"Command stderr: {e.stderr}")
        return []


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Add OATH accounts to YubiKey from a JSON file"
    )
    parser.add_argument("json_file", help="JSON file containing TOTP accounts")
    parser.add_argument(
        "-t",
        "--touch",
        choices=["y", "n", "ask"],
        default="ask",
        help="Touch requirement: y (always), n (never), ask (prompt for each "
        "account)",
    )

    return parser.parse_args()


def prompt_for_touch() -> bool:
    while True:
        response = input("Require touch for account? (y/n): ").lower().strip()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        print("Please enter 'y' or 'n'")


def add_account(
    item: Dict[str, Any], existing_accounts: List[str], touch_option: str
) -> bool:
    try:
        info = item.get("info", {})

        flat_item = {
            "type": item.get("type", ""),
            "name": item.get("name", ""),
            "issuer": item.get("issuer", ""),
            "secret": info.get("secret", ""),
            "algo": info.get("algo", "SHA1"),
            "digits": info.get("digits", 6),
            "period": info.get("period", 30),
        }

        account_id = f"{flat_item['issuer']}:{flat_item['name']}"
        if account_id in existing_accounts:
            print("Skipped existing account.")
            return False

        require_touch = False
        if touch_option == "y":
            require_touch = True
        elif touch_option == "n":
            require_touch = False
        elif touch_option == "ask":
            require_touch = prompt_for_touch()
        touch_param = "-t" if require_touch else ""

        command = (
            f"ykman oath accounts add "
            f'-o {flat_item["type"]} '
            f'-d {flat_item["digits"]} '
            f'-a {flat_item["algo"]} '
            f'-i "{flat_item["issuer"]}" '
            f'-P {flat_item["period"]} '
            f"{touch_param} "
            f'"{flat_item["name"]}" '
            f'{flat_item["secret"]}'
        )

        subprocess.run(command, shell=True, check=True, text=True, capture_output=True)

        return True

    except KeyError as e:
        print(f"Error: Missing key in item: {e}")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"Command stderr: {e.stderr}")

    return False


def main():
    args = parse_arguments()

    items = load_json_file(args.json_file)

    print(f"Found {len(items)} accounts in '{args.json_file}'")

    existing_accounts = get_existing_accounts()
    print(f"Found {len(existing_accounts)} existing accounts on YubiKey")

    for index, item in enumerate(items, 1):
        print(
            f"Processing account {index}/{len(items)}: {item.get('name')} "
            f"({item.get('issuer', 'No Issuer')})"
        )
        add_account(item, existing_accounts, args.touch)


if __name__ == "__main__":
    main()
