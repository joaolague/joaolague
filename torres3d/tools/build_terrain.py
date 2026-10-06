"""Build data/terrain.json for the Torres 3D viewer.

The grid is defined in the viewer's coast-aligned frame (x seaward, y alongshore) and must
match js/geo.js (ORIGIN, COAST_BEARING, DOMAIN).

Sources:
  openmeteo  Copernicus DEM GLO-90 via the Open-Meteo Elevation API (default, no key needed)
  geotiff    Any local DEM in a geographic or projected CRS (Copernicus GLO-30, LiDAR, drone
             survey...). Requires rasterio and pyproj.

Examples:
  python tools/build_terrain.py
  python tools/build_terrain.py --dx 50
  python tools/build_terrain.py --geotiff dem_torres.tif --dx 10
"""

import argparse
import json
import math
import time
import urllib.request
from pathlib import Path

import numpy as np

# Keep in sync with js/geo.js
ORIGIN_LAT, ORIGIN_LON = -29.347, -49.727
COAST_BEARING = 32.0
DOMAIN = dict(x0=-1500.0, x1=3500.0, y0=-3200.0, y1=4000.0)

M_PER_DEG_LAT = 110850.0
M_PER_DEG_LON = 111320.0 * math.cos(math.radians(ORIGIN_LAT))
SEAWARD = math.radians(COAST_BEARING + 90.0)
ALONG = math.radians(COAST_BEARING)
NHAT = np.array([math.sin(SEAWARD), math.cos(SEAWARD)])
THAT = np.array([math.sin(ALONG), math.cos(ALONG)])

OUT = Path(__file__).resolve().parents[1] / "data" / "terrain.json"


def coast_to_lonlat(x, y):
    e = x * NHAT[0] + y * THAT[0]
    n = x * NHAT[1] + y * THAT[1]
    return ORIGIN_LON + e / M_PER_DEG_LON, ORIGIN_LAT + n / M_PER_DEG_LAT


def grid_points(dx):
    xs = np.arange(DOMAIN["x0"], DOMAIN["x1"] + 0.5 * dx, dx)
    ys = np.arange(DOMAIN["y0"], DOMAIN["y1"] + 0.5 * dx, dx)
    X, Y = np.meshgrid(xs, ys)  # rows = y, columns = x (row-major, x fastest)
    lon, lat = coast_to_lonlat(X, Y)
    return xs, ys, lon, lat


def sample_openmeteo(lon, lat, chunk=100, pause=0.15):
    flat_lat, flat_lon = lat.ravel(), lon.ravel()
    out = np.empty(flat_lat.size)
    n_chunks = math.ceil(flat_lat.size / chunk)
    for c in range(n_chunks):
        sl = slice(c * chunk, (c + 1) * chunk)
        url = (
            "https://api.open-meteo.com/v1/elevation?latitude="
            + ",".join(f"{v:.5f}" for v in flat_lat[sl])
            + "&longitude="
            + ",".join(f"{v:.5f}" for v in flat_lon[sl])
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    vals = json.load(r)["elevation"]
                break
            except Exception as exc:  # network hiccup or rate limit
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
                print(f"  retry {attempt + 1}: {exc}")
        out[sl] = [v if v is not None and np.isfinite(v) else 0.0 for v in vals]
        print(f"\r  {c + 1}/{n_chunks} requests", end="", flush=True)
        time.sleep(pause)
    print()
    return out.reshape(lat.shape)


def sample_geotiff(path, lon, lat):
    import rasterio
    from pyproj import Transformer

    with rasterio.open(path) as src:
        tr = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        px, py = tr.transform(lon.ravel(), lat.ravel())
        vals = np.array([v[0] for v in src.sample(zip(px, py))], dtype=float)
        if src.nodata is not None:
            vals[vals == src.nodata] = 0.0
    vals[~np.isfinite(vals)] = 0.0
    return vals.reshape(lat.shape)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dx", type=float, default=75.0, help="grid spacing in metres (default 75)")
    ap.add_argument("--geotiff", type=Path, help="local DEM instead of the Open-Meteo API")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    xs, ys, lon, lat = grid_points(args.dx)
    print(f"Grid {xs.size} x {ys.size} = {lon.size} points, dx = {args.dx} m")
    if args.geotiff:
        elev = sample_geotiff(args.geotiff, lon, lat)
        source = f"DEM local ({args.geotiff.name})"
    else:
        elev = sample_openmeteo(lon, lat)
        source = "Copernicus DEM GLO-90 (via Open-Meteo)"

    print(f"Elevation range: {elev.min():.1f} to {elev.max():.1f} m; sea cells (<=0.5 m): {(elev <= 0.5).mean():.0%}")
    payload = {
        "source": source,
        "grid": {"x0": DOMAIN["x0"], "y0": DOMAIN["y0"], "dx": args.dx, "dy": args.dx, "nx": int(xs.size), "ny": int(ys.size)},
        "frame": {"origin": [ORIGIN_LAT, ORIGIN_LON], "coast_bearing": COAST_BEARING},
        "elevation": [round(float(v), 1) for v in elev.ravel()],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"Wrote {args.out} ({args.out.stat().st_size / 1024:.0f} kB)")


if __name__ == "__main__":
    main()
