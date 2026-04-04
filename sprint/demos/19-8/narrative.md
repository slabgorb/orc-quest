# 19-8

## Problem

Problem: Players exploring a dungeon have no map — they must remember every room they've visited by hand, or get lost. Why it matters: Spatial disorientation breaks immersion and frustrates players; a persistent, auto-drawn map is a foundational quality-of-life feature that separates a polished game from a prototype.

---

## What Changed

We added an **Automapper panel** to the game UI — a live dungeon floorplan that draws itself as you explore. Picture graph paper with rooms as squares and doorways as connecting lines. Every room you've visited appears on the map. Every room you haven't is hidden in fog. Your current location glows with an accent highlight so you always know where you are.

The map knows the *type* of each connection: a locked door gets a door icon, a corridor gets a clean line, stairs get a staircase symbol. It fits neatly in the game's sidebar without taking over the screen.

---

## Why This Approach

The game engine already tracks every room connection in a data structure called a "room graph" — essentially a list of rooms and which rooms they connect to. Rather than build a separate map system, we read that existing data directly and render it visually. This means the map is always accurate with zero extra server work. SVG (scalable vector graphics) was chosen for rendering because it scales cleanly to any screen size and lets us apply the graph-paper aesthetic through simple CSS styling.

---
