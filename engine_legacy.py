import sys
import json
import numpy as np
from scipy.spatial import ConvexHull

def get_local_basis(normal):
    normal = np.array(normal, dtype=float)
    normal = normal / np.linalg.norm(normal)
    z_local = np.array([0.0, 0.0, 1.0])
    if np.abs(normal[2]) > 0.9999:
        u = np.array([1.0, 0.0, 0.0])
        v = np.array([0.0, 1.0, 0.0])
    else:
        proj_z = z_local - normal * np.dot(z_local, normal)
        v = proj_z / np.linalg.norm(proj_z)
        u = np.cross(normal, v)
        u = u / np.linalg.norm(u)
    return u, v

def project_points_to_plane(points, normal, ref_point):
    u, v = get_local_basis(normal)
    projected = []
    for p in points:
        vec = p - ref_point
        x = np.dot(vec, u)
        y = np.dot(vec, v)
        projected.append([x, y])
    return np.array(projected)

def compute_outline_2d(pts_2d):
    """Mengembalikan outline (convex hull jika mungkin, titik unik jika tidak)"""
    if len(pts_2d) == 0:
        return []
    # Hapus duplikat
    pts_2d = np.unique(pts_2d, axis=0)
    if len(pts_2d) < 3:
        return pts_2d.tolist()
    try:
        # Convex hull hanya untuk titik non-colinear
        # Jika semua collinear, ConvexHull akan error, jadi kita fallback ke semua titik
        # Kita bisa deteksi collinearity dengan matriks kovarian
        if np.linalg.matrix_rank(pts_2d - pts_2d.mean(axis=0)) < 2:
            # Semua collinear, kembalikan titik ekstrem saja (min dan max)
            idx_min = np.argmin(pts_2d[:, 0])
            idx_max = np.argmax(pts_2d[:, 0])
            return [pts_2d[idx_min].tolist(), pts_2d[idx_max].tolist()]
        hull = ConvexHull(pts_2d)
        return pts_2d[hull.vertices].tolist()
    except Exception as e:
        print(f"ConvexHull error: {e}, using all points")
        return pts_2d.tolist()

def project_edges(vertices, edges, normal, ref_point):
    """Proyeksikan edge (indeks pasangan) ke koordinat 2D bidang"""
    pts_2d = project_points_to_plane(vertices, normal, ref_point)
    projected_edges = []
    for e in edges:
        p1 = pts_2d[e[0]].tolist()
        p2 = pts_2d[e[1]].tolist()
        projected_edges.append([p1, p2])
    return projected_edges

def main_transisi(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)

    vertices = np.array(data['vertices'])
    options = data['options']
    ref_point = np.array(data.get('ref_point', [0,0,0]))
    sides = options['sides']  # hash boolean
    mode = options.get('mode', 'outline')  # 'outline' atau 'detail'

    result_projections = {}
    for side, active in sides.items():
        if not active:
            continue
        normal = np.array(data['normals'][side])
        if mode == 'outline':
            pts_2d = project_points_to_plane(vertices, normal, ref_point)
            outline = compute_outline_2d(pts_2d)
            if outline:
                result_projections[side] = {'points_2d': outline, 'type': 'outline'}
            else:
                # Jika gagal, tambahkan dengan array kosong (tidak ditampilkan di Ruby)
                result_projections[side] = {'points_2d': [], 'type': 'outline'}
        elif mode == 'detail':
            edges = data.get('edges', [])
            if not edges:
                # Jika tidak ada edge dikirim, fallback ke outline
                pts_2d = project_points_to_plane(vertices, normal, ref_point)
                outline = compute_outline_2d(pts_2d)
                result_projections[side] = {'points_2d': outline, 'type': 'outline'}
            else:
                # Proyeksikan semua edge
                proj_edges = project_edges(vertices, edges, normal, ref_point)
                result_projections[side] = {'edges': proj_edges, 'type': 'detail'}

    with open(output_file, 'w') as f:
        json.dump({'projections': result_projections}, f, indent=2)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: engine.py transisi input.json output.json")
        sys.exit(1)
    command = sys.argv[1]
    if command == "transisi":
        main_transisi(sys.argv[2], sys.argv[3])