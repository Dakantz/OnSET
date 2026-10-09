import io
import urllib
from urllib.parse import urlencode
import urllib.parse

from fastapi import (
    APIRouter,
    Body,
    Query,
)
import urllib3.util

from api.config import DEFAULT_MANMAN
from assistant.model import QueryGraph, Operations
from api.validator import validate_image_file
from backend.src.explorative.data_tensor import DataTensor, DataTensorResp
from explorative.exp_model import FuzzyQuery, FuzzyQueryResults
from api.router.classes.search_llm import search_llm_router
from fastapi import UploadFile, File
from PIL import Image
from base64 import b64decode
import urllib3
import re

manman = DEFAULT_MANMAN

search_router = APIRouter(prefix="/search")
search_router.include_router(search_llm_router)


@search_router.post("")
def search_classes(
    q: FuzzyQuery = Body(FuzzyQuery()),
) -> FuzzyQueryResults:
    return manman.guidance_man.search_fuzzy(q)


@search_router.post("/assistant")
def get_assistant_results(
    q: str = Query("working field of person"),
    graph: QueryGraph = Body(...),
) -> Operations:
    key = f"{q}_{graph.model_dump_json()}"
    cache = manman.assistant_cache[key]
    if cache:
        return cache
    else:
        operations = manman.iterative_assistant.run_query(q, graph)
        manman.assistant_cache[key] = operations
        return operations


@search_router.post("/encode/text")
def encode_text(
    text: str = Body(...),
) -> DataTensorResp:
    return manman.guidance_man.encode(text=text).to_resp()


@search_router.post("/encode/image")
def encode_image(image: str = Body(...)) -> DataTensorResp:
    # validate_image_file(image)
    # url encoded base 64 data
    image_data = re.match(r"^data:image/([^;]+);base64,(.*)$", image)
    if not image_data:
        raise ValueError("Invalid image data")
    print("Decoding image data of:", format(image_data.group(1)))
    image_content = b64decode(image_data.group(2))
    image_pil = Image.open(io.BytesIO(image_content))
    image_pil = image_pil.convert("RGB")
    image_pil.save("test_image.png")
    with open("test_image_raw.png", "wb") as f:
        f.write(image_content)
    return manman.guidance_man.encode(image=image_pil).to_resp()
