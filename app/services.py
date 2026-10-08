from pathlib import Path
import geopandas as gpd
import zipfile
import tempfile
import shutil
import math


def clean_value(value):
    """Convert NaN values to None so they are valid JSON."""
    if isinstance(value, float) and math.isnan(value):
        return None

    return value


def process_geospatial_file(file_path: Path):
    """
    Read a KML file or ZIP containing a Shapefile
    and return feature information and measurements.
    """

    suffix = file_path.suffix.lower()

    # KML file
    if suffix == ".kml":
        gdf = gpd.read_file(file_path, driver="KML")

    # ZIP containing Shapefile
    elif suffix == ".zip":
        temp_dir = Path(tempfile.mkdtemp())

        try:
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            shapefiles = list(temp_dir.rglob("*.shp"))

            if not shapefiles:
                raise ValueError(
                    "The ZIP file does not contain a Shapefile."
                )

            gdf = gpd.read_file(shapefiles[0])

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        raise ValueError("Unsupported file format.")

    return extract_features(gdf)


def extract_features(gdf):
    """
    Extract feature information and calculate measurements.
    """

    features = []

    source_crs = gdf.crs

    # Convert to projected CRS for accurate measurements
    if source_crs is not None:
        try:
            measurement_gdf = gdf.to_crs(
                gdf.estimate_utm_crs()
            )
        except Exception:
            measurement_gdf = None
    else:
        measurement_gdf = None

    for index, row in gdf.iterrows():

        geometry = row.geometry

        properties = {}

        for key, value in row.items():
            if key != "geometry":
                properties[key] = clean_value(value)

        feature = {
            "feature_id": index,
            "geometry_type": (
                geometry.geom_type
                if geometry is not None
                else None
            ),
            "geometry": (
                geometry.__geo_interface__
                if geometry is not None
                else None
            ),
            "crs": (
                source_crs.to_string()
                if source_crs is not None
                else None
            ),
            "properties": properties,
            "measurement": None
        }

        # Calculate measurements using projected CRS
        if measurement_gdf is not None and geometry is not None:

            projected_geometry = measurement_gdf.loc[
                index, "geometry"
            ]

            if geometry.geom_type in ["Polygon", "MultiPolygon"]:
                feature["measurement"] = {
                    "type": "area",
                    "value": projected_geometry.area,
                    "unit": "square meters"
                }

            elif geometry.geom_type in [
                "LineString",
                "MultiLineString"
            ]:
                feature["measurement"] = {
                    "type": "length",
                    "value": projected_geometry.length,
                    "unit": "meters"
                }

            elif geometry.geom_type == "Point":
                feature["measurement"] = None

            else:
                # Unsupported geometry
                feature["measurement"] = None

        features.append(feature)

    return {
        "feature_count": len(features),
        "crs": (
            source_crs.to_string()
            if source_crs is not None
            else None
        ),
        "features": features
    }