# What is EDA in IC Design?

> **Note:** This document was created with the help of **Claude** (an AI assistant by Anthropic). It is based on the lecture slides *ECE 5745 Complex Digital ASIC Design – Topic 13: Physical Design Automation Algorithms* (Christopher Batten, Cornell University). Please verify technical details against the original source material.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Where Physical Design Fits in the CAD Flow](#2-where-physical-design-fits-in-the-cad-flow)
3. [Placement](#3-placement)
4. [Global Routing](#4-global-routing)
5. [Detailed Routing](#5-detailed-routing)
6. [Summary](#6-summary)
7. [References](#7-references)
8. [Learning](#8-references)

---

## 1. Overview

**EDA (Electronic Design Automation)**, also called **CAD (Computer-Aided Design)** for VLSI, is the family of software tools and algorithms used to design integrated circuits (ICs). A modern chip contains millions to billions of transistors, so it is impossible to design by hand. EDA tools automate the process of turning a high-level hardware description into a physical layout that can be manufactured.

The source slides focus on the **physical design** portion of the EDA flow, namely:

- **Placement** – deciding where each cell goes
- **Global routing** – coarse planning of wire paths
- **Detailed routing** – exact assignment of wires to tracks and layers

---

## 2. Where Physical Design Fits in the CAD Flow

The slides present the CAD flow ("Part 3: CAD Algorithms") as a sequence of automated steps:

| Stage | Description | Example from slides |
|---|---|---|
| **RTL to Logic Synthesis** | Converts RTL (registers, datapath, control FSM) into logic equations | `x = a'bc + a'bc'`, `y = b'c' + ab' + ac` |
| **Technology-Independent Synthesis** | Optimizes the logic equations without regard to a target cell library | `x = a'b`, `y = b'c' + ac` |
| **Technology-Dependent Synthesis** | Maps the optimized logic onto real standard cells (gates) | Network of AND/OR gates |
| **Placement** | Assigns each cell a location in the standard-cell rows | Cells arranged in rows |
| **Global Routing** | Plans approximate routes for each net through routing regions | Coarse wires between rows |
| **Detailed Routing** | Assigns wires to exact tracks, layers and vias | Horizontal/vertical segments + vias |

```
RTL ─► Logic Synthesis ─► Tech-Independent ─► Tech-Dependent ─► Placement ─► Global Routing ─► Detailed Routing
```

---

## 3. Placement

### 3.1 What is placement?

Placement determines the physical location of each cell (gate) in the layout. The slides show:

- **Linear placement** – cells in a single row
- **2D placement** – cells arranged in multiple rows
- **Placement and routing with standard cells** – rows of cells with power (VDD) and ground (GND) rails and I/O pads

### 3.2 Global vs. detailed placement

- **Global placement** – spreads cells roughly across the chip into regions.
- **Detailed placement** – legalizes the result by placing cells exactly into rows without overlap.

### 3.3 Placement objective functions

A placement is judged by several goals:

- **Total wirelength**
- **Number of cut nets**
- **Wire congestion**
- **Signal delay**

### 3.4 Good vs. bad placement

| Bad placement | Good placement |
|---|---|
| Routing congestion | Less circuit area (cost) and wiring |
| Larger area and more wiring | Shorter wires → less capacitance |
| Longer wires → more capacitance | Shorter delay |
| Longer delay | Less dynamic power |
| Higher dynamic power | |

### 3.5 Partitioning

Partitioning divides a circuit into blocks so that the number of connections crossing between blocks (the **cut**) is minimized.

Key terminology:

- **Block (partition)** – a group of cells
- **Cells** – the nodes of the graph
- **Cut set** – the collection of edges that cross the cut line

Example from the slides: two different cuts of the same 8-gate circuit gave **four** external connections (cut *c*ₐ) versus **two** (cut *c*ᵦ), showing that the choice of cut matters.

### 3.6 Kernighan–Lin (KL) algorithm

- **Given:** a graph with 2*n* nodes of equal weight
- **Goal:** split it into two disjoint subsets *A* and *B*, with |*A*| = |*B*| = *n*, and minimum cut cost

**Cost of moving a node *v*:**

```
D(v) = |Ec(v)| – |Enc(v)|
```

- `Ec(v)` = edges incident to *v* that are cut by the cut line
- `Enc(v)` = edges incident to *v* that are not cut
- High *D* (> 0) means the node should move; low *D* (< 0) means it should stay.

**Gain of swapping nodes *a* and *b*:**

```
Δg = D(a) + D(b) – 2·c(a,b)
```

where `c(a,b)` is the edge weight between *a* and *b* (0 if no edge). The larger Δg, the more the cut cost is reduced.

**Example from the slides (n = 4):**

| Step | Swap | Δg | Cumulative gain *G* |
|---|---|---|---|
| 1 | (3, 5) | 3 | 3 |
| 2 | (4, 6) | 5 | 8 |
| 3 | (1, 7) | –6 | 2 |
| 4 | (2, 8) | –2 | 0 |

The maximum gain is *G*ₘ = 8 at *m* = 2, so only the first two swaps are executed. Since *G*ₘ > 0, more passes are run until *G*ₘ ≤ 0.

### 3.7 Min-cut placement

1. Use a partitioning algorithm (such as KL) to divide the netlist into two regions.
2. Recursively divide each region into smaller regions (e.g., four regions).
3. Each cut heuristically minimizes the number of cut nets.

The slides demonstrate a 4 × 2 placement of a 6-gate circuit by alternating vertical and horizontal cut lines.

### 3.8 Analytical (quadratic) placement

The objective is the sum of weighted **squared Euclidean distances**:

```
L(P) = 1/2 · Σ c_ij · ( (x_i – x_j)² + (y_i – y_j)² )     (i, j = 1 … n)
```

- *n* = total number of cells; `c(i,j)` = connection cost between cells *i* and *j*
- Handles only two-point connections
- Minimized by setting the derivative to zero, which reduces to **solving a system of linear equations**

**Limitation:** minimizing this objective tends to **clump cells together** in the center of the chip. The slides show how repeated **partitioning is used to pull cells apart** over several iterations.

---

## 4. Global Routing

### 4.1 General routing problem

**Inputs:**

- A **netlist**, e.g. `N1 = {C4, D6, B3}`, `N2 = {D4, B4, C1, A4}`, ...
- **Technology information** (design rules)

**Output:** physical wires connecting all pins of each net.

### 4.2 Routing algorithm taxonomy

- **Multi-stage routing of signal nets**
  - **Global routing** – coarse-grain assignment of routes to routing regions
  - **Detailed routing** – fine-grain assignment of routes to routing tracks
  - **Timing-driven routing** – net topology optimization and resource allocation to critical nets
- **Large single-net routing** – power (VDD) and ground (GND) routing
- **Geometric techniques** – non-Manhattan and clock routing

### 4.3 Terminology

| Term | Meaning |
|---|---|
| **Channel** | Rectangular routing region with pins on two opposite sides |
| **Capacity** | Number of available routing tracks or columns |
| **Switchbox** | Intersection of horizontal and vertical channels (two-layer macro-cell layout) |
| **Feedthrough cells** | Cells used to route across multiple cell rows when metal layers are limited |

For variable-die standard cell designs:

```
Total height = Σ (cell row heights) + Σ (all channel heights)
```

### 4.4 Wirelength vs. feedthroughs

For one net there can be competing Steiner tree solutions: one with **minimal wirelength**, another with the **fewest feedthrough cells**.

### 4.5 Rectilinear routing flow

1. Define routing regions (grid cells)
2. Assign pins to grid cells
3. Build a **Rectilinear Steiner Minimum Tree (RSMT)**
4. Assign routing regions and feedthrough cells

### 4.6 Heuristic sequential Steiner tree algorithm

1. Find the closest (rectilinear distance) pin pair and construct their **minimum bounding box (MBB)**.
2. Find the closest point pair (*p*<sub>MBB</sub>, *p*<sub>C</sub>) between any point on the MBB and a pin from the set still to consider.
3. Construct the MBB of *p*<sub>MBB</sub> and *p*<sub>C</sub>.
4. Add the **L-shape** that *p*<sub>MBB</sub> lies on to tree *T* (deleting the other L-shape). If *p*<sub>MBB</sub> is a pin, add either L-shape.
5. Repeat from step 2 until no pins remain.

The slides walk through a 7-pin example, producing a final tree with Steiner points.

---

## 5. Detailed Routing

Detailed routing assigns each net's segments to exact tracks within **channels** and **switchboxes**, using horizontal and vertical segments connected by **vias**.

### 5.1 Horizontal constraint graph (HCG)

- Let **S(col)** be the set of nets passing through column *col*. It includes nets that either (1) have a pin in that column, or (2) have pins to both the left and right of it.
- Horizontal segments cannot overlap, so each net in S(col) needs a different track.
- Therefore the **lower bound on channel height** = the maximum cardinality of any S(col).

Example: `S(c) = {A, B, C, D, E}` has 5 nets, so at least 5 tracks are required.

Only columns that are **not subsets of any other column** need to be considered (in the example: S(c), S(f), S(g), S(i)).

### 5.2 Vertical constraint graph (VCG)

A directed graph that captures the **top/bottom pin ordering** in each column. If net *X* has a pin on the top and net *Y* has a pin on the bottom of the same column, then *X* must be routed **above** *Y* (edge *X → Y*).

### 5.3 Left-edge algorithm

1. Generate the VCG and the zone representation.
2. Consider the next track (`curr_track`).
3. Scan unassigned nets left to right. If `curr_net` has **no parents** in the VCG and **does not conflict** with nets already on `curr_track`, assign it to that track.
4. Delete the placed nets from the VCG and zone representation.
5. Repeat until all nets are assigned.

**Worked example from the slides (nets A–J):**

| Track | Nets assigned |
|---|---|
| 1 | A, J |
| 2 | D |
| 3 | E, G |
| 4 | C, F, I |
| 5 | B, H |

Result: all 10 nets are routed in **5 tracks**.

---

## 6. Summary

- **EDA** automates the translation of a hardware design into a manufacturable layout.
- After synthesis, **physical design** has three major steps: **placement → global routing → detailed routing**.
- **Placement** uses partitioning (e.g., Kernighan–Lin, min-cut) and analytical methods (quadratic placement) to minimize wirelength, congestion and delay.
- **Global routing** plans coarse routes using concepts like channels, capacity, switchboxes, feedthroughs and Steiner trees.
- **Detailed routing** assigns exact tracks using constraint graphs (HCG/VCG) and algorithms like **left-edge**.
- Good physical design leads to **smaller area, shorter wires, lower delay and lower dynamic power**.

---

## 7. References

- C. Batten, *ECE 5745 Complex Digital ASIC Design, Topic 13: Physical Design Automation Algorithms*, Cornell University. <http://www.csl.cornell.edu/courses/ece5745>
- [Kahng'11] A.B. Kahng, J. Lienig, I.L. Markov, and J. Hu, *VLSI Physical Design: From Graph Partitioning to Timing Closure*, Springer, 2011 (companion slides).
- [Devadas'06] S. Devadas, "VLSI CAD Flow: Logic Synthesis, Placement, and Routing," MIT 6.375 Complex Digital Systems guest lecture slides, 2006.

---
## 8. Learning
- Conversation with Gemini AI: https://share.gemini.google/CU6v7eP8rrwf
---

*This README was generated using Claude (Anthropic)*

