async def serialize_doc(doc):
    doc["id"] = str(doc.pop("_id"))# Add _id as part of the response
    return doc

async def transform_document(doc):
    # Replace ObjectId with a string and rename "_id" to "id"
    doc['id'] = str(doc.pop('_id'))
    return doc

async def flatten_query_simple(nested_query, sep='.'):
    """
    Flattens a nested dictionary into a MongoDB-compatible query using dot notation
    with a straightforward single-loop approach.

    :param nested_query: The nested dictionary to flatten.
    :param sep: Separator for nested keys (default is '.').
    :return: A flattened dictionary with dot notation keys.
    """
    flat_query = {}
    for key, value in nested_query.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flat_query[f"{key}{sep}{sub_key}"] = sub_value
        else:
            flat_query[key] = value
    return flat_query