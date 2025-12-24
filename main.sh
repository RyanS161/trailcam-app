

PHOTOS_DIR="/Volumes/WILD_CAM/DCIM/100STLTH"
OUTPUT_JSON="${PHOTOS_DIR}out.json"
OUTPUT_HTML="${PHOTOS_DIR}out.html"
VISUALIZATION_DIR="${PHOTOS_DIR}/viz"

uv run python -m speciesnet.scripts.run_model --folders ${PHOTOS_DIR} --predictions_json ${OUTPUT_JSON}

uv run python -m megadetector.visualization.visualize_detector_output ${OUTPUT_JSON} ${VISUALIZATION_DIR} --detections_only --html_output_file ${OUTPUT_HTML}