import os
import numpy as np
import trimesh
import trimesh.transformations as tf
from trimesh import creation, boolean
from trimesh.exchange.gltf import export_glb

# ----------------------------------------------------------------------
# Local AI models (transformers) – loaded once at startup
# ----------------------------------------------------------------------
_classifier_pipeline = None
_summarizer_model = None
_summarizer_tokenizer = None

def get_classifier():
    """Load zero-shot classification model (pipeline)."""
    global _classifier_pipeline
    if _classifier_pipeline is None:
        try:
            from transformers import pipeline
            print("Loading classifier model (distilbert-mnli)...")
            _classifier_pipeline = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli",
                device=-1
            )
            print("Classifier loaded.")
        except ImportError:
            print("transformers not installed. Classification will fallback to keyword matching.")
            _classifier_pipeline = False
    return _classifier_pipeline

def get_summarizer():
    """Load T5 model and tokenizer for summarization (direct, not pipeline)."""
    global _summarizer_model, _summarizer_tokenizer
    if _summarizer_model is None:
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            print("Loading summarization model (t5-small)...")
            _summarizer_tokenizer = AutoTokenizer.from_pretrained("t5-small")
            _summarizer_model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")
            print("Summarizer loaded.")
        except ImportError:
            print("transformers not installed. Summarization will fallback to default.")
            _summarizer_model = False
            _summarizer_tokenizer = False
    return _summarizer_model, _summarizer_tokenizer

def summarize_text(text, max_length=50):
    """Generate summary using T5 model."""
    model, tokenizer = get_summarizer()
    if model is None or tokenizer is None:
        return None
    try:
        # T5 expects a "summarize:" prefix
        input_text = f"summarize: {text}"
        inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
        summary_ids = model.generate(inputs, max_length=max_length, min_length=10, do_sample=False)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary
    except Exception as e:
        print(f"Summarization failed: {e}")
        return None

# Pre-load models when the module is imported (on Flask startup)
print("Pre-loading AI models...")
get_classifier()
get_summarizer()
print("AI models ready.")

def classify_object(description: str, api_key: str = None) -> str:
    """
    Determine object type using zero-shot classification.
    Falls back to keyword matching if model unavailable.
    """
    classifier = get_classifier()
    if classifier and classifier is not False:
        candidate_labels = ["hard hat", "wrench", "safety cone", "safety glasses", "generic"]
        label_map = {
            "hard hat": "hard_hat",
            "wrench": "wrench",
            "safety cone": "safety_cone",
            "safety glasses": "safety_glasses",
            "generic": "generic"
        }
        try:
            result = classifier(description, candidate_labels)
            top_label = result['labels'][0]
            return label_map.get(top_label, "generic")
        except Exception as e:
            print(f"Classification failed: {e}")

    # Fallback: simple keyword matching
    desc_lower = description.lower()
    if "hard hat" in desc_lower or "helmet" in desc_lower:
        return "hard_hat"
    if "wrench" in desc_lower:
        return "wrench"
    if "cone" in desc_lower:
        return "safety_cone"
    if "glass" in desc_lower or "goggle" in desc_lower:
        return "safety_glasses"
    return "generic"

def generate_summary(description: str, obj_type: str, api_key: str = None) -> str:
    """
    Generate educational summary using T5.
    Falls back to template if model unavailable.
    """
    # Build prompt
    prompt = f"This {obj_type.replace('_', ' ')} is used in industrial settings. {description}"
    summary = summarize_text(prompt)
    if summary:
        return summary

    # Fallback educational summary based on object type
    type_name = obj_type.replace('_', ' ')
    if obj_type == "hard_hat":
        return "A hard hat protects the head from falling objects and impact. It is essential on construction sites."
    elif obj_type == "wrench":
        return "A wrench is used to tighten or loosen nuts and bolts, commonly in mechanical and construction work."
    elif obj_type == "safety_cone":
        return "Safety cones mark hazardous areas and guide traffic. They are vital for worksite safety."
    elif obj_type == "safety_glasses":
        return "Safety glasses shield eyes from debris and chemicals. They are mandatory in many industrial environments."
    else:
        return f"This {type_name} is a generic tool used in industrial settings for various tasks."

