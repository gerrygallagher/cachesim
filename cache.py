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
        self.cache = {}
        # holds an ordered dict for each set

        # define other structures / metadata here (hint, check the imports)
        self.num_sets = int(size/(block_size*associativity))

        # define an ordereddict for each set
        num_index_bits = int(math.log2(self.num_sets))
        for i in range(self.num_sets):
            b_index = format(i, 'b')
            b_index = b_index.zfill(num_index_bits)  # pad the index with 0's
            self.cache[b_index] = OrderedDict()  # dict for each set, holds {tag, isdirty?}


        # todo define metadata structures (tags, dirty bits, etc...)
        # todo anything else you may want...

    def _calculate_index(self, address):
        # address is an int
        b = format(address, '032b')  # to add in leading zeros

        num_block_offset_bits = int(math.log2(self.block_size))
        num_index_bits = int(math.log2((self.size/self.block_size)/self.associativity))
        index_string = b[32-num_block_offset_bits-num_index_bits: 32-num_block_offset_bits]

        return index_string

    def _calculate_tag(self, address):
        # address is an int
        b = format(address, '032b')  # to add in leading zeros

        num_block_offset_bits = int(math.log2(self.block_size))
        num_index_bits = int(math.log2((self.size / self.block_size) / self.associativity))
        tag_string = b[0: 32-(num_block_offset_bits + num_index_bits)]

        return tag_string

    def _calculate_block_address(self, address):
        # address is an int
        b = format(address, '032b')  # to add in leading zeros

        num_block_offset_bits = int(math.log2(self.block_size))
        block_addr_string = b[0: 32-num_block_offset_bits]

        return block_addr_string

    def _calculate_block_address_from_tag_index(self, tag, cache_index):
        return tag + cache_index

    def is_dirty(self, block_address):
        num_index_bits = int(math.log2(self.num_sets))
        num_tag_bits = len(block_address) - num_index_bits

        tag = block_address[0: num_tag_bits]
        index = block_address[num_tag_bits: num_tag_bits + num_index_bits]

        working_set_dictionary = self.cache.get(index)
        if working_set_dictionary is None:
            return False
        else:
            return working_set_dictionary.get(tag, False)


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
        index = self._calculate_index(address)
        tag = self._calculate_tag(address)
        block_address = self._calculate_block_address(address)

        working_set_dictionary = self.cache.get(index)

        if tag in working_set_dictionary: # hit
            self.report_hit(operation, address)
            if operation == "W":
                working_set_dictionary[tag] = True
            if self.eviction_policy == "LRU":
                working_set_dictionary.move_to_end(tag)
            if self.eviction_policy == "MRU":
                working_set_dictionary.move_to_end(tag, last=False)
        else: # miss
            #report it
            self.report_miss(operation, address)
            #evict if cache is full
            if len(working_set_dictionary) >= self.associativity:
                self.evict(index)
            #insert into cache
            if operation == "W" or operation == "B":
                dirty = True
            else:
                dirty = False
            working_set_dictionary[tag] = dirty
            if operation != "B":
                self.higher_level.access("R", address)
            if self.higher_level.is_dirty(block_address):
                working_set_dictionary[tag] = True
            if self.eviction_policy == "LRU":
                working_set_dictionary.move_to_end(tag, last=True)
            elif self.eviction_policy == "MRU":
                working_set_dictionary.move_to_end(tag, last=False)


        return

    def evict(self, cache_index):
        """
        Select a victim block in the given way provided this level's eviction policy. Calculate its block address and
        then invalidate said block.
        """
        working_set_dictionary = self.cache.get(cache_index)
        # select a victim block in the set provided the eviction policy (FIFO | LRU | MRU)
        victim = None
        if self.eviction_policy == "LRU" or self.eviction_policy == "FIFO":
            victim = working_set_dictionary.popitem(last=False)  # evict first item in set dict
        elif self.eviction_policy == "MRU":
            victim = working_set_dictionary.popitem(last=True)  # evict last item in set dict
        victim_block_tag = victim[0]


        # call "B" operations to higher levels here when evicting a dirty block
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
        num_index_bits = int(math.log2(self.num_sets))
        num_tag_bits = len(block_address) - num_index_bits
        tag = block_address[0: num_tag_bits]
        index = block_address[num_tag_bits: num_tag_bits + num_index_bits]
        if self.lower_level:
            self.lower_level.invalidate(block_address)

        working_set_dict = self.cache[index]
        if tag in working_set_dict:
            # if its dirty, writeback before you evict
            if working_set_dict[tag]:  # dirty
                int_block_address = int(block_address, 2)
                self.report_writeback(int_block_address)
                self.higher_level.access("B", int_block_address)

            # evict
            working_set_dict.pop(tag)

            # Report the eviction
            self.report_eviction(int(block_address, 2))
