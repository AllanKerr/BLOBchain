from chain import Chain
import math
import time
import threading
import logging


class Miner:

    """
    The difficulty target in number of seconds that the
    difficulty should be adjusted to try and ensure a block
    is mined every DIFFICULTY_TARGET seconds.
    """
    DIFFICULTY_TARGET = 15.0

    def __init__(self):

        # the set of blobs that have yet to be validated
        self.pending_blobs_lock = threading.Lock()
        self.pending_blobs = set()

        self.chain_lock = threading.Lock()

        self.chain = Chain()
        self.mine_event = []

        # If the block chain has been modified since mining started
        self.dirty = True

    def mine(self):
        """
        Starts mining blocks by creating new blocks, searching for valid nonces
        and adding them to the chain. This method never returns.
        """
        while True:
            while not self.dirty and not cur.is_valid():
                cur.next()

            with self.chain_lock:
                if not self.dirty:
                    self.___add_block(cur)

                logging.debug("Valid chain: %s", self.chain.is_valid())

                difficulty = self.__compute_difficulty()
                with self.pending_blobs_lock:
                    cur = self.chain.next(difficulty, self.pending_blobs)
                self.dirty = False

    def add(self, msg):
        """
        Add a Blob Message to the set of pending blobs to be
        added to the body of the next block that is created.
        :param msg: The Blob Message as a BlobMessage protocol buffer object.
        """
        with self.pending_blobs_lock:
            self.pending_blobs.add(msg)

    def receive_block(self, block, chain_cost):
        """
        Receive a block that was mined from a peer node in the network.
        :param block: The block that was mined.
        :param chain_cost: The total cost of the chain that the peer node is working on.
        """
        with self.chain_lock:

            # only set dirty if chain is modified
            self.dirty = True

    def ___add_block(self, block):
        """
        Add a block to the chain. This involves removing all of the blobs in its
        body from the pending blobs set.
        :param block: The block to be added.
        """
        self.chain.add(block)

        for handler in self.mine_event:
            handler(block)

        with self.pending_blobs_lock:
            self.pending_blobs.difference_update(block.get_body().blobs)

    def __compute_difficulty(self):
        """
        Compute the difficulty for the next block in the chain.
        :return: The difficulty required for the next block to be mined.
        """
        prev = self.chain.blocks[-1]
        if len(self.chain.blocks) == 1:
            return prev.get_difficulty()

        # TODO Add sliding window difficulty recalculation
        delta = time.time() - self.chain.blocks[-1].get_timestamp()
        difficulty = math.log2(Miner.DIFFICULTY_TARGET / delta) * 0.1 + prev.get_difficulty()

        logging.info("New difficulty: %f Delta: %f", difficulty, delta)

        return int(round(max(difficulty, 1)))
