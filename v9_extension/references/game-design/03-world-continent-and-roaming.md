# World, Continent, and Roaming

Status: **Canonical world principles**, working direction for exact content scale.

## 1. World identity

Eonwild takes place in a **fictional paleo-continent** built to support credible animals, multiple climatic characters, seasonal movement, and future expansion.

The continent is not a historical claim that every included species coexisted. It is a coherent game ecosystem whose animals are individually grounded in evidence and whose real age/geography remain available through the field guide.

## 2. One world, not a chain of zones

The world uses one continuous coordinate space. It may be partitioned for:

- streaming;
- rendering;
- navigation;
- authoring;
- simulation fidelity;
- download packaging.

Those partitions must not become visible level structure.

The player should be able to:

- wander laterally;
- return by a different route;
- backtrack;
- ignore migration pressure;
- investigate quiet valleys and side areas;
- temporarily become lost;
- find alternative water or shelter;
- observe a landmark from several approaches.

## 3. Biomes are environmental blends

The world should not be authored as a fixed sequence such as:

```text
forest → corridor → floodplain → basin → refuge
```

Those environmental characters may exist, but their shapes emerge from overlapping fields:

- elevation;
- moisture;
- temperature;
- canopy;
- substrate;
- water proximity and depth;
- exposure;
- shelter;
- seasonal biomass;
- fire/flood history;
- traversal cost.

This permits:

- forest descending into sheltered valleys;
- dry rain-shadow areas beside elevated terrain;
- riparian corridors crossing several regions;
- wetlands opening into exposed floodplains;
- mixed ecotones rather than hard biome borders.

## 4. Macro environmental characters

Long-term world design may include combinations of:

### Upland forest and ridge country

- cooler temperatures;
- cover and shelter;
- limited sight lines;
- elevated observation routes;
- seasonal food decline;
- narrow but natural passes.

### Floodplain and braided river

- high biomass;
- changing channels;
- exposed mud and sandbars;
- herd concentration;
- dangerous crossings;
- flood and drought variability.

### Fern woodland and wetlands

- dense cover;
- high ambient life;
- reduced visibility;
- soft ground and water edges;
- predator ambush opportunities.

### Dry basin and open country

- scarce cover;
- long sight lines;
- sparse water;
- mineral or feeding sites;
- heat and travel pressure.

### Seasonal refuges

- temporary suitability rather than permanent safe zones;
- water or food concentration;
- high competition;
- predator pressure;
- social gathering.

These are a palette, not a mandatory traversal order.

## 5. Roaming topology

The world should offer several route types:

- **direct and exposed** — shorter, visible, potentially dangerous;
- **covered** — longer, lower visibility, constrained movement;
- **elevated** — better information, higher traversal or weather cost;
- **water-following** — reliable orientation, greater predator/herd activity;
- **exploratory** — uncertain reward, landmark or route discovery;
- **seasonal** — available only under certain water, flood, or temperature states.

Major areas should connect through loops. Natural chokepoints are valuable when they are a minority of travel and arise from geography rather than loading needs.

## 6. Scale and density

Logical world size and active cost are separate.

The existing technical direction uses a 12 × 12 demonstration grid of 256-metre cells, producing a logical bounding space of roughly 3.07 × 3.07 km. That is a benchmark envelope, not a permanent limit or a promise that every cell is equally authored.

The product should prioritize:

- enough area for route choice and temporary disorientation;
- density of meaningful signs and ecological information;
- memorable landmarks;
- quiet wilderness that feels intentional;
- high-value vistas and event locations;
- outward expansion without coordinate or save rewrites.

Do not increase square kilometres merely to market a large number.

## 7. Content-density tiers

### Tier A — memorable vistas and ecological stages

Examples:

- herd river crossing;
- valley overlook;
- drying waterhole;
- storm front over open basin;
- refuge seen from a ridge;
- predator concentration around a bottleneck.

These receive the highest composition and rendering investment.

### Tier B — normal roaming landscape

The majority of play:

- route choices;
- feeding and cover;
- tracks and signs;
- modest encounters;
- navigation by terrain and sound.

### Tier C — quiet transition and wilderness

Lower density, but still intentional:

- supports anticipation;
- creates contrast;
- allows recovery;
- communicates scale;
- avoids constant theme-park stimulation.

## 8. Landmarks and orientation

Players should navigate through:

- river systems;
- ridges;
- mountain silhouettes;
- distinctive tree groups;
- rock formations;
- wetlands;
- mineral deposits;
- distant herd movement;
- sky/weather direction;
- audio landmarks.

A restrained map or memory aid may exist, but the world should remain learnable from observation.

## 9. Dynamic geography

Environmental state may temporarily change traversal:

- flood removes or creates crossings;
- drought exposes mudflats and channels;
- fire or smoke makes an area dangerous;
- storms reduce visibility;
- cold or heat changes shelter value;
- vegetation density changes feeding routes;
- carcasses and herds create temporary hotspots.

Dynamic events may close a path for ecological reasons. They must not become permanent excuses for a linear structure.

## 10. Distant world illusion

The world can feel much larger than the fully active area through:

- horizon meshes;
- distant mountains;
- atmospheric perspective;
- off-map herd silhouettes;
- dust;
- weather fronts;
- distant calls;
- rivers continuing beyond current authored terrain;
- far ecology records.

The renderer should spend detail where the player can perceive it.

## 11. World expansion model

The continent expands through:

- new adjacent cells;
- new environmental-field presets;
- new shared vegetation and terrain packs;
- new water systems;
- new ecology tables;
- new seasonal events;
- horizon and landmark updates.

Expansion should not require:

- renumbering existing cells;
- moving the world origin;
- rewriting saves;
- changing core biome enums;
- replacing the renderer;
- introducing a chapter sequence.

## 12. World acceptance questions

A world slice is aligned when:

- players choose more than one route;
- most space exists outside the shortest objective path;
- backtracking works;
- landmarks orient without over-explaining;
- quiet areas still contain signs of life;
- migration influences but does not command movement;
- cells are invisible to the player;
- players describe a place, not a level layout.
