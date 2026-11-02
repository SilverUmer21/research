# Color, light and motion study

## The reference

Reference repository: https://github.com/brunosimon/folio-2025

Inspected source revision: `41046b57eeed8d156d9c3fd7fa259900baef7816`.

The source study covered `MeshDefaultMaterial.js`, `Ligthing.js`, `Fog.js`, `Materials.js`, `DayCycles.js` and `cheapDOF.js`, alongside the author's rendered imagery and actual reference vehicle geometry. The live folio WebGL experience was unavailable in the inspection environment, so this study does not claim a complete live walkthrough.

The useful lesson was the relationship between a simple surface, a deliberate shadow color and a colored light source. A luminous accent feels stronger when its light also changes the adjacent material. That principle guided the series: graphite supports amber, pearl silver supports cyan, and violet supports magenta. The studio stays dark enough to preserve those relationships.

## What changed in this revision

The previous isolated car's booster geometry and animated plume construction were retained. The revision adds three paint/energy palettes and individual front/rear aero treatments. The front, tail and cabin lights remain separate color roles within each theme.

Branching Bezier curves are projected onto clean body and fender surfaces. Each branch has a dark wider bed and a narrower emissive ribbon. The shader reads distance along the branch, so a bright core travels through a turbulent darker stream. The channels therefore pulse along their length instead of changing brightness as a single uniform strip.

Four small flame anchors per car use the same pulse clock. Height, width and opacity vary as the heat arrives, with stronger activity around ignition. They add local blaze without covering the hood's geometry. Colored point-light contributions at six vein junctions connect the emissive channels to the surrounding paint.

The cars also gain sculpted bonnet spines, recessed side intakes, fender louvers, flying buttresses, layered splitters and variant wings. The greenhouse is lower, and the front extension and body width differ by variant. They remain three members of one chassis family.

## Light and compositing

The film uses authored directional lighting, colored shadow response, analytical studio highlights and local energy lights. A mirrored geometry pass supplies the floor reflections. Molten surfaces and jets use animated 3D noise; bloom and localized screen-space heat distortion complete the image. These are real-time-style authored effects, not a fluid or combustion simulation.

## Camera and sound

Each car receives a low front reveal, a tighter elevated hood pass and a rear-quarter ignition shot. Motion eases within each shot. The three palettes cut on the same nine-second rhythm; the final group shot makes their differences directly visible. There are no title cards over the car.

The original score moves through three related tonal centers. Mechanical ticks accompany nozzle deployment, a rising charge precedes ignition at 6, 15 and 24 seconds, and the sustained twin-jet sound carries through each rear shot. The final lineup resolves quietly.

## Visual iteration

Still renders and a moving close-up test were inspected before full delivery. Early channels climbed over panel details, and several new aero faces had reversed shading. Projection was restricted to the clean body surfaces, polygon winding was corrected, and branches were moved away from louvers and the bonnet spine. The final contact sheet is extracted from the encoded video so it represents the delivered picture.
