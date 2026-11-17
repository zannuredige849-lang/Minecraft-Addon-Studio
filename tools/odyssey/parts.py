"""Reusable anatomy parts: chained digits that curl without gaps, tapered limbs and strands."""
import math


def digit(m, bone, top, lengths, width, curl, mats, plane="x", s=1, nail=None, nail_size=None):
    """Chain of segments hanging down from `top`, curling progressively.

    plane='x': curls in the x-y plane toward +x when s=+1 (right hand: toward the palm side).
    plane='z': curls in the y-z plane toward -z (forward) when s=+1 (thumbs, toes pointing forward).
    width = (wx, wz) cross-section. `curl` = cumulative angle (degrees) per segment.
    Returns the tip position."""
    x, y, z = top
    a = 0.0
    wx, wz = width
    for i, L in enumerate(lengths):
        a += curl[i]
        r = math.radians(a)
        if plane == "x":
            dx, dy, dz = s * math.sin(r), -math.cos(r), 0.0
            rot = (0, 0, -s * a)
        else:
            dx, dy, dz = 0.0, -math.cos(r), -s * math.sin(r)
            rot = (-s * a, 0, 0)
        L = m.snap(L)
        origin = (x - wx / 2, y - L, z - wz / 2)
        m.cube(bone, origin, (wx, L, wz), mats[min(i, len(mats) - 1)], rot=rot if a else None, pivot=(x, y, z))
        x, y, z = x + dx * L, y + dy * L, z + dz * L
    if nail is not None:
        nw = nail_size or (wx * 0.9, 0.5, wz * 0.9)
        m.cube(bone, (x - nw[0] / 2, y - nw[1] + 0.12, z - nw[2] / 2), nw, nail, rot=rot if a else None, pivot=(x, y + 0.12, z))
    return (x, y, z)


def forward_digit(m, bone, root, lengths, width, droop, mats, nail=None):
    """Toe-like chain pointing forward (-z) from `root`, drooping down by `droop` degrees per segment."""
    x, y, z = root
    a = 0.0
    wx, wy = width
    for i, L in enumerate(lengths):
        a += droop[i]
        r = math.radians(a)
        dz, dy = -math.cos(r), -math.sin(r)
        L = m.snap(L)
        origin = (x - wx / 2, y - wy / 2, z - L)
        m.cube(bone, origin, (wx, wy, L), mats[min(i, len(mats) - 1)], rot=(a, 0, 0) if a else None, pivot=(x, y, z))
        x, y, z = x, y + dy * L, z + dz * L
    if nail is not None:
        m.cube(bone, (x - wx * 0.45, y - wy * 0.2, z - 0.25), (wx * 0.9, wy * 0.6, 0.5), nail, rot=(a, 0, 0) if a else None,
               pivot=(x, y, z))
    return (x, y, z)


def chain_y(m, bone, start, lengths, sizes, angles, mats, up=True, overlap=0.0):
    """Segments chained along y (up or down) bending in the y-z plane; angle<0 bends toward -z (forward).
    sizes = [(wx, wz), ...] per segment. overlap extends every segment but the last past its joint, closing the
    wedge gaps a bend opens on the outer edge (a curved blade then reads as one piece). Returns the end point."""
    x, y, z = start
    a = 0.0
    for i, L in enumerate(lengths):
        a += angles[i]
        r = math.radians(a)
        wx, wz = sizes[min(i, len(sizes) - 1)]
        L = m.snap(L)
        drawn = L + (m.snap(overlap) if i < len(lengths) - 1 else 0.0)
        if up:
            origin = (x - wx / 2, y, z - wz / 2)
            dy, dz = math.cos(r), -math.sin(r)
            rot = (-a, 0, 0)
        else:
            origin = (x - wx / 2, y - drawn, z - wz / 2)
            dy, dz = -math.cos(r), math.sin(r)
            rot = (a, 0, 0)
        m.cube(bone, origin, (wx, drawn, wz), mats[min(i, len(mats) - 1)], rot=rot if a else None, pivot=(x, y, z))
        y, z = y + dy * L, z + dz * L
    return (x, y, z)


def strands(m, bone, x0, x1, y_top, z, lengths, width, depth, mat, count, seed=1, rot=None):
    """A curtain of hanging hair strands of varying length."""
    for i in range(count):
        t = i / max(1, count - 1)
        x = x0 + (x1 - x0) * t
        L = lengths[0] + (lengths[1] - lengths[0]) * (((i * 7919 + seed * 104729) % 97) / 96.0)
        m.cube(bone, (x - width / 2, y_top - L, z - depth / 2), (width, L, depth), mat,
               rot=rot, pivot=(x, y_top, z) if rot else None)
