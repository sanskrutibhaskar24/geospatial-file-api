# Geospatial File Measurement API

A FastAPI backend for uploading and processing geospatial files and calculating geometry measurements.

## Features

- Upload KML files
- Upload ZIP files containing Shapefiles
- Extract geometry, CRS, feature ID and properties
- Calculate Polygon area
- Calculate LineString length
- Handle Point geometry without measurement
- Transform geographic CRS to projected CRS before measurement
- REST API using FastAPI

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt