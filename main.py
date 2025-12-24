import os
from pathlib import Path
import shutil
from PIL import Image
from PIL.ExifTags import TAGS
import time
from run_model import run_model
from megadetector.visualization.visualize_detector_output import visualize_detector_output
import json
from tqdm import tqdm
import argparse


def find_all_image_files(root_folder):
    image_extensions = {'.jpg', '.jpeg', '.png'}
    image_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext in image_extensions and not filename.startswith('.'):
                image_files.append(str(Path(dirpath) / filename))
    return image_files


def get_timestamp_filename(img_path):
    # gets time from the image metadata and returns a filename based on that timestamp
    img = Image.open(img_path)
    exif_data = img._getexif()
    if exif_data:
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'DateTimeOriginal':
                timestamp = value.replace(':', '').replace(' ', '_')
                ext = Path(img_path).suffix.lower()
                return f"{timestamp}{ext}"
    # Fallback to file modification time if no EXIF data
    print("No EXIF timestamp found, using file modification time on ", img_path)
    mod_time = Path(img_path).stat().st_mtime
    timestamp = time.strftime('%Y%m%d_%H%M%S', time.localtime(mod_time))
    ext = Path(img_path).suffix.lower()
    return f"{timestamp}{ext}"

def move_and_rename_images(image_files, destination_folder):
    for idx, image_path in enumerate(tqdm(image_files, desc="Moving and renaming files", unit="file")):
        ext = Path(image_path).suffix
        new_filename = get_timestamp_filename(image_path)
        new_path = Path(destination_folder) / new_filename

        if not new_path.exists():
            shutil.copy(image_path, new_path)
        else:
            # If a file with the same timestamp exists, append an index
            stem = Path(new_filename).stem
            new_filename = f"{stem}_{idx}{ext}"
            new_path = Path(destination_folder) / new_filename
            # copy the file with the new name
            shutil.copy(image_path, new_path)


def prepare_instances_dict(  # pylint: disable=too-many-positional-arguments
    folder = None,
    country = None,
    admin1_region = None,
) -> dict:


    def _enforce_location(
        instances_dict: dict, country, admin1_region
    ) -> dict:
        if not country:
            return instances_dict
        location_dict = {"country": country}
        if admin1_region:
            location_dict["admin1_region"] = admin1_region
        return {
            "instances": [
                instance_dict | location_dict
                for instance_dict in instances_dict["instances"]
            ]
        }

    filepaths = find_all_image_files(folder)

    assert filepaths is not None
    return _enforce_location(
        {
            "instances": [
                {
                    "filepath": (
                        filepath if isinstance(filepath, str) else filepath.as_posix()
                    )
                }
                for filepath in filepaths
            ]
        },
        country,
        admin1_region,
    )


def make_dir(dir_name):
    if not Path(dir_name).exists():
        Path(dir_name).mkdir(parents=True, exist_ok=True)


def main(input_folder, run_name):
    OUTPUT_ROOT = str("/working_volume")
    OUTPUT_FOLDER = str(Path(OUTPUT_ROOT) / f"run_{run_name}")
    UNPROCESSED_FOLDER = str(Path(OUTPUT_FOLDER) / "unprocessed_images")
    OUTPUT_JSON = str(Path(OUTPUT_FOLDER) / "out.json")
    VIZ_DIR = str(Path(OUTPUT_FOLDER) / "detections_bboxes")
    DETECTIONS_DIR = str(Path(OUTPUT_FOLDER) / "detections")
    CONFIDENCE_THRESHOLD = 0.15


    if not Path(input_folder).exists():
        print(f"Input folder {input_folder} does not exist. Please check the path.")
        return
    

    make_dir(OUTPUT_FOLDER)

    print("Scanning for image files...")
    all_image_files = find_all_image_files(input_folder)

    total_unprocessed = len(all_image_files)

    print(f"Found {total_unprocessed} image files. Moving and renaming...")
    make_dir(UNPROCESSED_FOLDER)
    move_and_rename_images(all_image_files, UNPROCESSED_FOLDER)


    print("Processing images with SpeciesNet...")

    instances_dict = prepare_instances_dict(
        folder=UNPROCESSED_FOLDER,
        country=None, # 'USA'
        admin1_region=None, # 'MT'
    )

    run_model(instances_dict=instances_dict, predictions_json=OUTPUT_JSON)

    print(f"Processing complete. Predictions saved to {OUTPUT_JSON}")

    print("Visualizing results...")

    # move detections to detections folder
    print("Cleaning up non-detections...")
    make_dir(DETECTIONS_DIR)
    total_detections = 0
    with open(OUTPUT_JSON, 'r') as f:
        predictions = json.load(f)
        for instance in predictions.get("predictions", []):
            filepath = instance.get("filepath")
            detections = instance.get("detections", [])
            if len(detections) > 0 and filepath and Path(filepath).exists():
                # max confidence detection
                max_conf_detection = max(detections, key=lambda d: d.get("conf", 0))
                print(f"Max confidence for {filepath}: {max_conf_detection.get('conf', 0)}")
                if max_conf_detection.get("conf", 0) >= CONFIDENCE_THRESHOLD:   
                    shutil.copy(filepath, DETECTIONS_DIR)
                    total_detections += 1

    print(f"Total detections above confidence threshold {CONFIDENCE_THRESHOLD}: {total_detections} out of {total_unprocessed} images.")

    make_dir(VIZ_DIR)
    visualize_detector_output(OUTPUT_JSON,
                            VIZ_DIR,
                            render_detections_only=True,
                            # html_output_file=OUTPUT_HTML,
                            confidence_threshold=CONFIDENCE_THRESHOLD)

    #Cleanup: remove unprocessed dir and json file
    print("Cleaning up temporary files...")
    shutil.rmtree(UNPROCESSED_FOLDER)
    # os.remove(OUTPUT_JSON)

    print(f"Removed {total_unprocessed - total_detections} non-detections")

    print("All done! See output folder for results:", OUTPUT_FOLDER)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process wildlife images with SpeciesNet.")
    parser.add_argument("input_folder", help="Path to the input folder containing images")
    parser.add_argument("--run_name", default=time.strftime('%Y%m%d_%H%M%S'), help="Run name (default: current timestamp)")
    args = parser.parse_args()

    input_folder = args.input_folder
    run_name = args.run_name

    main(input_folder, run_name)