"""
Creation of the BlockChain module
It allows the user to create a new blockchain, to get the chain, to set the chain, to get the open transactions in it, to save the new data in the blockchain, to get all the nodes in the network
"""

import json
import requests

from functools import reduce
from utility.hash_util import hash_block
from block import Block
from transaction import Transaction
from utility.verification import Verification
from wallet import Wallet


MINING_REWARD = 10  # Reward that we give to miners for creating a new block


class BlockChain:
    def __init__(self, public_key, node_id):
        """
        Initialize the blockchain with default values.

        :param public_key str: The unique ID of the host of the blockchain.
        :param node_id int: ID of the node, represented by the port.
        :var blockchain list: the list of blocks of the blockchain
        :var open_transactions list: The list of all unhandled transactions initialised by the empty list.
        :var chain list: Blockchain containing the genesis block.
        :var genesis_block Block: The first block to be generated in a blockchain.
        :var peer_nodes set: Set of all the participants (nodes) in the network.
        :var resolve_conflicts bool: Manages resolving conflicts, no conflicts to solve at initialisation (False).
        :returns Block: Yields a blockchain's instance.
        """
        genesis_block = Block(0, '', [], 100, 0)
        self.chain = [genesis_block]
        self.__open_transactions = []
        self.public_key = public_key
        self.__peer_nodes = set()
        self.node_id = node_id
        self.resolve_conflicts = False
        # Loading the data from file if it exists, must be at the end, after doing all above initialisations
        self.load_data()

    @property
    def chain(self):
        """
        Getter of the chain of the blockchain.

        :returns list: Chain of the blockchain.
        """
        return self.__chain[:]

    @chain.setter
    def chain(self, val):
        """
        Setter of the chain of the blockchain.

        :param val list: New value of the blockchain.
        :returns: None.
        """
        self.__chain = val

    def get_open_transactions(self):
        """
        Getter of a copy of the open transactions.

        :returns list: The open transactions.
        """
        return self.__open_transactions[:]

    def save_data(self):
        """
        Saves the whole blockchain into a file named 'blockchain.txt'.

        :var saveable_chain list: Construction of the 
        :var saveable_tx list: Construction of all of the transactions.
        :returns: None.
        :raises IOError: If the file is not created or not written properly an error is raised and it prints a message that the saving has failed.
        """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='w') as file:
                saveable_chain = [block.__dict__ for block in [Block(block_el.index, block_el.previous_hash, [
                                                                     tx.__dict__ for tx in block_el.transactions], block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                file.write(json.dumps(saveable_chain))
                file.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                file.write(json.dumps(saveable_tx))
                file.write('\n')
                # Updates the number of nodes in the network
                file.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('Saving failed!')

    def load_data(self):
        """
        Loads the blockchain from the blockchain.txt file. Displays a failure message if there is an error.

        :var file_content list: Reads the line of the file of the blockchain.
        :var blockchain dict: Blockchain red from the file.
        :var updated_blockchain list: The updated blockchain after loading after loading from the file.
        :var updated_transactions list: The updated transactions after loading from the file.
        :var peer_nodes dict: All peer nodes of the network red from the file.
        :returns: None.
        :raises IOError: Error if the file is not properly red. 
        :raises IndexError: Error in the loops on the blocks or on the transactions.
        """
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode='r') as file:
                file_content = file.readlines()

                # Part of the blockchain
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                for block in blockchain:
                    converted_tx = [Transaction(
                        tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
                    updated_block = Block(
                        block['index'], block['previous_hash'], converted_tx, block['proof'], block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.chain = updated_blockchain

                # Part of the transaction
                self.__open_transactions = json.loads(file_content[1][:-1])
                updated_transactions = []
                for tx in self.__open_transactions:
                    updated_tx = Transaction(
                        tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                    updated_transactions.append(updated_tx)
                self.__open_transactions = updated_transactions  # Loads the connected nodes
                peer_nodes = json.loads(file_content[2])
                self.__peer_nodes = set(peer_nodes)
        except (IOError, IndexError):
            print('File not found!')

    def proof_of_work(self):
        """
        Verify the integrity of the blockchain.

        :var last_block list: The last block of the blockchain.
        :var last_hash Block: The hash of the last block of last_block.
        :var proof int: The proof number of the blockchain initialised at 0.
        :returns int: If the proof equals 0 then the block is valid, if it not it is invalid.
        """
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_last_blockchain_value(self):
        """
        Get last block of the blockchain.

        :returns list: The last block to the blockchain, None if its length is less than 1.
        """
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    def add_transaction(self, recipient, sender, signature, amount=1.0, is_receiving=False):
        """
        Add a transaction to the blockchain and broadcasts the transactions into the network.

        :param sender str: the sender's name of the transaction
        :param recipient str: the recipient's name of the transaction
        :param signature str: Signature of the transaction.
        :param amount: the amount of the transaction, Default=1.0.
        :param is_receiving: False when creating a new transaction on this node, True when receiving a broadcast transaction
        :returns: True if transaction if verified, False if not.
        :raises ConnectionError: If the POST is not sent properly.
        """
        transaction = Transaction(sender, recipient, signature, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            if not is_receiving:
                # Looping through all nodes to broadcast the infos:
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        response = requests.post(url, json={
                                                 'sender': sender, 'recipient': recipient, 'amount': amount, 'signature': signature})
                        if response.status_code == 400 or response.status_code == 500:
                            print('Transaction declined, needs resolving')
                            return False
                    except requests.exceptions.ConnectionError:
                        continue
                    return True
                else:
                    return False

    def mine_block(self):
        """
        Mine a block for the blockchain.
        :var last_block Block:
        :var hashed_block str: Hash of the block.
        :var proof int: Proof of work of the block. 0: valid, other: invalid.
        :var reward_transaction Transaction: A transacion corresponding to a mining's action.
        :var copied_transaction Transaction: A copy of the transactions of the blockchain.
        :var block Block: 
        :returns bool: True if the block has been successfully added to the blockchain, false if not.
        :raised ConnectionError:
        """
        if self.public_key == None:
            return None
        last_block = self.__chain[-1]
        hashed_block = hash_block(last_block)

        proof = self.proof_of_work()

        reward_transaction = Transaction(
            'MINING', self.public_key, '', MINING_REWARD)
        copied_transaction = self.__open_transactions[:]
        for tx in copied_transaction:
            if not Wallet.verify_transaction(tx):
                return None
        copied_transaction.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block,
                      copied_transaction, proof)
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        # Broadcast the block to the network:
        for node in self.__peer_nodes:
            url = 'http://{}/broadcast-block'.format(node)
            converted_block = block.__dict__.copy()
            converted_block['transactions'] = [
                tx.__dict__ for tx in converted_block['transactions']]
            try:
                response = requests.post(url, json={'block': converted_block})
                if response.status_code == 400 or response.status_code == 500:
                    print('Block declined, needs resolving')
                if response.status_code == 409:
                    self.resolve_conflicts = True
            except requests.exceptions.ConnectionError:
                continue
        return block

    def get_balance(self, sender=None):
        """
        Get the balance of a participant via his transactions.

        :return: the balance between the amount received and the amount sent
        """
        if sender == None:
            # This tests if the public key exists (referenced by hositng_node)
            if self.public_key == None:
                return None
            participant = self.public_key  # Participant is a unique ID
        else:
            participant = sender
        tx_sender = [[tx.amount for tx in block.transactions
                      if tx.sender == participant] for block in self.__chain]
        open_tx_sender = [tx.amount for tx in self.__open_transactions
                          if tx.sender == participant]
        tx_sender.append(open_tx_sender)
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                             if len(tx_amt) > 0 else tx_sum + 0, tx_sender, 0)

        tx_recipient = [[tx.amount for tx in block.transactions
                         if tx.recipient == participant] for block in self.__chain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt)
                                 if len(tx_amt) > 0 else tx_sum + 0, tx_recipient, 0)

        return amount_received - amount_sent

    def add_peer_node(self, node):
        """
        Adds a new node to the network.

        :return: None
        :param node: The node URL which should be added
        """
        self.__peer_nodes.add(node)
        self.save_data()

    def remove_peer_node(self, node):
        """
        Removes a node to the network
        :return: None
        :param node: The node URL which should be removed
        """
        self.__peer_nodes.discard(node)
        self.save_data()

    def get_peer_nodes(self):
        """
        Function that gives all the connected peer nodes in the network.

        :return: a list of all connected peer nodes.
        """
        return list(self.__peer_nodes)

    def add_block(self, block):
        """
        Function that adds a block to the blockchain.

        :param block: the block to add to the blockchain
        :returns: false if the block has not been added, true if it has
        """
        # Validation of the block
        transactions = [Transaction(
            tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']]
        proof_is_valid = Verification.valid_proof(
            transactions[:-1], block['previous_hash'], block['proof'])
        hashes_match = hash_block(self.chain[-1]) == block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        # Add the block
        converted_block = Block(
            block['index'], block['previous_hash'], transactions, block['proof'], block['timestamp'])
        self.__chain.append(converted_block)
        # Manage open transactions and forces them to update
        stored_transactions = self.__open_transactions[:]
        for itx in block['transactions']:
            for opentx in stored_transactions:
                if opentx.sender == itx['sender'] and opentx.recipient == itx['recipient'] and opentx.amount == itx['amount'] and opentx.signature == itx['signature']:
                    try:
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('Item was already removed')
        self.save_data()
        return True

    def to_resolve_conflicts(self):
        """
        Function that resolve conflicts between nodes - Implementation of a consensus.

        :returns: Returns true if the blockchain has been replaced, false if not
        """
        winner_chain = self.chain
        replace = False  # whether or not our blockchain has been replaced or not
        for node in self.__peer_nodes:
            url = 'https://{}/chain'.format(node)
            try:
                response = requests.get(url)
                node_chain = response.json()
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(tx['sender'], tx['recipient'], tx['signature'], tx['amount'])
                                                                             for tx in block['transactions']], block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length = len(node_chain)
                local_chain_length = len(self.chain)
                if node_chain_length > local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain = node_chain  # We update the valid chain for the longest valid
                    replace = True
            except requests.exceptions.ConnectionError:
                continue  # We simply continue with the next peer node, we don't want to break the solving because of one node
        self.resolve_conflicts = False  # Because the conflict has been solved by above
        self.chain = winner_chain
        if replace:
            self.__open_transactions = []
        self.save_data()
        return replace
