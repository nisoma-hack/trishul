# Trishul

Trishul is a small game-backend scripting language designed for writing game logic in Romanized Hindi. It is meant to help creators define entities, components, state changes, actions, and event-driven gameplay systems in a readable and expressive way.

## What Trishul is

Trishul is a lightweight prototype language built for:
- entity creation
- component attachment
- game state updates
- action and event triggers
- simple conditionals and loops
- exporting game state as JSON

It is useful for scripting logic in game backends, simple game systems, NPC behaviors, combat logic, inventory logic, and simulation-style game events.

## Why Trishul

The goal of Trishul is to make game scripting feel natural to Hindi-speaking developers while still remaining simple and approachable. The language uses Roman script for typing, but its design is centered around gameplay concepts rather than translated English syntax.

## Supported concepts

- Entities
- Components
- State mutation
- Actions
- Conditionals
- Loops
- Function-like reusable logic
- JSON export of game state

## Example program

```trishul
entity banao "hero" { health: 100, mana: 50, level: 1 }

component add_karo hero: Position { x: 0, y: 0 }
component add_karo hero: Inventory { slots: 10 }

state_badlo hero { health: 90 }

action trigger_karo hero: attack { target: "enemy_1", damage: 15 }

agar hero.health < 50 to {
    likho "Low health!"
} warna {
    likho "Fight ready!"
}
```

## How to run it

From the repository root:

```bash
python trishul.py --help
```

To run a script:

```bash
python trishul.py run my_game.tri
```

To save the resulting game state as JSON:

```bash
python trishul.py run my_game.tri -o game_state.json
```

## Project structure

```text
trishul/
├── trishul.py
├── README.md
├── examples/
│   ├── hello.tri
│   ├── rpg_game.tri
│   └── npc_behavior.tri
└── scripts/
    └── your_game_logic.tri
```

## Writing your own script

Create a new file with `.tri` extension:

```bash
nano my_game.tri
```

Example:

```trishul
entity banao "player" { health: 100, mana: 50, level: 1 }

component add_karo player: Position { x: 10, y: 20 }
component add_karo player: Inventory { slots: 8 }

state_badlo player { health: 75 }

agar player.health < 80 to {
    likho "Player is low on health"
} warna {
    likho "Player is in good condition"
}
```

Run it:

```bash
python trishul.py run my_game.tri
```

## Common commands

### Create an entity

```trishul
entity banao "enemy" { health: 30, level: 1 }
```

### Add a component

```trishul
component add_karo enemy: Combat { attack: 8, defense: 3 }
```

### Update state

```trishul
state_badlo enemy { health: 20 }
```

### Trigger an action

```trishul
action trigger_karo enemy: attack { target: "hero", damage: 10 }
```

### Conditional logic

```trishul
agar health < 50 to {
    likho "Need healing"
} warna {
    likho "Ready for battle"
}
```

### Loop logic

```trishul
jabtak i < 10 to {
    likho i
    i ko i + 1 rakho
}
```

## Example game backend flow

Here is a full simple example:

```trishul
entity banao "hero" { health: 100, mana: 50, level: 1 }
entity banao "goblin" { health: 30, level: 1 }

component add_karo hero: Position { x: 0, y: 0 }
component add_karo goblin: Position { x: 5, y: 5 }

attack_damage ko 15 rakho

action trigger_karo hero: attack { target: "goblin", damage: attack_damage }

state_badlo goblin { health: 15 }

agar goblin.health <= 0 to {
    likho "Goblin defeated!"
} warna {
    likho "Goblin is still alive."
}
```

## JSON export

This language can export the current game state and events as JSON, which is useful for:
- game backend testing
- saving runtime state
- debugging gameplay logic
- serializing simulations

Example:

```bash
python trishul.py run my_game.tri -o game_state.json
```

The exported file will contain:
- entities
- component data
- state values
- event logs

## Limitations

This project is a lightweight prototype. It is not yet a complete commercial game engine language. It is best used for:
- learning language design
- building simple game logic scripts
- prototyping backend game systems
- experimenting with Hindi-style custom syntax

## Future ideas

Possible future improvements include:
- stronger parser rules
- better function semantics
- NPC AI behaviors
- quest and inventory systems
- support for more game engine concepts
- real compiler output to Python or JavaScript

## Repo usage summary

Use this command flow often:

```bash
python trishul.py --help
python trishul.py run examples/hello.tri
python trishul.py run my_game.tri -o game_state.json
```

## Contribution

If you want to improve Trishul, you can:
- add more built-in game commands
- design a richer grammar
- add new scripting features
- create more example game loops
- improve JSON export and state simulation

## License

This repository is intended for experimentation and prototype development.

---

This README is meant to help new users understand the purpose of Trishul, how to run scripts, and how to structure game logic using entities, components, state, and actions.
