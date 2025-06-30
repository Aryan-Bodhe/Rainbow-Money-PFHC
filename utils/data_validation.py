from typing import Any, List, Tuple
import json

def is_valid_json(json_str: str) -> bool:
    try:
        json.loads(json_str)
        return True
    except Exception:
        return False

def validate_report_response(data: Any) -> Tuple[bool, List[str]]:
    """
    Validate that `data` matches the expected report JSON schema:
    {
      "overall_profile_review": str,
      "commendable_areas": [ { "header": str, "content": str }, ... ] (≤3 items),
      "areas_for_improvement": [ { "header": str, "current_scenario": str, "actionable": str }, ... ] (≤7 items),
      "summary": str
    }
    """
    errors: List[str] = []
    
    # Top‐level must be a dict
    if not isinstance(data, dict):
        return False, ["Response is not a JSON object"]
    
    # Required keys
    required = {"overall_profile_review", "commendable_areas", "areas_for_improvement", "summary"}
    missing = required - data.keys()
    extra   = set(data.keys()) - required
    if missing:
        errors.append(f"Missing keys: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"Unexpected keys: {', '.join(sorted(extra))}")

    # overall_profile_review
    opr = data.get("overall_profile_review")
    if not isinstance(opr, str):
        errors.append("`overall_profile_review` must be a string")

    # commendable_areas
    ca = data.get("commendable_areas")
    if not isinstance(ca, list):
        errors.append("`commendable_areas` must be a list")
    else:
        if len(ca) > 3:
            errors.append(f"`commendable_areas` has {len(ca)} items; maximum is 3")
        for i, item in enumerate(ca, start=1):
            if not isinstance(item, dict):
                errors.append(f"`commendable_areas[{i}]` is not an object")
                continue
            if set(item.keys()) != {"header", "content"}:
                errors.append(f"`commendable_areas[{i}]` keys must be exactly ['header','content']")
            else:
                if not isinstance(item["header"], str):
                    errors.append(f"`commendable_areas[{i}].header` must be a string")
                if not isinstance(item["content"], str):
                    errors.append(f"`commendable_areas[{i}].content` must be a string")

    # areas_for_improvement
    afi = data.get("areas_for_improvement")
    if not isinstance(afi, list):
        errors.append("`areas_for_improvement` must be a list")
    else:
        if len(afi) > 7:
            errors.append(f"`areas_for_improvement` has {len(afi)} items; maximum is 7")
        for i, item in enumerate(afi, start=1):
            if not isinstance(item, dict):
                errors.append(f"`areas_for_improvement[{i}]` is not an object")
                continue
            expected = {"header", "current_scenario", "actionable"}
            if set(item.keys()) != expected:
                errors.append(f"`areas_for_improvement[{i}]` keys must be exactly {sorted(expected)}")
            else:
                for key in expected:
                    if not isinstance(item[key], str):
                        errors.append(f"`areas_for_improvement[{i}].{key}` must be a string")

    # summary
    summ = data.get("summary")
    if not isinstance(summ, str):
        errors.append("`summary` must be a string")

    return (len(errors) == 0), errors
