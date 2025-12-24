import json
import multiprocessing as mp
from pathlib import Path
from typing import Literal, Optional, Union

from speciesnet import SpeciesNet

StrPath = Union[str, Path]

_MODEL = "kaggle:google/speciesnet/pyTorch/v4.0.1a"
_GEOFENCE = False
_RUN_MODE = "multi_thread"
_BATCH_SIZE = 8
_PROGRESS_BARS = True



def run_model(instances_dict, predictions_json) -> None:

    _PREDICTIONS_JSON = predictions_json

    components = "all"

    # Set running mode.
    run_mode: Literal["multi_thread", "multi_process"] = _RUN_MODE  # type: ignore

    # Make predictions.
    model = SpeciesNet(
        _MODEL,
        components=components,
        geofence=_GEOFENCE,
        multiprocessing=(run_mode == "multi_process"),
    )

    predictions_dict = model.predict(
        instances_dict=instances_dict,
        run_mode=run_mode,
        batch_size=_BATCH_SIZE,
        progress_bars=_PROGRESS_BARS,
        predictions_json=_PREDICTIONS_JSON,
    )
    if predictions_dict is not None:
        print(
            "Predictions:\n"
            + json.dumps(predictions_dict, ensure_ascii=False, indent=4)
        )
