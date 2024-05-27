#include <windows.h>
#include <iostream>
#include <unordered_map>
#include <cassert>

// Block and arena header, block info structures
struct BlockHeader {
    size_t size;
    bool is_free;
    bool is_first;
    bool is_last;
};
struct MemoryArena {
    size_t size;
    void* base;
    MemoryArena* next;
};
struct BlockInfo {
    void* ptr;
    size_t size;
    uint32_t checksum;
};

// Global variables
size_t DEFAULT_ARENA_SIZE;
MemoryArena* ARENA_LIST = nullptr;
std::unordered_map<void*, BlockHeader*> BLOCK_MAP;

// Function declarations
MemoryArena* create_memory_arena(size_t size);
void* allocate_block(MemoryArena* arena, size_t size);
void split_memory_block(BlockHeader* block, size_t size);
void coalesce_memory_blocks();
size_t align_memory_size(size_t size);

void* mem_alloc(size_t size);
void mem_free(void* ptr);
void* mem_realloc(void* ptr, size_t size);
void mem_show();

// Functions
uint32_t calculate_checksum(const void* data, size_t size) {
    const uint8_t* bytes = static_cast<const uint8_t*>(data);
    uint32_t checksum = 0;
    for (size_t i = 0; i < size; ++i) {
        checksum += bytes[i];
    }
    return checksum;
}
void fill_random_data(void* data, size_t size) {
    uint8_t* bytes = static_cast<uint8_t*>(data);
    for (size_t i = 0; i < size; ++i) {
        bytes[i] = rand() % 256;
    }
}
void test(size_t iterations, size_t max_block_size) {
    DEFAULT_ARENA_SIZE = 4096;
    std::vector<BlockInfo> blocks;
    srand(static_cast<unsigned>(time(0)));
    for (size_t i = 0; i < iterations; ++i) {
        std::cout << "Iteration " << i + 1 << "/" << iterations << ": \n";
        int operation = rand() % 3;
        switch (operation) {
        case 0: {
            size_t size = rand() % max_block_size + 1;
            std::cout << "mem_alloc(size=" << size << ")" << std::endl;
            void* ptr = mem_alloc(size);
            if (ptr) {
                fill_random_data(ptr, size);
                uint32_t checksum = calculate_checksum(ptr, size);
                blocks.push_back({ ptr, size, checksum });
            }
            break;
        }
        case 1: {
            if (!blocks.empty()) {
                size_t index = rand() % blocks.size();
                BlockInfo& block = blocks[index];
                uint32_t checksum = calculate_checksum(block.ptr, block.size);
                assert(checksum == block.checksum && "Checksum mismatch before free");
                std::cout << "mem_free(ptr=" << block.ptr << ", size=" << block.size << ")" << std::endl;
                mem_free(block.ptr);
                blocks.erase(blocks.begin() + index);
            }
            break;
        }
        case 2: {
            if (!blocks.empty()) {
                size_t index = rand() % blocks.size();
                BlockInfo& block = blocks[index];
                uint32_t checksum = calculate_checksum(block.ptr, block.size);
                assert(checksum == block.checksum && "Checksum mismatch before realloc");
                size_t new_size = rand() % max_block_size + 1;
                std::cout << "mem_realloc(ptr=" << block.ptr << ", old_size=" << block.size << ", new_size=" << new_size << ")" << std::endl;
                void* new_ptr = mem_realloc(block.ptr, new_size);
                if (new_ptr) {
                    fill_random_data(new_ptr, new_size);
                    block.ptr = new_ptr;
                    block.size = new_size;
                    block.checksum = calculate_checksum(new_ptr, new_size);
                }
            }
            break;
        }
        }
        mem_show();
        std::cout << "<<<<<>>>>>" << std::endl;
    }
    for (const BlockInfo& block : blocks) {
        uint32_t checksum = calculate_checksum(block.ptr, block.size);
        assert(checksum == block.checksum && "Error! Checksums doesn't asserts");
        mem_free(block.ptr);
    }
    std::cout << "Successfully completed" << std::endl;
}
MemoryArena* create_memory_arena(size_t size) {
    size = max(size, DEFAULT_ARENA_SIZE);
    size = align_memory_size(size);
    void* base = VirtualAlloc(nullptr, size, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    if (!base) {
        return nullptr;
    }
    MemoryArena* arena = new MemoryArena{ size, base, ARENA_LIST };
    ARENA_LIST = arena;
    BlockHeader* initial_block = reinterpret_cast<BlockHeader*>(base);
    initial_block->size = size - sizeof(BlockHeader);
    initial_block->is_free = true;
    initial_block->is_first = true;
    initial_block->is_last = true;
    BLOCK_MAP[base] = initial_block;
    return arena;
}
size_t align_memory_size(size_t size) {
    return (size + 3) & ~3;
}
void* allocate_block(MemoryArena* arena, size_t size) {
    size = align_memory_size(size);
    char* base = static_cast<char*>(arena->base);
    while (reinterpret_cast<size_t>(base) < reinterpret_cast<size_t>(arena->base) + arena->size) {
        BlockHeader* block = reinterpret_cast<BlockHeader*>(base);
        if (block->is_free && block->size >= size) {
            split_memory_block(block, size);
            block->is_free = false;
            return base + sizeof(BlockHeader);
        }
        base += sizeof(BlockHeader) + block->size;
    }
    return nullptr;
}
void split_memory_block(BlockHeader* block, size_t size) {
    size = align_memory_size(size);
    if (block->size >= size + sizeof(BlockHeader) + 4) {
        BlockHeader* new_block = reinterpret_cast<BlockHeader*>(
            reinterpret_cast<char*>(block) + sizeof(BlockHeader) + size);
        new_block->size = block->size - size - sizeof(BlockHeader);
        new_block->is_free = true;
        new_block->is_first = false;
        new_block->is_last = block->is_last;
        block->size = size;
        block->is_last = false;
        BLOCK_MAP[new_block] = new_block;
    }
}
void coalesce_memory_blocks() {
    for (auto it = BLOCK_MAP.begin(); it != BLOCK_MAP.end();) {
        BlockHeader* block = it->second;
        if (block->is_free) {
            char* base = reinterpret_cast<char*>(block);
            BlockHeader* next_block = reinterpret_cast<BlockHeader*>(
                base + sizeof(BlockHeader) + block->size);
            if (BLOCK_MAP.find(next_block) != BLOCK_MAP.end() && next_block->is_free) {
                block->size += sizeof(BlockHeader) + next_block->size;
                block->is_last = next_block->is_last;
                BLOCK_MAP.erase(next_block);
                continue;
            }
        }
        ++it;
    }
}
void* mem_alloc(size_t size) {
    if (size == 0) {
        return nullptr;
    }
    size = align_memory_size(size);
    for (MemoryArena* arena = ARENA_LIST; arena; arena = arena->next) {
        if (void* ptr = allocate_block(arena, size)) {
            return ptr;
        }
    }
    MemoryArena* new_arena = create_memory_arena(size + sizeof(BlockHeader));
    if (!new_arena) {
        return nullptr;
    }
    return allocate_block(new_arena, size);
}
void mem_free(void* ptr) {
    if (!ptr) {
        return;
    }
    auto it = BLOCK_MAP.find(static_cast<char*>(ptr) - sizeof(BlockHeader));
    if (it == BLOCK_MAP.end()) {
        return;
    }
    BlockHeader* block = it->second;
    block->is_free = true;
    coalesce_memory_blocks();
}
void* mem_realloc(void* ptr, size_t size) {
    if (!ptr) {
        return mem_alloc(size);
    }
    size = align_memory_size(size);
    auto it = BLOCK_MAP.find(static_cast<char*>(ptr) - sizeof(BlockHeader));
    if (it == BLOCK_MAP.end()) {
        return nullptr;
    }
    BlockHeader* block = it->second;
    if (block->size >= size) {
        split_memory_block(block, size);
        return ptr;
    }
    void* new_ptr = mem_alloc(size);
    if (!new_ptr) {
        return nullptr;
    }
    memcpy(new_ptr, ptr, block->size);
    mem_free(ptr);
    return new_ptr;
}
void mem_show() {
    int arena_counter = 1;
    std::cout << "-------------------- mem_show start --------------------" << std::endl;
    for (MemoryArena* arena = ARENA_LIST; arena; arena = arena->next) {
        std::cout << "Arena #" << arena_counter << " (" << arena->size << " bytes)" << std::endl;
        char* base = static_cast<char*>(arena->base);
        int block_counter = 1;
        while (reinterpret_cast<size_t>(base) < reinterpret_cast<size_t>(arena->base) + arena->size) {
            BlockHeader* block = reinterpret_cast<BlockHeader*>(base);
            std::cout << " #" << block_counter
                << "\t  " << (block->is_free ? "free" : "busy")
                << "\t  " << (block->is_first ? "first" : "-----")
                << "\t  " << (block->is_last ? "last" : "----") 
                << "\t  " << block->size << " bytes" << std::endl;
            base += sizeof(BlockHeader) + block->size;
            block_counter++;
        }
        arena_counter++;
    }
    std::cout << "-------------------- mem_show end   --------------------" << std::endl;
}
int main() {
    DEFAULT_ARENA_SIZE = 4096;

    void* p0 = mem_alloc(1234);
    mem_show();
    void* p1 = mem_alloc(2345);
    mem_show();
    void* p2 = mem_alloc(4321);
    mem_show();
    mem_free(p0);
    mem_show();
    void* p3 = mem_realloc(p1, 1500);
    mem_show();
    void* p4 = mem_realloc(p3, 3000);
    mem_show();

    /*
    test((size_t) 10, (size_t) 4096);
    */

    return 0;
}