# --------------------- Procedural 3D Models (unchanged) ---------------------
def create_hard_hat() -> trimesh.Trimesh:
    dome = creation.uv_sphere(radius=1.0, count=[32, 32])
    dome.apply_transform(tf.translation_matrix([0, 0, 0.5]))
    brim = creation.cylinder(radius=1.2, height=0.2, sections=32)
    brim.apply_transform(tf.translation_matrix([0, 0, 0.0]))
    hat = trimesh.util.concatenate([dome, brim])
    peak = creation.cylinder(radius=0.3, height=0.3, sections=16)
    peak.apply_transform(tf.translation_matrix([0, 0, 0.9]))
    hat = trimesh.util.concatenate([hat, peak])
    hat.visual.vertex_colors = [255, 200, 0, 255]
    return hat

def create_wrench() -> trimesh.Trimesh:
    handle = creation.box(extents=[2.5, 0.6, 0.4])
    handle.apply_transform(tf.translation_matrix([0, 0, 0]))
    ring = creation.cylinder(radius=0.7, height=0.4, sections=32)
    ring.apply_transform(tf.translation_matrix([1.3, 0, 0]))
    ring2 = creation.cylinder(radius=0.5, height=0.41, sections=32)
    ring2.apply_transform(tf.translation_matrix([1.3, 0, 0]))
    ring_open = boolean.difference([ring, ring2])
    if ring_open is None:
        ring_open = ring
    wrench = trimesh.util.concatenate([handle, ring_open])
    wrench.visual.vertex_colors = [100, 100, 100, 255]
    return wrench

def create_safety_cone() -> trimesh.Trimesh:
    cone = creation.cone(radius=0.8, height=1.5, sections=32)
    base = creation.cylinder(radius=0.9, height=0.1, sections=32)
    base.apply_transform(tf.translation_matrix([0, 0, -0.75]))
    cone.apply_transform(tf.translation_matrix([0, 0, -0.2]))
    full = trimesh.util.concatenate([cone, base])
    full.visual.vertex_colors = [255, 100, 0, 255]
    return full

def create_safety_glasses() -> trimesh.Trimesh:
    lens = creation.cylinder(radius=0.4, height=0.1, sections=24)
    lens_left = lens.copy()
    lens_left.apply_transform(tf.translation_matrix([-0.5, 0, 0]))
    lens_right = lens.copy()
    lens_right.apply_transform(tf.translation_matrix([0.5, 0, 0]))
    bridge = creation.box(extents=[0.6, 0.15, 0.1])
    bridge.apply_transform(tf.translation_matrix([0, 0, 0]))
    glasses = trimesh.util.concatenate([lens_left, lens_right, bridge])
    glasses.visual.vertex_colors = [0, 150, 255, 255]
    return glasses

def create_generic() -> trimesh.Trimesh:
    box = creation.box(extents=[1.0, 1.0, 1.0])
    box.visual.vertex_colors = [128, 128, 128, 255]
    return box

def generate_glb_from_type(obj_type: str) -> bytes:
    """Return GLB bytes of the generated model."""
    if obj_type == "hard_hat":
        mesh = create_hard_hat()
    elif obj_type == "wrench":
        mesh = create_wrench()
    elif obj_type == "safety_cone":
        mesh = create_safety_cone()
    elif obj_type == "safety_glasses":
        mesh = create_safety_glasses()
    else:
        mesh = create_generic()

    # Center and scale
    mesh.apply_translation(-mesh.centroid)
    scale_factor = 1.5 / max(mesh.extents)
    mesh.apply_scale(scale_factor)

    return export_glb(mesh)