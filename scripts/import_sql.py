import pandas as pd
from sqlalchemy import create_engine
import os


class Database():
    def __init__(self, database, username="root", password="12345678", host="127.0.0.1", port=3306):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database
        self.connect()

    def connect(self):
        self.engine = create_engine('mysql+mysqldb://%s:%s@%s:%i/%s'
                                    % (self.username, self.password, self.host, self.port, self.database))


if __name__ == '__main__':
    db = Database(database="centaur")

    df = pd.read_csv(os.path.join(os.getcwd(), "..", "data",
                     "polygon-test", "entry_sql.csv"), header=None)
    df.columns = ['entry_id', 'transaction_id',
                  'ledger_account_id', 'account_type', 'action', 'amount', 'date', 'owner', 'deleted']
    df.to_sql('entry_denormalized', db.engine,
              if_exists='replace', index=False)

    df = pd.read_csv(os.path.join(os.getcwd(), "..", "data",
                     "polygon-test", "LedgerAccount.csv"), header=None)
    df.columns = ['owner', 'id', 'accountType', 'accountName',
                  'debit', 'credit', 'transactionCount', 'deleted']
    df.to_sql('LedgerAccount', db.engine, if_exists='append', index=False)

    df = pd.read_csv(os.path.join(os.getcwd(), "..", "data",
                     "polygon-test", "LedgerEntry.csv"), header=None)
    df.columns = ['id', 'ledgerAccountId', 'action', 'amount']
    df.to_sql('LedgerEntry', db.engine, if_exists='append', index=False)

    df = pd.read_csv(os.path.join(os.getcwd(), "..", "data",
                     "polygon-test", "TransactionEntryLink.csv"), header=None)
    df.columns = ['transactionId', 'entryId']
    df.to_sql('TransactionEntryLink', db.engine,
              if_exists='append', index=False)

    df = pd.read_csv(os.path.join(os.getcwd(), "..", "data",
                     "polygon-test", "LedgerTransaction.csv"), header=None)
    df.columns = ['owner', 'date', 'id', 'memo', 'deleted']
    df.to_sql('LedgerTransaction', db.engine, if_exists='append', index=False)
