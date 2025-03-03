import hashlib
import time
import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

class SmartContract:
    def __init__(self, contract_code):
        self.contract_code = contract_code

    def execute(self, *args, **kwargs):
        exec(self.contract_code, globals(), locals())

class ERupeesBlock:
    def __init__(self, index, previous_hash, timestamp, transactions, nonce=0, staker=None, smart_contract=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.transactions = transactions
        self.nonce = nonce
        self.staker = staker
        self.smart_contract = smart_contract
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True, default=str)
        return hashlib.sha256(block_string.encode()).hexdigest()

class ERupeesBlockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.difficulty = 2
        self.total_supply = 20100001.00000
        self.reserved_for_owner = 100001.00000
        self.current_supply = self.reserved_for_owner
        self.coin_value_in_inr = 1.1
        self.immutable = True
        self.stakers = {}
        self.confirmation_required = 5
        self.daily_release = 550.00000
        self.halving_interval = 2 * 365 * 24 * 60 * 60
        self.last_halving_time = time.time()

    def create_genesis_block(self):
        return ERupeesBlock(0, "0", time.time(), "Genesis Block")

    def get_latest_block(self):
        return self.chain[-1]

    def apply_halving(self):
        if time.time() - self.last_halving_time >= self.halving_interval:
            self.daily_release /= 2
            self.last_halving_time = time.time()

    def add_block(self, transactions, amount, miner=None, smart_contract_code=None):
        if self.immutable:
            return "Blockchain is immutable. No new blocks can be added."
        
        self.apply_halving()
        amount = round(amount, 5)
        
        if amount > self.daily_release:
            return "Transaction exceeds daily release limit!"
        
        if self.current_supply + amount > self.total_supply:
            return "Transaction exceeds total supply limit!"
        
        latest_block = self.get_latest_block()
        smart_contract = SmartContract(smart_contract_code) if smart_contract_code else None
        new_block = ERupeesBlock(latest_block.index + 1, latest_block.hash, time.time(), transactions, smart_contract=smart_contract)
        
        if random.random() < 0.5:
            self.mine_block(new_block)
        else:
            new_block.staker = self.select_staker()
        
        self.chain.append(new_block)
        self.current_supply += amount
        return "Block added successfully."

    def mine_block(self, block):
        if self.immutable:
            return "Blockchain is immutable. Mining is disabled."
        
        while block.hash[:self.difficulty] != "0" * self.difficulty:
            block.nonce += 1
            block.hash = block.calculate_hash()

    def select_staker(self):
        if not self.stakers:
            return None
        return random.choices(list(self.stakers.keys()), weights=self.stakers.values())[0]

    def add_staker(self, address, stake_amount):
        if address in self.stakers:
            self.stakers[address] += stake_amount
        else:
            self.stakers[address] = stake_amount

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def is_transaction_confirmed(self, transaction):
        confirmations = 0
        for block in reversed(self.chain):
            if transaction in block.transactions:
                confirmations += 1
            if confirmations >= self.confirmation_required:
                return True
        return False

    def convert_to_inr(self, amount):
        return round(amount * self.coin_value_in_inr, 2)

blockchain = ERupeesBlockchain()

@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.get_json()
    transactions = data.get('transactions')
    amount = data.get('amount', 0.0)
    result = blockchain.add_block(transactions, amount)
    return jsonify({'message': result})

@app.route('/get_chain', methods=['GET'])
def get_chain():
    chain_data = [block.__dict__ for block in blockchain.chain]
    return jsonify({'chain': chain_data})

@app.route('/is_valid', methods=['GET'])
def is_valid():
    return jsonify({'valid': blockchain.is_chain_valid()})

@app.route('/convert_to_inr', methods=['POST'])
def convert_to_inr():
    data = request.get_json()
    amount = data.get('amount', 0.0)
    return jsonify({'inr_value': blockchain.convert_to_inr(amount)})

if __name__ == '__main__':
    app.run(debug=True)
