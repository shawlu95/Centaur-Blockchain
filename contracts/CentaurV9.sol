//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

contract CentaurV9 {
    mapping(address => uint256[]) public userAccountsMap;
    LedgerAccount[] public allAccounts;

    mapping(address => uint256[]) public userTransactionsMap;
    LedgerTransaction[] public allTransactions;

    mapping(uint256 => uint256[]) public accountTransactionMap;

    LedgerEntry[] public allEntries;

    enum ACCOUNT_TYPE {
        ASSET,
        LIABILITY,
        SHAREHOLDER_EQUITY,
        TEMPORARY
    }

    enum ACTION {
        DEBIT,
        CREDIT
    }

    struct LedgerAccount {
        address owner;
        uint256 id;
        ACCOUNT_TYPE accountType;
        string accountName;
        uint256 debit;
        uint256 credit;
        uint256 transactionCount;
        uint256 deleted;
    }

    struct LedgerTransaction {
        address owner;
        int256 date;
        uint256 id;
        string memo;
        uint256[] entries;
        uint256 deleted;
    }

    struct LedgerEntry {
        uint256 id;
        uint256 ledgerAccountId;
        ACTION action;
        uint256 amount;
    }

    event AddLedgerAccount(
        address indexed _owner,
        uint256 _accountId,
        string _accountName
    );

    event UpdateLedgerAccount(
        address indexed _owner,
        uint256 _accountId,
        string _accountName
    );

    event UpdateLedgerAccountType(
        address indexed _owner,
        uint256 _accountId,
        ACCOUNT_TYPE _accountType
    );

    event UpdateLedgerTransaction(
        address indexed _owner,
        uint256 _oldId,
        uint256 _newId
    );

    event DeleteLedgerTransaction(
        address indexed _owner,
        uint256 _transactionId
    );

    event DeleteLedgerAccount(address indexed _owner, uint256 _accountId);
    event AddLedgerTransaction(address indexed _owner, uint256 _transactionId);

    function addLedgerAccount(
        string memory _accountName,
        ACCOUNT_TYPE _accountType
    ) public {
        for (uint256 i = 0; i < userAccountsMap[msg.sender].length; i++) {
            LedgerAccount memory existAcc = allAccounts[
                userAccountsMap[msg.sender][i]
            ];
            require(
                keccak256(bytes(existAcc.accountName)) !=
                    keccak256(bytes(_accountName)),
                "Account exists!"
            );
        }
        uint256 nextId = allAccounts.length;
        LedgerAccount memory newAccount = LedgerAccount(
            msg.sender,
            nextId,
            _accountType,
            _accountName,
            0,
            0,
            0,
            0
        );
        allAccounts.push(newAccount);
        userAccountsMap[msg.sender].push(nextId);
        emit AddLedgerAccount(msg.sender, nextId, _accountName);
    }

    function updateLedgerAccount(uint256 _accountId, string memory _accountName)
        public
    {
        require(_accountId < allAccounts.length, "Account does not exist!");
        LedgerAccount memory acc = allAccounts[_accountId];
        require(acc.owner == msg.sender, "Not owner of account!");
        acc.accountName = _accountName;
        emit UpdateLedgerAccount(msg.sender, _accountId, _accountName);
    }

    function deleteAccountById(uint256 _accountId) public {
        LedgerAccount storage acc = allAccounts[_accountId];
        require(acc.owner == msg.sender, "Not owner of account!");
        require(acc.transactionCount == 0, "Account cannot have transactions!");
        acc.deleted = 1;
        emit DeleteLedgerAccount(msg.sender, _accountId);
    }

    function addLedgerTransaction(
        int256 _date,
        string calldata _memo,
        LedgerEntry[] calldata _ledgerEntries
    ) public {
        require(
            validateLedgerTransaction(_ledgerEntries) == true,
            "Invalid transaction!"
        );

        commitTransaction(_date, _memo, _ledgerEntries);
    }

    function addLedgerTransactions(
        uint8[] calldata _txnSizes,
        int256[] calldata _dates,
        string[] calldata _memos,
        LedgerEntry[] calldata _ledgerEntries
    ) public {
        require(_txnSizes.length > 0, "Empty _txnSizes array!");
        require(_dates.length > 0, "Empty _dates array!");
        require(_ledgerEntries.length > 0, "Empty _ledgerEntries array!");
        require(
            _txnSizes.length == _dates.length,
            "_txnSizes and _dates not same size!"
        );

        uint8 currentTxnId = 0;
        uint8 nextTxnSize = _txnSizes[0];
        uint256 currentTxnSize = 0;
        LedgerEntry[] memory entries = new LedgerEntry[](nextTxnSize);

        for (uint8 i = 0; i < _ledgerEntries.length; i++) {
            if (currentTxnSize == nextTxnSize) {
                require(
                    validateLedgerTransaction(entries) == true,
                    "Invalid transaction!"
                );
                commitTransaction(
                    _dates[currentTxnId],
                    _memos[currentTxnId],
                    entries
                );

                currentTxnId += 1;
                nextTxnSize = _txnSizes[currentTxnId];
                entries = new LedgerEntry[](nextTxnSize);
                currentTxnSize = 0;
            }
            entries[currentTxnSize] = _ledgerEntries[i];
            currentTxnSize += 1;
        }
        // Commit lLast transaction of the batch
        require(
            validateLedgerTransaction(entries) == true,
            "Invalid transaction!"
        );
        commitTransaction(_dates[currentTxnId], _memos[currentTxnId], entries);
    }

    function updateTransaction(
        uint256 _transactionId,
        string calldata _memo,
        int256 _date,
        LedgerEntry[] calldata _ledgerEntries
    ) public {
        require(_transactionId < allTransactions.length);
        deleteTransactionById(_transactionId);
        addLedgerTransaction(_date, _memo, _ledgerEntries);

        uint256[] storage transactionIds = userTransactionsMap[msg.sender];
        emit UpdateLedgerTransaction(
            msg.sender,
            _transactionId,
            transactionIds[transactionIds.length - 1]
        );
    }

    function deleteTransactionById(uint256 _transactionId) public {
        LedgerTransaction storage txn = allTransactions[_transactionId];
        require(txn.owner == msg.sender, "Not owner of transaction!");
        for (uint256 i = 0; i < txn.entries.length; i++) {
            LedgerEntry memory entry = allEntries[txn.entries[i]];

            LedgerAccount storage acc = allAccounts[entry.ledgerAccountId];
            if (entry.action == ACTION.DEBIT) {
                acc.debit -= entry.amount;
            } else if (entry.action == ACTION.CREDIT) {
                acc.credit -= entry.amount;
            }
            acc.transactionCount -= 1;
        }
        txn.deleted = 1;
        emit DeleteLedgerTransaction(msg.sender, _transactionId);
    }

    function validateLedgerTransaction(LedgerEntry[] memory _ledgerEntries)
        internal
        returns (bool)
    {
        uint256 debit = 0;
        uint256 credit = 0;
        for (uint256 i = 0; i < _ledgerEntries.length; i++) {
            LedgerEntry memory entry = _ledgerEntries[i];
            require(
                entry.ledgerAccountId < allAccounts.length,
                "Unknown ledger account!"
            );
            require(
                allAccounts[entry.ledgerAccountId].owner == msg.sender,
                "Not owner of ledger account!"
            );
            if (entry.action == ACTION.DEBIT) {
                debit = debit + entry.amount;
            } else if (entry.action == ACTION.CREDIT) {
                credit = credit + entry.amount;
            }
        }
        require(credit == debit, "Credit must equal debit!");
        return true;
    }

    function commitTransaction(
        int256 _date,
        string calldata _memo,
        LedgerEntry[] memory _ledgerEntries
    ) internal {
        uint256 nextTransactionId = allTransactions.length;
        uint256 nextEntryId = allEntries.length;

        allTransactions.push(
            LedgerTransaction({
                owner: msg.sender,
                date: _date,
                id: nextTransactionId,
                memo: _memo,
                deleted: 0,
                entries: new uint256[](0)
            })
        );
        LedgerTransaction storage latest = allTransactions[nextTransactionId];

        for (uint256 i = 0; i < _ledgerEntries.length; i++) {
            LedgerEntry memory entry = _ledgerEntries[i];
            entry.id = nextEntryId + i;
            allEntries.push(entry);
            latest.entries.push(entry.id);
            LedgerAccount storage acc = allAccounts[entry.ledgerAccountId];
            if (entry.action == ACTION.DEBIT) {
                acc.debit += entry.amount;
            } else if (entry.action == ACTION.CREDIT) {
                acc.credit += entry.amount;
            }
            acc.transactionCount += 1;
        }
        userTransactionsMap[msg.sender].push(nextTransactionId);

        emit AddLedgerTransaction(msg.sender, nextTransactionId);
    }

    function getUserAccounts(address _user)
        public
        view
        returns (LedgerAccount[] memory)
    {
        return getAccountByIdsInternal(userAccountsMap[_user]);
    }

    function getAccountByIds(uint256[] calldata _ledgerAccountIds)
        public
        view
        returns (LedgerAccount[] memory)
    {
        return getAccountByIdsInternal(_ledgerAccountIds);
    }

    function getAccountByIdsInternal(uint256[] memory _ledgerAccountIds)
        internal
        view
        returns (LedgerAccount[] memory)
    {
        uint256 length = _ledgerAccountIds.length;
        LedgerAccount[] memory accs = new LedgerAccount[](length);
        for (uint256 i = 0; i < length; i++) {
            LedgerAccount memory acc = allAccounts[_ledgerAccountIds[i]];
            accs[i] = acc;
        }
        return accs;
    }

    function getUserTransactionIds(address _user)
        public
        view
        returns (uint256[] memory)
    {
        return userTransactionsMap[_user];
    }

    function getUserTransactionEntries(address _user)
        public
        view
        returns (LedgerTransaction[] memory, LedgerEntry[] memory)
    {
        return getTransactionByIdsInternal(userTransactionsMap[_user]);
    }

    function getTransactionByIds(uint256[] calldata _transactionIds)
        public
        view
        returns (LedgerTransaction[] memory, LedgerEntry[] memory)
    {
        return getTransactionByIdsInternal(_transactionIds);
    }

    function getTransactionByIdsInternal(uint256[] memory _transactionIds)
        internal
        view
        returns (LedgerTransaction[] memory, LedgerEntry[] memory)
    {
        LedgerTransaction[] memory txns = new LedgerTransaction[](
            _transactionIds.length
        );
        uint256 entryCount = 0;
        for (uint256 i = 0; i < _transactionIds.length; i++) {
            LedgerTransaction memory txn = allTransactions[_transactionIds[i]];
            txns[i] = txn;
            entryCount += txn.entries.length;
        }
        LedgerEntry[] memory entries = new LedgerEntry[](entryCount);
        uint256 cursor = 0;
        for (uint256 i = 0; i < _transactionIds.length; i++) {
            LedgerTransaction memory txn = allTransactions[_transactionIds[i]];
            for (uint256 j = 0; j < txn.entries.length; j++) {
                entries[cursor] = allEntries[txn.entries[j]];
                cursor += 1;
            }
        }
        return (txns, entries);
    }

    function getEntryByIds(uint256[] calldata _entryIds)
        public
        view
        returns (LedgerEntry[] memory)
    {
        LedgerEntry[] memory entries = new LedgerEntry[](_entryIds.length);
        for (uint256 i = 0; i < _entryIds.length; i++) {
            LedgerEntry memory entry = allEntries[_entryIds[i]];
            entries[i] = entry;
        }
        return entries;
    }

    function getEntriesForTransaction(uint256 transactionId)
        public
        view
        returns (LedgerEntry[] memory)
    {
        LedgerTransaction memory trans = allTransactions[transactionId];

        uint256 count = trans.entries.length;
        LedgerEntry[] memory entries = new LedgerEntry[](count);

        for (uint256 i = 0; i < count; i++) {
            LedgerEntry memory entry = allEntries[trans.entries[i]];
            entries[i] = entry;
        }
        return entries;
    }

    struct BalanceSheet {
        int256 asset;
        int256 liability;
        int256 equity;
    }

    function getBalanceSheetSnapshot(address _user, int256[] calldata _dates)
        public
        view
        returns (
            int256[] memory,
            int256[] memory,
            int256[] memory
        )
    {
        int256[] memory assets = new int256[](_dates.length);
        int256[] memory liabilities = new int256[](_dates.length);
        int256[] memory equities = new int256[](_dates.length);
        uint256[] memory txnIds = userTransactionsMap[_user];

        BalanceSheet memory bs;
        uint256 nextBreak = 0;
        for (uint256 i = 0; i < txnIds.length; i++) {
            LedgerTransaction memory txn = allTransactions[txnIds[i]];
            if (txn.deleted == 1 || txn.date > _dates[_dates.length - 1]) {
                continue;
            }

            if (txn.date > _dates[nextBreak]) {
                // Save snapshot
                assets[nextBreak] = bs.asset;
                liabilities[nextBreak] = bs.liability;
                equities[nextBreak] = bs.equity;
                nextBreak += 1;
            }

            for (uint256 j = 0; j < txn.entries.length; j++) {
                LedgerEntry memory ent = allEntries[txn.entries[j]];
                LedgerAccount memory acc = allAccounts[ent.ledgerAccountId];
                if (acc.accountType == ACCOUNT_TYPE.ASSET) {
                    if (ent.action == ACTION.DEBIT) {
                        bs.asset += int256(ent.amount);
                    } else if (ent.action == ACTION.CREDIT) {
                        bs.asset -= int256(ent.amount);
                    }
                } else if (acc.accountType == ACCOUNT_TYPE.LIABILITY) {
                    if (ent.action == ACTION.DEBIT) {
                        bs.liability -= int256(ent.amount);
                    } else if (ent.action == ACTION.CREDIT) {
                        bs.liability += int256(ent.amount);
                    }
                } else if (acc.accountType == ACCOUNT_TYPE.SHAREHOLDER_EQUITY) {
                    if (ent.action == ACTION.DEBIT) {
                        bs.equity -= int256(ent.amount);
                    } else if (ent.action == ACTION.CREDIT) {
                        bs.equity += int256(ent.amount);
                    }
                }
            }
        }

        // Save final snapshot
        assets[nextBreak] = bs.asset;
        liabilities[nextBreak] = bs.liability;
        equities[nextBreak] = bs.equity;
        return (assets, liabilities, equities);
    }

    function getUserAccountCount(address _user) public view returns (uint256) {
        return userAccountsMap[_user].length;
    }

    function getUserTransactionCount(address _user)
        public
        view
        returns (uint256)
    {
        return userTransactionsMap[_user].length;
    }

    function getAccountCount() public view returns (uint256) {
        return allAccounts.length;
    }

    function getTransactionCount() public view returns (uint256) {
        return allTransactions.length;
    }

    function getEntriesCount() public view returns (uint256) {
        return allEntries.length;
    }
}
