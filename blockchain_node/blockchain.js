// file: blockchain.js

const sha256 = require('sha256');
const { v4: uuid } = require('uuid');

class Blockchain {
    constructor() {
        this.chain = [];
        this.currentData = [];
        this.createNewBlock(100, '0', '0'); // genesis block
    }

    createNewBlock(nonce, previousHash, hash) {
        const newBlock = {
            index: this.chain.length + 1,
            timestamp: Date.now(),
            data: this.currentData,
            nonce,
            hash,
            previousHash
        };

        this.currentData = [];
        this.chain.push(newBlock);
        return newBlock;
    }

    getLastBlock() {
        return this.chain[this.chain.length - 1];
    }

    createNewData(product) {
        this.currentData.push(product);
        return this.getLastBlock()['index'] + 1;
    }

    hashBlock(previousHash, currentData, nonce) {
        const dataString = previousHash + nonce + JSON.stringify(currentData);
        return sha256(dataString);
    }

    proofOfWork(previousHash, currentData) {
        let nonce = 0;
        let hash = this.hashBlock(previousHash, currentData, nonce);

        while (hash.substring(0, 4) !== '0000') {
            nonce++;
            hash = this.hashBlock(previousHash, currentData, nonce);
        }

        return nonce;
    }

    isChainValid(chain) {
        for (let i = 1; i < chain.length; i++) {
            const current = chain[i];
            const prev = chain[i - 1];

            const hash = this.hashBlock(
                prev.hash,
                current.data,
                current.nonce
            );

            if (hash.substring(0, 4) !== '0000') return false;
            if (current.previousHash !== prev.hash) return false;
        }
        return true;
    }
}

module.exports = Blockchain;