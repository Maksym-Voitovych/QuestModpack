# Description
Block Stats specify the enchanting stats that a block provides to the enchanting table, replacing the code-based stat lookup for the selected blocks.  

Block Stats are loaded from the `data/<namespace>/enchanting_stats/` datapack folder.  

A single file may select blocks in three ways, which are additive: all blocks from the `blocks` list, the single `block`, and every block in the `tag` receive the given stats.

# Dependencies
This object references the following objects:
1. [Stats](./Stats.md)

# Schema
```js
{
    "blocks": [        // [Optional] || A list of block registry names receiving the stats. Default value = empty list.
        "string"
    ],
    "block": "string", // [Optional] || A single block registry name receiving the stats.
    "tag": "string",   // [Optional] || The registry name of a block tag. All blocks in the tag receive the stats.
    "stats": Stats     // [Mandatory] || The enchanting stats provided by the selected blocks.
}
```

Note: At least one of the three selectors should be provided, or the file will have no effect.

# Examples
The Hellshelf, which raises the eterna cap to 45 and provides 3 eterna and 3 quanta.

```json
{
    "block": "apothic_enchanting:hellshelf",
    "stats": {
        "maxEterna": 45,
        "eterna": 3,
        "quanta": 3,
        "arcana": 0
    }
}
```

Basic skulls, which provide 5 quanta each, selected via a block tag.

```json
{
    "tag": "apothic_enchanting:basic_skulls",
    "stats": {
        "maxEterna": 0,
        "eterna": 0,
        "quanta": 5,
        "arcana": 0,
        "clues": 0
    }
}
```

Wither skulls, which provide 10 quanta, selected via a block list.

```json
{
    "blocks": [
        "minecraft:wither_skeleton_skull",
        "minecraft:wither_skeleton_wall_skull"
    ],
    "stats": {
        "maxEterna": 0,
        "eterna": 0,
        "quanta": 10,
        "arcana": 0,
        "clues": 0
    }
}
```
