"""Forward kinematics and model checks.

Bedrock geometry is mirrored on X relative to Blockbench space. A bone rotation (rx, ry, rz)
is applied in Blockbench space as Euler 'ZYX' with angles (-rx, -ry, rz) - the same conversion the
three.js previewer uses. All checks run in that space; mirroring does not change any of them.
"""
import math


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return ((1, 0, 0), (0, c, -s), (0, s, c))


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0, s), (0, 1, 0), (-s, 0, c))


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0), (s, c, 0), (0, 0, 1))


def _mm(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def _mv(a, v):
    return (a[0][0] * v[0] + a[0][1] * v[1] + a[0][2] * v[2],
            a[1][0] * v[0] + a[1][1] * v[1] + a[1][2] * v[2],
            a[2][0] * v[0] + a[2][1] * v[1] + a[2][2] * v[2])


def rot_matrix(r):
    """Bedrock bone/cube rotation in degrees -> 3x3 matrix in Blockbench space."""
    rx, ry, rz = (math.radians(v) for v in r)
    return _mm(_rz(rz), _mm(_ry(-ry), _rx(-rx)))


IDENT = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def bb(p):
    return (-p[0], p[1], p[2])


def world_transforms(bones, pose=None):
    """Return {bone: (R, t)} so that world = R @ local + t, with local measured from the bone pivot."""
    pose = pose or {}
    out = {}
    by_name = {b["name"]: b for b in bones}

    def solve(name):
        if name in out:
            return out[name]
        b = by_name[name]
        r = list(b.get("rotation", [0, 0, 0]))
        pr = pose.get(name)
        pos = (0.0, 0.0, 0.0)
        if pr:
            r = [r[0] + pr[0], r[1] + pr[1], r[2] + pr[2]]
            if len(pr) >= 6:                       # an animated position offset, in model units (x mirrors in bb space)
                pos = (-pr[3], pr[4], pr[5])
        R = rot_matrix(r)
        p = bb(b["pivot"])
        if "parent" in b:
            PR, Pt = solve(b["parent"])
            pp = bb(by_name[b["parent"]]["pivot"])
            off = (p[0] - pp[0] + pos[0], p[1] - pp[1] + pos[1], p[2] - pp[2] + pos[2])
            t = tuple(a + o for a, o in zip(_mv(PR, off), Pt))
            out[name] = (_mm(PR, R), t)
        else:
            out[name] = (R, (p[0] + pos[0], p[1] + pos[1], p[2] + pos[2]))
        return out[name]

    for b in bones:
        solve(b["name"])
    return out


def cube_corners(cd, bone_pivot, R, t):
    """World-space corners of one cube."""
    w, h, d = cd["size"]
    inf = cd.get("inflate", 0)
    ox, oy, oz = cd["origin"]
    fx = -(ox + w)
    corners = []
    for cx in (fx - inf, fx + w + inf):
        for cy in (oy - inf, oy + h + inf):
            for cz in (oz - inf, oz + d + inf):
                corners.append((cx, cy, cz))
    p = bb(bone_pivot)
    out = []
    if "rotation" in cd:
        cp = bb(cd["pivot"])
        Rc = rot_matrix(cd["rotation"])
        for c in corners:
            rel = _mv(Rc, (c[0] - cp[0], c[1] - cp[1], c[2] - cp[2]))
            loc = (cp[0] - p[0] + rel[0], cp[1] - p[1] + rel[1], cp[2] - p[2] + rel[2])
            out.append(tuple(a + b for a, b in zip(_mv(R, loc), t)))
    else:
        for c in corners:
            loc = (c[0] - p[0], c[1] - p[1], c[2] - p[2])
            out.append(tuple(a + b for a, b in zip(_mv(R, loc), t)))
    return out


def world_boxes(model, pose=None):
    """List of (cube_index, bone, aabb_min, aabb_max) in world space."""
    T = world_transforms(model.bones, pose)
    boxes = []
    idx = 0
    for b in model.bones:
        R, t = T[b["name"]]
        for cd in b["cubes"]:
            cs = cube_corners(cd, b["pivot"], R, t)
            mn = tuple(min(c[i] for c in cs) for i in range(3))
            mx = tuple(max(c[i] for c in cs) for i in range(3))
            boxes.append((idx, b["name"], mn, mx))
            idx += 1
    return boxes


def extents(model, pose=None):
    boxes = world_boxes(model, pose)
    mn = tuple(min(b[2][i] for b in boxes) for i in range(3))
    mx = tuple(max(b[3][i] for b in boxes) for i in range(3))
    return mn, mx


def descendants(model, roots):
    out = set(roots)
    changed = True
    while changed:
        changed = False
        for b in model.bones:
            if b.get("parent") in out and b["name"] not in out:
                out.add(b["name"])
                changed = True
    return out


def ground(model, ignore=()):
    """Shift the model so its lowest point in rest pose (ignoring e.g. held weapons) sits exactly on y=0."""
    skip = descendants(model, ignore)
    boxes = [b for b in world_boxes(model) if b[1] not in skip]
    lo = min(b[2][1] for b in boxes)
    if abs(lo) > 1e-3:
        model.shift(dy=-lo)
    return -lo


def bone_extents(model, names):
    skip_keep = descendants(model, names)
    boxes = [b for b in world_boxes(model) if b[1] in skip_keep]
    if not boxes:
        return None
    return (tuple(min(b[2][i] for b in boxes) for i in range(3)), tuple(max(b[3][i] for b in boxes) for i in range(3)))


def _overlap(a_mn, a_mx, b_mn, b_mx, tol):
    return all(a_mn[i] <= b_mx[i] + tol and b_mn[i] <= a_mx[i] + tol for i in range(3))


def connectivity(model, tol=0.3, ignore_tags=()):
    """Groups of cubes that do not touch the main body (floating parts)."""
    boxes = world_boxes(model)
    cubes = [c for c in model.cubes]
    keep = [i for i, c in enumerate(cubes) if c.get("tag") not in ignore_tags]
    parent = {i: i for i in keep}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    # order of model.cubes matches world_boxes order only if cubes were appended bone-by-bone in bone order;
    # map by identity instead
    order = []
    for b in model.bones:
        for cd in b["cubes"]:
            order.append(cd)
    pos_of = {id(cd): k for k, cd in enumerate(order)}
    box_of = {i: boxes[pos_of[id(cubes[i]["cd"])]] for i in keep}
    for a in range(len(keep)):
        ia = keep[a]
        A = box_of[ia]
        for b in range(a + 1, len(keep)):
            ib = keep[b]
            B = box_of[ib]
            if _overlap(A[2], A[3], B[2], B[3], tol):
                ra, rb = find(ia), find(ib)
                if ra != rb:
                    parent[ra] = rb
    groups = {}
    for i in keep:
        groups.setdefault(find(i), []).append(i)
    gl = sorted(groups.values(), key=len, reverse=True)
    return [[(cubes[i]["bone"], cubes[i]["cd"]["origin"]) for i in g] for g in gl[1:]]


def joint_gaps(model, tol=1.0):
    """Child bones whose pivot is far from every cube of their parent (rotations would detach them)."""
    T = world_transforms(model.bones)
    boxes = world_boxes(model)
    by_bone = {}
    for _, bn, mn, mx in boxes:
        by_bone.setdefault(bn, []).append((mn, mx))
    issues = []
    for b in model.bones:
        par = b.get("parent")
        if not par or par not in by_bone or b["name"] not in by_bone:
            continue
        PR, Pt = T[par]
        pp = bb(model.index[par]["pivot"])
        p = bb(b["pivot"])
        w = tuple(a + o for a, o in zip(_mv(PR, (p[0] - pp[0], p[1] - pp[1], p[2] - pp[2])), Pt))
        best = min(math.sqrt(sum(max(0.0, mn[i] - w[i], w[i] - mx[i]) ** 2 for i in range(3)))
                   for mn, mx in by_bone[par])
        if best > tol:
            issues.append((b["name"], round(best, 2)))
    return issues


def zfight(model, inflate=0.015):
    """Coplanar, same-facing, overlapping faces of unrotated cubes in one bone.
    Fixes them by inflating the smaller cube slightly; returns the list of fixed pairs."""
    fixed = []
    for b in model.bones:
        cs = [cd for cd in b["cubes"] if "rotation" not in cd]
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                A, B = cs[i], cs[j]
                amn = A["origin"]; amx = [A["origin"][k] + A["size"][k] for k in range(3)]
                bmn = B["origin"]; bmx = [B["origin"][k] + B["size"][k] for k in range(3)]
                hit = False
                for ax in range(3):
                    others = [k for k in range(3) if k != ax]
                    ov = all(min(amx[k], bmx[k]) - max(amn[k], bmn[k]) > 1e-4 for k in others)
                    if not ov:
                        continue
                    if abs(amn[ax] - bmn[ax]) < 1e-4 or abs(amx[ax] - bmx[ax]) < 1e-4:
                        hit = True
                if hit:
                    va = A["size"][0] * A["size"][1] * A["size"][2]
                    vb = B["size"][0] * B["size"][1] * B["size"][2]
                    small = A if va <= vb else B
                    if not small.get("inflate"):
                        small["inflate"] = inflate
                        fixed.append((b["name"], small["origin"]))
    return fixed


def uv_overlaps(model):
    rects = []
    for c in model.cubes:
        w, h, d = c["cd"]["size"]
        u, v = c["cd"]["uv"]
        rects.append((u, v, u + 2 * (d + w), v + d + h))
    bad = 0
    for i in range(len(rects)):
        a = rects[i]
        for j in range(i + 1, len(rects)):
            b = rects[j]
            if a[0] < b[2] - 1e-6 and b[0] < a[2] - 1e-6 and a[1] < b[3] - 1e-6 and b[1] < a[3] - 1e-6:
                bad += 1
    return bad


def transparent_faces(model, img, allowed_tags=()):
    """Faces that came out fully transparent (usually a material/decal mistake)."""
    D = model.D
    out = []
    for c in model.cubes:
        if c.get("tag") in allowed_tags:
            continue
        w, h, d = c["cd"]["size"]
        u, v = c["cd"]["uv"]
        faces = (("east", u, v + d, d, h), ("north", u + d, v + d, w, h), ("west", u + d + w, v + d, d, h),
                 ("south", u + 2 * d + w, v + d, w, h), ("up", u + d, v, w, d), ("down", u + d + w, v, w, d))
        for face, fu, fv, fw, fh in faces:
            x0, y0, pw, ph = int(round(fu * D)), int(round(fv * D)), int(round(fw * D)), int(round(fh * D))
            total = pw * ph
            clear = sum(1 for yy in range(ph) for xx in range(pw) if img[y0 + yy][x0 + xx][3] == 0)
            if total and clear == total:
                out.append((c["bone"], face))
    return out
