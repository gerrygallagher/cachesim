from collections import deque, OrderedDict
from utils import Level
import math


class CacheLevel(Level):
    def __init__(self, size, block_size, associativity, eviction_policy, write_policy, level_name, higher_level=None, lower_level=None):
        super().__init__(level_name, higher_level, lower_level)
        self.size = size
        self.block_size = block_size
        self.associativity = associativity
        self.eviction_policy = eviction_policy  # FIFO | LRU | MRU
        self.write_policy = write_policy  # always WB for this assignment

        # define other structures / metadata here (hint, check the imports)
        # todo define number of sets
        # todo define metadata structures (tags, dirty bits, etc...)
        # todo anything else you may want...

    def _calculate_index(self, address):
        d = int(address, 16)  # hex to decimal
        b = bin(d)  # decimal to binary
        b = b[2:]  # remove "0b" prefix
        # note b is a string
        num_block_offset_bits = int(math.log2(self.block_size))
        num_index_bits = int(math.log2((self.size/self.block_size)/self.associativity))
        index_string = b[32-num_block_offset_bits-num_index_bits : 32-num_block_offset_bits]
        '''
        should return be a string, 
        is addr always 32, 
        needs tested, 
        returning right thing?
        '''
        return index_string

    def _calculate_tag(self, address):
        d = int(address, 16)  # hex to decimal
        b = bin(d)  # decimal to binary
        b = b[2:]  # remove "0b" prefix
        # note b is a string
        num_block_offset_bits = int(math.log2(self.block_size))
        num_index_bits = int(math.log2((self.size / self.block_size) / self.associativity))
        tag_string = b[0:32-(num_block_offset_bits+num_index_bits)]

        return tag_string

    def _calculate_block_address(self, address):
        return 0  # todo

    def _calculate_block_address_from_tag_index(self, tag, cache_index):
        return 0  # todo

    def is_dirty(self, block_address):
        return True|False  # todo

    def access(self, operation, address):
        """
        Perform a memory access to the given address. Operations are R for reads, W for writes, and B for block
        / writeback updates. B-type operations do not modify the eviction policy meta-details. To perform an access,
        check to see if the address is in this level. If it is a hit, then report the hit and update the eviction policy
        (if required). If the operation was a store make sure to set the block's dirty bits. If the access was a miss,
        report the miss and check if this set needs to evict a block. If it does, evict the target block. Now that the
        target is evicted allocate space for the next block, update the dirty bits (if required) and perform a read
        on the higher levels to propagate the block. Finally, if the block fetched from the higher block is dirty, set
        our block to also be dirty.
        """
        pass  # todo

    def evict(self, cache_index):
        """
        Select a victim block in the given way provided this level's eviction policy. Calculate its block address and
        then invalidate said block.
        """
        # select a victim block in the set provided the eviction policy (FIFO | LRU | MRU)
        victim_block_tag = None  # todo

        # invalidate the block
        evicted_block = self._calculate_block_address_from_tag_index(victim_block_tag, cache_index)
        self.invalidate(evicted_block)

    def invalidate(self, block_address):
        """
        Invalidate the block given by block address. If the block is not in this level, then we know it is not in
        lower levels. If it is in this level, then we need to invalidate lower levels first since they may be dirty.
        Once all lower levels have been invalidated, we need to check if our level is dirty, and if it is, perform a
        writeback and report that. Finally, once all lower levels have been invalidated we can remove the block from
        our level and report the eviction.
        """
        pass  # todo
