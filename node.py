from chain import Chain
from uuid import uuid4
from verification import Verification

class Node:

    def __init__(self):
        """
        Constructor of the Node class
        :var id: the unique id of the node
        :var chain: the chain of the blockchain
        """
        # Unique ID
        self.id = uuid4()
        # Initialize the chain with a unique ID
        self.chain = Chain(self.id)


    def get_transaction_value(self):
        """
        Get the user input for the transaction amount and the recipient's name
        :return: (string, float) recipient's name and amount of the transaction of the user
        """
        recipient = input('Enter the recipient of the transaction: ')
        amount = float(input('Enter the amount of the transaction: '))
        return recipient, amount

    def print_blockchain_elements(self):
        """
        Output th block chain list to the console
        :return: print the elements of the blockchain
        """
        for block in self.chain.blockchain:
            print('Outputting block')
            print(block)
        else:
            print('-' * 20)

    def get_user_choice(self):
        """
        Get the choice of the user
        :return: the choice's number
        """
        user_input = input('Your choice: ')
        return user_input

    def listen_for_input(self):
        waiting_for_input = True
        while waiting_for_input:
            print('Please choose an option:')
            print('1: Add a new transaction value')
            print('2: Mine a new block')
            print('3: Print the block chain')
            print('4: Check transaction validity')
            print('q: Quit')
            user_choice = self.get_user_choice()
            if user_choice == '1':
                recipient, amount = self.get_transaction_value()
                if self.chain.add_transaction(recipient, amount=amount):
                    print('Added transaction')
                else:
                    print('Transaction failed!')
            elif user_choice == '2':
                self.chain.mine_block()
            elif user_choice == '3':
                self.print_blockchain_elements()
            elif user_choice == '4':
                verifier = Verification()
                if verifier.verify_transactions(self.chain.open_transactions, self.chain.get_balance):
                    print('All transactions are valid')
                else:
                    print('There are invalid transactions!')
            elif user_choice == 'q':
                waiting_for_input = False
            else:
                print('Input was invalid, please pick a value from the list')
            verifier = Verification()
            if not verifier.verify_chain(self.chain.blockchain):
                print(self.print_blockchain_elements())
                print('Invalid blockchain!')
                break
            print('Balance of {}: {:6.2f}'.format(self.id, self.chain.get_balance()))
            print('Choice registered')
        else:
            print('User left!')

        print('Done!')


node = Node()
node.listen_for_input()