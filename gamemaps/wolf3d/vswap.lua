-- Reads data from VSVSWAP.WL6 - Wolfenstein 3D shareware.
--
-- Special thanks to Bruce A. Lewis for documenting the file format for the
-- VSVSWAP file at: https://devinsmith.net/backups/bruce/wolf3d.html
--
-- Copyright 2021, Sean Donnellan
-- Licence: MIT Licence
local graphicsFileName = "VSWAP.WL6"

vswap = {}

---
--- Open the file and return the header information and the opened file.
---@return table
function vswap.open()
    local file = assert(io.open(graphicsFileName, "rb"))

    -- The format of the file is as so:
    -- struct Header
    -- {
    --     uint16_t ChunkCount;
    --     uint16_t SpriteStart;
    --     uint16_t SoundStart;
    --     uint32_t ChunkOffsets[ChunkCount];
    --     uint16_t ChunkLengths[ChunkCount];
    -- };

    local chunk_count = string.unpack("<I2", file:read(2))
    local sprint_start = string.unpack("<I2", file:read(2))
    local sound_start = string.unpack("<I2", file:read(2))

    local chunk_offsets = {}
    for i = 0, chunk_count
    do
        chunk_offsets[i] = string.unpack("<I4", file:read(4))
    end

    local chunk_lengths = {}
    for i = 0, chunk_count
    do
        chunk_lengths[i] = string.unpack("<I2", file:read(2))
    end

    local header = {}
    header["file"] = file
    header["chunk_count"] = chunk_count
    header["sprint_start"] = sprint_start
    header["sound_start"] = sound_start
    header["chunk_offsets"] = chunk_offsets
    header["chunk_lengths"] = chunk_lengths
    header["size"] = 6 + 4 * chunk_count + 2 * chunk_count
    return header
end

---
--- Read the walls out of the VSWAP file. Returns an array of 64 by 64 wall
--- tiles.
---@return table
function vswap.walls()
    local header = vswap.open()
    local file = header["file"]

    -- The wall data is 64-by-64 bytes. The value is an index into a colour
    -- palette.

    -- The walls are in the chunks from the first chunk till sprint_start

    local wall_count = header["sprint_start"]

    local walls = {}
    for i = 0, wall_count - 1
    do
        local offset = header["chunk_offsets"][i]
        local length = header["chunk_lengths"][i]

        -- length should be 64 * 64.

        file:seek("set", offset)
        local wall = file:read(length)
        walls[i] = wall
    end

    file:close()

    return walls
end
