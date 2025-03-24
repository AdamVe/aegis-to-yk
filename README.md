# aegis to yk
Import accounts from Aegis to YubiKey OATH app.

## How to use 
1. install ykman
2. export your Aegis vault and decrypt it
3. connect your YubiKey
4. use `python aegis_to_yk.py vault.json`

## Options
```
options:
  -h, --help            show this help message and exit
  -t {y,n,ask}, --touch {y,n,ask}
                        Touch requirement: y (always), n (never), ask (prompt for each account)
```

## Notes
- currently only works with YubiKeys which don't have password set for OATH, or where ykman "remembers" the password
- the script will always skip existing accounts
- the script does not check if the addition succeeded
