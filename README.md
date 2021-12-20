## Centaur Blockchain
Centaur's mission is to eliminate accounting fraud.

### BSC Testnet
- `0x06DA78824018d281260d4919710965AfdB93A8C2`: CentaurAdmin
- `0x965516A404439FaA0Ab2a79B65Ec39A66855706F`: Centaur (proxy)
- `0xd376A18507f0fb677b7818fD19213b306eBD7F6A`: Verified, private member fields.
- `0xEfe5a5981E8116A6A3E80B755E20edBdED48BAe9`: Verified, public member fields.
- `0x5FE138e58Bd8DeF2fA9FF8edE024D195aE1DA6ec`: CentaurV0
- `0xb91DFC40fEaAf850ce69bA84AdBc2AB337d68d61`: CentaurV1
- `0xFdD6198f151768207d5369cE4C1A94B3f2b5540f`: CentaurV2
    * fixed a bug where AccountType cannot be updated
    * enable update account type
- `0x5Ad07ABB9cDF025981ee18a7F26B10Db25fFB2dB`: CentaurV3
    * Maintain previous method `updateLedgerAccount` from CentaurV1
    * to modify account type, use `UpdateLedgerAccountType`

### Polygon Testnet
- `0x8C582894d4A566a16b1EfE1b5C53aBf8F0538Fa2`: CentaurV4
    * Add `getUserTransactionEntries`
- `0x6688B3FacCB8B2318aB791BF0351C15bdD42D26E`: CentaurV5
    * Add `getEntryByIds`, `getTransactionByIds`

#### Integration Test

```bash
brownie run scripts/deploy_centaur.py --network bsc-test
brownie run scripts/upgrade_centaur.py --network bsc-test
```