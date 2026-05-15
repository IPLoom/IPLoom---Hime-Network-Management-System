from fastapi import APIRouter
from app.services.classification import TYPE_TO_ICON, ICON_METADATA, get_custom_assets

router = APIRouter(tags=["System"])

@router.get("/constants")
async def get_constants():
    """
    Returns unified constants for the UI to ensure consistency across platforms.
    """
    # Fetch custom assets to include in the available list
    custom_assets = get_custom_assets()
    
    brand_registry_map = {}
    
    # Add custom and seeded brand icons from DB
    for name, asset in custom_assets.items():
        if asset["type"] == 'brand':
            brand_registry_map[name] = {
                "id": name,
                "name": name.capitalize(),
                "path": asset["path"]
            }

    brand_icons = list(brand_registry_map.values())
    
    # Format Lucide icons with metadata
    lucide_icons = []
    for icon_name, meta in ICON_METADATA.items():
        lucide_icons.append({
            "name": icon_name,
            "label": meta["label"],
            "category": meta["category"]
        })
    
    # Sort by category then label
    lucide_icons.sort(key=lambda x: (x["category"], x["label"]))

    # Custom Device Icons
    custom_device_icons = []
    for name, asset in custom_assets.items():
        if asset["type"] == 'device':
            custom_device_icons.append({
                "name": asset["path"],
                "label": name.capitalize(),
                "category": "Custom Assets",
                "is_custom": True
            })

    return {
        "device_types": sorted(list(TYPE_TO_ICON.keys())),
        "type_to_icon_map": TYPE_TO_ICON,
        "brand_registry": brand_icons,
        "available_icons": lucide_icons + custom_device_icons,
        "icon_metadata": ICON_METADATA
    }
