from collections import OrderedDict
from utils import Level
import math


class CacheLevel(Level):
    def __init__(self, size, block_size, associativity, eviction_policy, write_policy, level_name, higher_level=None,
                 lower_level=None):
        super().__init__(level_name, higher_level, lower_level)
        self.size = size
        self.block_size = block_size
        self.associativity = associativity
        self.eviction_policy = eviction_policy  # FIFO | LRU | MRU
        self.write_policy = write_policy  # always WB for this assignment

        self.cache = {}
        # holds an ordered dict for each set

        # define other structures / metadata here (hint, check the imports)
        self.num_sets = int(size / (block_size * associativity))  # same as other formula(algebraically) just different

        # define an ordereddict for each set
        for i in range(self.num_sets):
            self.cache[i] = OrderedDict()  # dict for each set, holds {tag, isdirty?}
        self.num_offset_bits = int(math.log2(self.block_size))
        self.num_index_bits = int(math.log2(self.num_sets))

            
        

    def _calculate_index(self, address):
        index = (address >> self.num_offset_bits) & ((1 << self.num_index_bits) - 1)

        return index

    def _calculate_tag(self, address):
        tag = address >> (self.num_offset_bits + self.num_index_bits)

        return tag

    def _calculate_block_address(self, address):
        offset = (1 << self.num_offset_bits) - 1
        block_addr = address & ~offset

        return block_addr

    def _calculate_block_address_from_tag_index(self, tag, cache_index):
        return (tag << (self.num_index_bits + self.num_offset_bits)) | (cache_index << self.num_offset_bits)

    def is_dirty(self, block_address):

        index = (block_address >> self.num_offset_bits) & ((1 << self.num_index_bits) - 1)
        tag = block_address >> (self.num_index_bits + self.num_offset_bits)

        working_set_dictionary = self.cache.get(index)

        if working_set_dictionary is None:
            return False
        return tag in working_set_dictionary and working_set_dictionary[tag]["dirty"]

    def access(self, operation, address):
        index = self._calculate_index(address)
        tag = self._calculate_tag(address)
        block_address = self._calculate_block_address(address)
        working_set_dictionary = self.cache.get(index)

        if operation == "B":
            if tag in working_set_dictionary:
                #dirty
                self.report_hit("W", address)
                working_set_dictionary[tag]["dirty"] = True
            else:
                # write miss
                self.report_miss("W", address)
                if len(working_set_dictionary) >= self.associativity:
                    self.evict(index)
                working_set_dictionary[tag] = {"dirty": True, "addr": self._calculate_block_address(address)}  # another dictionary
            return

        if tag in working_set_dictionary:  # hit
            self.report_hit(operation, address)
            if operation == "W":
                working_set_dictionary[tag]["dirty"] = True
            if self.eviction_policy == "LRU":
                working_set_dictionary.move_to_end(tag)
            if self.eviction_policy == "MRU":
                working_set_dictionary.move_to_end(tag, last=False)
        else:  # miss
            self.report_miss(operation, address)
            if len(working_set_dictionary) >= self.associativity:
                self.evict(index)
            if operation == "W":
                dirty = True
            else:
                dirty = False
            working_set_dictionary[tag] = {"dirty": dirty, "addr": self._calculate_block_address(address)}   # another dictionary
            self.higher_level.access("R", address)
            if self.higher_level.is_dirty(block_address):
                working_set_dictionary[tag]["dirty"] = True
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
        if self.eviction_policy == "FIFO" or self.eviction_policy == "LRU":
            victim_block_tag = list(working_set_dictionary.keys())[0]  # get the first one
        else:  # MRU
            # get the last item in the set
            victim_block_tag = list(working_set_dictionary.keys())[0]  # get the last one

        # call "B" operations to higher levels here when evicting a dirty block in invalidate
        # invalidate the block
        evicted_block = self._calculate_block_address_from_tag_index(victim_block_tag, cache_index)
        self.invalidate(evicted_block)

    def invalidate(self, block_address):

        index = (block_address >> self.num_offset_bits) & ((1 << self.num_index_bits) - 1)
        tag = block_address >> (self.num_index_bits + self.num_offset_bits)
        if self.lower_level:
            self.lower_level.invalidate(block_address)

        working_set_dict = self.cache.get(index)

        if tag in working_set_dict:
            block = working_set_dict[tag]
            evicted_block_address = block["addr"]
            if block["dirty"]:
                self.report_writeback(evicted_block_address)
                self.higher_level.access("B", evicted_block_address)
            working_set_dict.pop(tag)
            self.report_eviction(evicted_block_address)


