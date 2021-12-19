## Centaur Blockchain
Centaur's mission is to eliminate accounting fraud.

### BSC Testnet Contracts
- `0xd376A18507f0fb677b7818fD19213b306eBD7F6A`: Verified, private member fields.
- `0xEfe5a5981E8116A6A3E80B755E20edBdED48BAe9`: Verified, public member fields.
- `0x5FE138e58Bd8DeF2fA9FF8edE024D195aE1DA6ec`: CentaurV0
- `0x06DA78824018d281260d4919710965AfdB93A8C2`: CentaurAdmin
- `0x965516A404439FaA0Ab2a79B65Ec39A66855706F`: Centaur (proxy)

#### Integration Test

```bash
brownie run scripts/deploy_centaur.py --network bsc-test
brownie run scripts/upgrade_centaur.py --network bsc-test
```