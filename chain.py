from functools import reduce
import json
from hash_util import hash_block
#import pickle
from block import Block
from transaction import Transaction
from verification import Verification

# Reward that we give to miners for creating a new block
MINING_REWARD = 10


class Chain:
    def __init__(self, hosting_node_id):
        # The starting block for the blockchain
        genesis_block = Block(0, '', [], 100, 0)
        # Initializing the blockchain list with genesis block
        self.blockchain = [genesis_block]
        # Unhandled transactions
        self.open_transactions = []
        # Loading the data from file if it exists
        self.load_data()
        # Name of the host of the blockchain
        self.hosting_node = hosting_node_id

    def save_data(self):
        try:
            ####JSON part
            with open('blockchain.txt', mode='w') as file:
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [tx.__dict__ for tx in block_el.transactions] , block_el.proof, block_el.timestamp) for block_el in self.blockchain]]
                file.write(json.dumps(saveable_chain))
                file.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.open_transactions]
                file.write(json.dumps(saveable_tx))

            ###Pickle part
            # with open('blockchain.p', mode='wb') as file:
            #     save_data = {
            #         'chain': blockchain,
            #         'ot': open_transactions
            #     }
            #     file.write(pickle.dumps(save_data))
        except IOError:
            print('Saving failed!')

    def load_data(self):
        #JSON version
        try:
            with open('blockchain.txt', mode='r') as file:
                file_content = file.readlines()

                #Part of the blockchain
                self.blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in self.blockchain:
                    converted_tx = [Transaction(tx['sender'], tx['recipient'], tx['amount']) for tx in block['transactions']]
                    updated_block = Block(block['index'], block['previous_hash'], converted_tx, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                blockchain = updated_blockchain
                #Part of the transaction
                self.open_transactions = json.loads(file_content[1])
                updated_transactions = []
                for tx in self.open_transactions:
                    updated_tx = Transaction(tx['sender'], tx['recipient'], tx['amount'])
                    updated_transactions.append(updated_tx)
                open_transactions = updated_transactions
        except (IOError, IndexError):
            print('File not found!')

        #Pickle version
        # with open('blockchain.p', mode='rb') as file:
            # file_content = pickle.loads(file.read())
            # global blockchain, open_transactions
            # blockchain = file_content['chain']
            # open_transactions = file_content['ot']

    def proof_of_work(self):
        last_block = self.blockchain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        verifier = Verification()
        while not verifier.valid_proof(self.open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_last_blockchain_value(self):
        """
        Get last value of the blockchain
        :return: the last value to the block chain
        """
        if len(self.blockchain) < 1:
            return None
        return self.blockchain[-1]

    def add_transaction(self, recipient, sender, amount=1.0):
        """
        Add a value to the block chain list
        :param sender: the sender's name of the transaction
        :param recipient: the recipient's name of the transaction
        :param amount: the amount of the transaction (default = 1.0)
        :return: True if transaction if verified, False if not
        """
        transaction = Transaction(sender, recipient, amount)
        verifier = Verification()
        if verifier.verify_transaction(transaction, self.get_balance):
            self.open_transactions.append(transaction)
            self.save_data()
            return True
        else:
            return False

    def mine_block(self):
        """
        Mine a block to the blockchain
        :return: True if the block has been successfully added to the blockchain
        """
        last_block = self.blockchain[-1]
        hashed_block = hash_block(last_block)

        proof = self.proof_of_work()

        reward_transaction = Transaction('MINING', self.hosting_node, MINING_REWARD)
        copied_transaction = self.open_transactions[:]
        copied_transaction.append(reward_transaction)
        block = Block(len(self.blockchain), hashed_block, copied_transaction, proof)
        self.blockchain.append(block)
        self.open_transactions = []
        self.save_data()
        return True

    def get_balance(self):
        """
        Get the balance of a participant via his transactions
        :return: the balance between the amount received and the amount sent
        """
        participant = self.hosting_node # Participant is a unique ID
        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == participant] for block in self.blockchain]
        open_tx_sender = [tx.amount for tx in self.open_transactions
                          if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)

        tx_recipient = [[tx.amount for tx in block.transactions
                         if tx.recipient == participant] for block in self.blockchain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)

        return amount_received - amount_sent