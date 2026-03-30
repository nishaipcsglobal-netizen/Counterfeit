// file: networkNode.js

const express = require('express');
const bodyParser = require('body-parser');
const Blockchain = require('./blockchain');

const app = express();
const port = 3000;

const bitcoin = new Blockchain();

app.use(bodyParser.json());


// Add product
app.post('/product', (req, res) => {
    const product = req.body;

    const blockIndex = bitcoin.createNewData(product);

    res.json({
        note: `Product will be added in block ${blockIndex}`
    });
});


// Mine block
app.get('/mine', (req, res) => {
    const lastBlock = bitcoin.getLastBlock();
    const previousHash = lastBlock.hash;

    const nonce = bitcoin.proofOfWork(previousHash, bitcoin.currentData);
    const hash = bitcoin.hashBlock(previousHash, bitcoin.currentData, nonce);

    const newBlock = bitcoin.createNewBlock(nonce, previousHash, hash);

    const PORT = process.env.PORT || 3000;
       app.listen(PORT, "0.0.0.0", () => console.log(`Listening on ${PORT}`));

    res.json({
        note: "New block mined",
        block: newBlock
    });
});


// Get blockchain
app.get('/blockchain', (req, res) => {
    res.json(bitcoin);
});


// Verify chain
app.get('/validate', (req, res) => {
    const valid = bitcoin.isChainValid(bitcoin.chain);
    res.json({ valid });
});


app.listen(port, () => {
    console.log(`Running on port ${port}`);
});
